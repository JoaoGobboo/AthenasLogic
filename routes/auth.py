from flask import Blueprint, jsonify, request

from config.BlockChain import get_web3
from dtos.auth_dto import CheckAuthDTO, RequestNonceDTO
from services.auth_service import (
    generate_nonce_response,
    logout_response,
    verify_signature_response,
)


auth_bp = Blueprint("auth", __name__)
_nonce_state: dict[str, str] = {}


def _extract_payload() -> dict:
    return request.get_json(silent=True) or {}


@auth_bp.route("/auth/request_nonce", methods=["POST"])
def request_nonce() -> tuple:
    global _nonce_state
    payload = _extract_payload()

    try:
        dto = RequestNonceDTO(**payload)
    except Exception as exc:  # pragma: no cover - validation errors are unit tested in dtos
        return jsonify({"error": str(exc)}), 400

    service_response = generate_nonce_response(dto.address, _nonce_state)
    _nonce_state = service_response.state
    return jsonify(service_response.payload), service_response.status


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_signature() -> tuple:
    global _nonce_state
    payload = _extract_payload()

    try:
        dto = CheckAuthDTO(**payload)
    except Exception as exc:  # pragma: no cover - validation errors are unit tested in dtos
        return jsonify({"error": str(exc)}), 400

    service_response = verify_signature_response(
        address=dto.address,
        signature=dto.signature,
        state=_nonce_state,
        web3=get_web3(),
    )
    _nonce_state = service_response.state
    return jsonify(service_response.payload), service_response.status


@auth_bp.route("/auth/logout", methods=["POST"])
def logout() -> tuple:
    global _nonce_state
    payload = _extract_payload()
    service_response = logout_response(payload.get("address"), _nonce_state)
    _nonce_state = service_response.state
    return jsonify(service_response.payload), service_response.status
