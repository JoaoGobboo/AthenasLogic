from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from config.BlockChain import get_web3
from dtos.auth_dto import CheckAuthDTO, RequestNonceDTO
from services.auth_service import (
    NonceStore,
    ServiceResponse,
    generate_nonce_response,
    logout_response,
    verify_signature_response,
)
from services.session_service import SessionStore
from services.user_service import get_or_create_user, get_user_by_id, serialize_user


auth_bp = Blueprint("auth", __name__)
_NONCE_STORE_KEY = "nonce_store"
_SESSION_STORE_KEY = "session_store"


def _extract_payload() -> dict:
    return request.get_json(silent=True) or {}


def _get_nonce_store() -> NonceStore:
    store = current_app.extensions.get(_NONCE_STORE_KEY)
    if store is None:
        store = NonceStore()
        current_app.extensions[_NONCE_STORE_KEY] = store
    return store


def _get_session_store() -> SessionStore:
    store = current_app.extensions.get(_SESSION_STORE_KEY)
    if store is None:
        store = SessionStore()
        current_app.extensions[_SESSION_STORE_KEY] = store
    return store


def _apply_service_response(store: NonceStore, service_response: ServiceResponse) -> tuple:
    store.replace(service_response.state)
    return jsonify(service_response.payload), service_response.status


def _extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization")
    if not header:
        return None
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    return token or None


def _resolve_authenticated_user():
    token = _extract_bearer_token()
    if not token:
        return None, None
    store = _get_session_store()
    user_id = store.resolve(token)
    if not user_id:
        return None, token
    user = get_user_by_id(user_id)
    if user is None:
        store.destroy(token)
    return user, token


@auth_bp.route("/auth/request_nonce", methods=["POST"])
def request_nonce() -> tuple:
    """Solicita um nonce temporario para autenticacao.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        required: true
        schema:
          type: object
          required:
            - address
          properties:
            address:
              type: string
              description: Endereco Ethereum em formato checksum
              example: 0x0000000000000000000000000000000000000000
    responses:
      200:
        description: Nonce gerado com sucesso
        schema:
          type: object
          properties:
            nonce:
              type: string
      400:
        description: Dados invalidos
        schema:
          type: object
          properties:
            error:
              type: string
    """
    payload = _extract_payload()

    try:
        dto = RequestNonceDTO(**payload)
    except Exception as exc:  # pragma: no cover - validation errors are unit tested in dtos
        return jsonify({"error": str(exc)}), 400

    store = _get_nonce_store()
    state = store.snapshot()
    service_response = generate_nonce_response(dto.address, state)
    return _apply_service_response(store, service_response)


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_signature() -> tuple:
    """Valida a assinatura do nonce para autenticar o usuario.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        required: true
        schema:
          type: object
          required:
            - address
            - signature
          properties:
            address:
              type: string
              description: Endereco Ethereum em formato checksum
              example: 0x0000000000000000000000000000000000000000
            signature:
              type: string
              description: Assinatura gerada pela carteira
    responses:
      200:
        description: Assinatura validada com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
            address:
              type: string
      400:
        description: Assinatura invalida ou nonce inexistente
        schema:
          type: object
          properties:
            success:
              type: boolean
            error:
              type: string
      503:
        description: Provedor blockchain indisponivel
        schema:
          type: object
          properties:
            error:
              type: string
    """
    payload = _extract_payload()

    try:
        dto = CheckAuthDTO(**payload)
    except Exception as exc:  # pragma: no cover - validation errors are unit tested in dtos
        return jsonify({"error": str(exc)}), 400

    try:
        web3 = get_web3()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    store = _get_nonce_store()
    state = store.snapshot()
    service_response = verify_signature_response(
        address=dto.address,
        signature=dto.signature,
        state=state,
        web3=web3,
    )
    return _apply_service_response(store, service_response)


@auth_bp.route("/auth/logout", methods=["POST"])
def legacy_logout() -> tuple:
    """Remove o nonce associado ao endereco informado.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        required: true
        schema:
          type: object
          properties:
            address:
              type: string
              description: Endereco Ethereum associado ao nonce
    responses:
      200:
        description: Logout realizado
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: Endereco ausente ou invalido
        schema:
          type: object
          properties:
            success:
              type: boolean
            error:
              type: string
    """
    payload = _extract_payload()
    store = _get_nonce_store()
    state = store.snapshot()
    service_response = logout_response(payload.get("address"), state)
    return _apply_service_response(store, service_response)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login() -> tuple:
    """Autentica o usuario via assinatura de carteira e inicia sessao.
    ---
    tags:
      - Auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        required: true
        schema:
          type: object
          required:
            - address
            - signature
          properties:
            address:
              type: string
            signature:
              type: string
    responses:
      200:
        description: Sessao criada com sucesso
      400:
        description: Erro de validacao ou assinatura invalida
      401:
        description: Assinatura invalida
      503:
        description: Provedor blockchain indisponivel
    """
    payload = _extract_payload()
    try:
        dto = CheckAuthDTO(**payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        web3 = get_web3()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    nonce_store = _get_nonce_store()
    state = nonce_store.snapshot()
    verification_response = verify_signature_response(
        address=dto.address,
        signature=dto.signature,
        state=state,
        web3=web3,
    )
    nonce_store.replace(verification_response.state)

    if not verification_response.payload.get("success"):
        return jsonify(verification_response.payload), verification_response.status

    normalized_address = verification_response.payload.get("address")
    user = get_or_create_user(normalized_address)
    session = _get_session_store().create(user.id)

    body = {
        "token": session.token,
        "user": serialize_user(user),
    }
    return jsonify(body), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
def current_user() -> tuple:
    """Retorna os dados do usuario autenticado.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Dados do usuario
      401:
        description: Token ausente ou invalido
    """
    user, _ = _resolve_authenticated_user()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(serialize_user(user)), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout_session() -> tuple:
    """Encerra a sessao autenticada via token Bearer.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Sessao encerrada
      401:
        description: Token ausente
    """
    token = _extract_bearer_token()
    if token is None:
        return jsonify({"error": "Missing bearer token"}), 401

    store = _get_session_store()
    store.destroy(token)
    return jsonify({"success": True, "message": "Sessao encerrada"}), 200
