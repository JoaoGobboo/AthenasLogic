from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from dtos.election_dto import CreateElectionDTO, UpdateElectionDTO
from services.election_service import (
    create_election,
    delete_election,
    end_election,
    get_election,
    list_elections,
    serialize_election,
    start_election,
    update_election,
)


elections_bp = Blueprint("elections", __name__)


def _serialize_or_404(election_id: int) -> dict:
    election = get_election(election_id)
    if election is None:
        abort(404, description="Election not found")
    return serialize_election(election)


def _format_validation_error(exc: ValidationError) -> list[str]:
    return [error["msg"] for error in exc.errors()]


@elections_bp.route("/api/eleicoes", methods=["POST"])
def create() -> tuple:
    data = request.get_json(silent=True) or {}
    try:
        dto = CreateElectionDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    election = create_election(dto)
    return jsonify(election), 201


@elections_bp.route("/api/eleicoes", methods=["GET"])
def index() -> tuple:
    elections = list_elections()
    return jsonify(elections), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["GET"])
def show(election_id: int) -> tuple:
    election = _serialize_or_404(election_id)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["PUT"])
def update(election_id: int) -> tuple:
    data = request.get_json(silent=True) or {}
    try:
        dto = UpdateElectionDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    election = update_election(election_id, dto)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["DELETE"])
def delete(election_id: int) -> tuple:
    delete_election(election_id)
    return "", 204


@elections_bp.route("/api/eleicoes/<int:election_id>/start", methods=["POST"])
def start(election_id: int) -> tuple:
    election = start_election(election_id)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>/end", methods=["POST"])
def end(election_id: int) -> tuple:
    election = end_election(election_id)
    return jsonify(election), 200
