from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from dtos.user_dto import UpdateUserProfileDTO
from services.session_service import SessionStore
from services.user_service import get_user_by_id, update_user_profile


users_bp = Blueprint("users", __name__, url_prefix="/api/users")
_SESSION_STORE_KEY = "session_store"


def _get_session_store() -> SessionStore:
    store = current_app.extensions.get(_SESSION_STORE_KEY)
    if store is None:
        store = SessionStore()
        current_app.extensions[_SESSION_STORE_KEY] = store
    return store


def _extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization")
    if not header:
        return None
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    return token or None


@users_bp.route("/profile", methods=["PUT"])
def update_profile() -> tuple:
    """Atualiza os dados do perfil do usuario autenticado.
    ---
    tags:
      - Users
    consumes:
      - application/json
    responses:
      200:
        description: Perfil atualizado
      400:
        description: Dados invalidos
      401:
        description: Token ausente ou invalido
    """
    token = _extract_bearer_token()
    if token is None:
        return jsonify({"error": "Missing bearer token"}), 401

    session_store = _get_session_store()
    user_id = session_store.resolve(token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = get_user_by_id(user_id)
    if user is None:
        session_store.destroy(token)
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    try:
        dto = UpdateUserProfileDTO(**payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    updated = update_user_profile(user, dto)
    return jsonify(updated), 200

