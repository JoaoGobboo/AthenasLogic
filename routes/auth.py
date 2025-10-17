from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from config.BlockChain import get_web3
from extensions import limiter
from dtos.auth_dto import CheckAuthDTO, RequestNonceDTO
from routes.security import extract_bearer_token, get_session_store, require_auth
from services.auth_service import ServiceResponse, generate_nonce_response, logout_response, verify_signature_response
from services.session_service import ResolvedSession
from services.user_service import get_or_create_user, serialize_user


auth_bp = Blueprint("auth", __name__)


def _extract_payload() -> dict:
    return request.get_json(silent=True) or {}


def _apply_service_response(service_response: ServiceResponse) -> tuple:
    return jsonify(service_response.payload), service_response.status

def _resolve_authenticated_user() -> tuple[ResolvedSession | None, str | None]:
    token = extract_bearer_token()
    if not token:
        return None, None
    store = get_session_store()
    session = store.resolve(token)
    if not session:
        return None, token
    return session, token


@auth_bp.route("/auth/request_nonce", methods=["POST"])
@limiter.limit("10 per minute")
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

    store = get_session_store()
    service_response = generate_nonce_response(dto.address, store)
    return _apply_service_response(service_response)


@auth_bp.route("/auth/verify", methods=["POST"])
@limiter.limit("10 per minute")
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

    store = get_session_store()
    service_response = verify_signature_response(
        address=dto.address,
        signature=dto.signature,
        store=store,
        web3=web3,
    )
    return _apply_service_response(service_response)


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
    store = get_session_store()
    service_response = logout_response(payload.get("address"), store)
    return _apply_service_response(service_response)


@auth_bp.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
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

    nonce_store = get_session_store()
    verification_response = verify_signature_response(
        address=dto.address,
        signature=dto.signature,
        store=nonce_store,
        web3=web3,
    )

    if not verification_response.payload.get("success"):
        return jsonify(verification_response.payload), verification_response.status

    normalized_address = verification_response.payload.get("address")
    user = get_or_create_user(normalized_address)
    session = get_session_store().create(user.id)

    body = {
        "token": session.token,
        "csrf_token": session.csrf_token,
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
    resolved, _ = _resolve_authenticated_user()
    if resolved is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(serialize_user(resolved.user)), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@require_auth()
def logout_session() -> tuple:
    """Encerra a sessao autenticada via token Bearer (requer X-CSRF-Token).
    ---
    tags:
      - Auth
    responses:
      200:
        description: Sessao encerrada
      401:
        description: Token ausente
    """
    store = get_session_store()
    store.destroy(g.current_session.token)
    return jsonify({"success": True, "message": "Sessao encerrada"}), 200
