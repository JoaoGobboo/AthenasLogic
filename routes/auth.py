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


auth_bp = Blueprint("auth", __name__)
_NONCE_STORE_KEY = "nonce_store"


def _extract_payload() -> dict:
    return request.get_json(silent=True) or {}


def _get_nonce_store() -> NonceStore:
    store = current_app.extensions.get(_NONCE_STORE_KEY)
    if store is None:
        store = NonceStore()
        current_app.extensions[_NONCE_STORE_KEY] = store
    return store


def _apply_service_response(store: NonceStore, service_response: ServiceResponse) -> tuple:
    store.replace(service_response.state)
    return jsonify(service_response.payload), service_response.status


@auth_bp.route("/auth/request_nonce", methods=["POST"])
def request_nonce() -> tuple:
    """Solicita um nonce temporário para autenticação.
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
              description: Endereço Ethereum em formato checksum
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
        description: Dados inválidos
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
    """Valida a assinatura do nonce para autenticar o usuário.
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
              description: Endereço Ethereum em formato checksum
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
        description: Assinatura inválida ou nonce inexistente
        schema:
          type: object
          properties:
            success:
              type: boolean
            error:
              type: string
      503:
        description: Provedor blockchain indisponível
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
def logout() -> tuple:
    """Remove o nonce associado ao endereço informado.
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
              description: Endereço Ethereum associado ao nonce
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
        description: Endereço ausente ou inválido
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
