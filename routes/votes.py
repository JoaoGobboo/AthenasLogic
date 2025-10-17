from __future__ import annotations

from flask import Blueprint, jsonify

from services import vote_service


votes_bp = Blueprint("votes", __name__, url_prefix="/api/votos")


@votes_bp.route("/<string:tx_hash>/verificar", methods=["GET"])
def verify_vote(tx_hash: str) -> tuple:
    result = vote_service.verify_vote_on_chain(tx_hash)
    if not result.get("verified"):
        status = result.get("status")
        status_code = 404 if status == "not_found" else 400
        return jsonify(result), status_code
    return jsonify(result), 200
