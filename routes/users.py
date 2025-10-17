from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from dtos.user_dto import UpdateUserProfileDTO
from routes.security import require_auth
from services.user_service import update_user_profile


users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/profile", methods=["PUT"])
@require_auth()
def update_profile() -> tuple:
    """Atualiza os dados do perfil do usuario autenticado (requer X-CSRF-Token).
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
    payload = request.get_json(silent=True) or {}
    try:
        dto = UpdateUserProfileDTO(**payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    updated = update_user_profile(g.current_user, dto)
    return jsonify(updated), 200
