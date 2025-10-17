from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from dtos.election_dto import CreateElectionDTO, UpdateElectionDTO
from dtos.vote_dto import CastVoteDTO
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

from services.vote_service import (
    get_election_results,
    get_election_status,
    register_vote,
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
    """Cria uma nova eleição.
    ---
    tags:
      - Elections
    consumes:
      - application/json
    parameters:
      - in: body
        name: payload
        required: true
        schema:
          $ref: '#/definitions/ElectionCreate'
    responses:
      201:
        description: Eleição criada com sucesso
        schema:
          $ref: '#/definitions/ElectionResponse'
      400:
        description: Dados inválidos
        schema:
          type: object
          properties:
            error:
              type: array
              items:
                type: string
    definitions:
      ElectionResponse:
        type: object
        properties:
          id:
            type: integer
            format: int64
          titulo:
            type: string
          descricao:
            type: string
            x-nullable: true
          data_inicio:
            type: string
          data_fim:
            type: string
          ativa:
            type: boolean
          blockchain_tx:
            type: string
            x-nullable: true
      ElectionCreate:
        type: object
        required:
          - titulo
          - data_inicio
          - data_fim
        properties:
          titulo:
            type: string
            minLength: 1
            maxLength: 255
          descricao:
            type: string
          data_inicio:
            type: string
            format: date-time
          data_fim:
            type: string
            format: date-time
          ativa:
            type: boolean
          candidatos:
            type: array
            items:
              type: string
      ElectionUpdate:
        type: object
        properties:
          titulo:
            type: string
          descricao:
            type: string
          data_inicio:
            type: string
            format: date-time
          data_fim:
            type: string
            format: date-time
          ativa:
            type: boolean
          candidatos:
            type: array
            items:
              type: string
    """
    data = request.get_json(silent=True) or {}
    try:
        dto = CreateElectionDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    election = create_election(dto)
    return jsonify(election), 201


@elections_bp.route("/api/eleicoes", methods=["GET"])
def index() -> tuple:
    """Lista eleições cadastradas.
    ---
    tags:
      - Elections
    responses:
      200:
        description: Lista de eleições
        schema:
          type: array
          items:
            $ref: '#/definitions/ElectionResponse'
    """
    elections = list_elections()
    return jsonify(elections), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["GET"])
def show(election_id: int) -> tuple:
    """Retorna os detalhes de uma eleição.
    ---
    tags:
      - Elections
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
    responses:
      200:
        description: Detalhes da eleição
        schema:
          $ref: '#/definitions/ElectionResponse'
      404:
        description: Eleição não encontrada
    """
    election = _serialize_or_404(election_id)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["PUT"])
def update(election_id: int) -> tuple:
    """Atualiza campos editáveis da eleição.
    ---
    tags:
      - Elections
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
      - in: body
        name: payload
        required: true
        schema:
          $ref: '#/definitions/ElectionUpdate'
    responses:
      200:
        description: Eleição atualizada
        schema:
          $ref: '#/definitions/ElectionResponse'
      400:
        description: Dados inválidos
        schema:
          type: object
          properties:
            error:
              type: array
              items:
                type: string
      404:
        description: Eleição não encontrada
    """
    data = request.get_json(silent=True) or {}
    try:
        dto = UpdateElectionDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    election = update_election(election_id, dto)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>", methods=["DELETE"])
def delete(election_id: int) -> tuple:
    """Remove a eleição informada.
    ---
    tags:
      - Elections
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
    responses:
      204:
        description: Eleição removida
      404:
        description: Eleição não encontrada
    """
    delete_election(election_id)
    return "", 204


@elections_bp.route("/api/eleicoes/<int:election_id>/start", methods=["POST"])
def start(election_id: int) -> tuple:
    """Inicia a eleição e opcionalmente sincroniza com o contrato.
    ---
    tags:
      - Elections
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
    responses:
      200:
        description: Eleição iniciada
        schema:
          $ref: '#/definitions/ElectionResponse'
      400:
        description: Eleição já ativa ou datas inválidas
      404:
        description: Eleição não encontrada
    """
    election = start_election(election_id)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>/end", methods=["POST"])
def end(election_id: int) -> tuple:
    """Encerra a eleição e opcionalmente sincroniza com o contrato.
    ---
    tags:
      - Elections
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
    responses:
      200:
        description: Eleição encerrada
        schema:
          $ref: '#/definitions/ElectionResponse'
      400:
        description: Eleição já inativa ou datas inválidas
      404:
        description: Eleição não encontrada
    """
    election = end_election(election_id)
    return jsonify(election), 200


@elections_bp.route("/api/eleicoes/<int:election_id>/votar", methods=["POST"])
def cast_vote(election_id: int) -> tuple:
    payload = request.get_json(silent=True) or {}
    try:
        dto = CastVoteDTO(**payload)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    vote = register_vote(election_id, dto)
    return jsonify(vote), 201


@elections_bp.route("/api/eleicoes/<int:election_id>/resultados", methods=["GET"])
def election_results(election_id: int) -> tuple:
    results = get_election_results(election_id)
    return jsonify(results), 200


@elections_bp.route("/api/eleicoes/<int:election_id>/status", methods=["GET"])
def election_status(election_id: int) -> tuple:
    status = get_election_status(election_id)
    return jsonify(status), 200
