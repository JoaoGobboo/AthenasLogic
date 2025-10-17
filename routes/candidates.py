from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from dtos.candidate_dto import CreateCandidateDTO, UpdateCandidateDTO
from services.candidate_service import (
    create_candidate,
    delete_candidate,
    list_candidates,
    update_candidate,
)
from routes.security import require_auth


candidates_bp = Blueprint("candidates", __name__)


def _format_validation_error(exc: ValidationError) -> list[str]:
    return [error["msg"] for error in exc.errors()]


@candidates_bp.route("/api/eleicoes/<int:election_id>/candidatos", methods=["POST"])
@require_auth()
def create(election_id: int) -> tuple:
    """Adiciona um candidato a uma eleição.
    ---
    tags:
      - Candidates
    consumes:
      - application/json
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
        description: ID da eleição
      - in: body
        name: payload
        required: true
        schema:
          $ref: '#/definitions/CandidateCreate'
      - name: X-CSRF-Token
        in: header
        type: string
        required: true
        description: Token anti-CSRF retornado pelo login
    responses:
      201:
        description: Candidato criado com sucesso
        schema:
          $ref: '#/definitions/CandidateResponse'
      400:
        description: Dados inválidos ou eleição ativa
        schema:
          type: object
          properties:
            error:
              type: array
              items:
                type: string
      404:
        description: Eleição não encontrada
    definitions:
      CandidateResponse:
        type: object
        properties:
          id:
            type: integer
            format: int64
          nome:
            type: string
          eleicao_id:
            type: integer
            format: int64
          votos_count:
            type: integer
          blockchain_tx:
            type: string
            x-nullable: true
      CandidateCreate:
        type: object
        required:
          - nome
        properties:
          nome:
            type: string
            minLength: 1
            maxLength: 255
      CandidateUpdate:
        type: object
        properties:
          nome:
            type: string
            minLength: 1
            maxLength: 255
    """
    data = request.get_json(silent=True) or {}
    try:
        dto = CreateCandidateDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    candidate = create_candidate(election_id, dto)
    return jsonify(candidate), 201


@candidates_bp.route("/api/eleicoes/<int:election_id>/candidatos", methods=["GET"])
def index(election_id: int) -> tuple:
    """Lista todos os candidatos de uma eleição.
    ---
    tags:
      - Candidates
    parameters:
      - name: election_id
        in: path
        required: true
        type: integer
        format: int64
        description: ID da eleição
    responses:
      200:
        description: Lista de candidatos
        schema:
          type: array
          items:
            $ref: '#/definitions/CandidateResponse'
      404:
        description: Eleição não encontrada
    """
    candidates = list_candidates(election_id)
    return jsonify(candidates), 200


@candidates_bp.route("/api/candidatos/<int:candidate_id>", methods=["PUT"])
@require_auth()
def update(candidate_id: int) -> tuple:
    """Atualiza os dados de um candidato.
    ---
    tags:
      - Candidates
    parameters:
      - name: candidate_id
        in: path
        required: true
        type: integer
        format: int64
        description: ID do candidato
      - name: X-CSRF-Token
        in: header
        type: string
        required: true
        description: Token anti-CSRF retornado pelo login
      - in: body
        name: payload
        required: true
        schema:
          $ref: '#/definitions/CandidateUpdate'
      - name: X-CSRF-Token
        in: header
        type: string
        required: true
        description: Token anti-CSRF retornado pelo login
    responses:
      200:
        description: Candidato atualizado
        schema:
          $ref: '#/definitions/CandidateResponse'
      400:
        description: Dados inválidos ou eleição ativa
        schema:
          type: object
          properties:
            error:
              type: array
              items:
                type: string
      404:
        description: Candidato não encontrado
    """
    data = request.get_json(silent=True) or {}
    try:
        dto = UpdateCandidateDTO(**data)
    except ValidationError as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400
    candidate = update_candidate(candidate_id, dto)
    return jsonify(candidate), 200


@candidates_bp.route("/api/candidatos/<int:candidate_id>", methods=["DELETE"])
@require_auth()
def delete(candidate_id: int) -> tuple:
    """Remove um candidato.
    ---
    tags:
      - Candidates
    parameters:
      - name: candidate_id
        in: path
        required: true
        type: integer
        format: int64
        description: ID do candidato
    responses:
      204:
        description: Candidato removido
      400:
        description: Eleição ativa (não pode remover)
      404:
        description: Candidato não encontrado
    """
    delete_candidate(candidate_id)
    return "", 204
