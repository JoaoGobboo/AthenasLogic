# routes/audit.py

from flask import Blueprint, jsonify
from services.audit_service import AuditService

audit_bp = Blueprint('audit_bp', __name__, url_prefix='/api/audit')

@audit_bp.route('/logs', methods=['GET'])
def get_audit_logs():
    """
    Lista todos os logs de auditoria do sistema.
    Retorna uma lista de todos os eventos de auditoria registrados, ordenados do mais recente para o mais antigo.
    ---
    tags:
      - audit
    responses:
      200:
        description: Uma lista de logs de auditoria retornada com sucesso.
        schema:
          type: array
          items:
            $ref: '#/definitions/AuditLogResponse'
      500:
        description: Erro interno do servidor ao tentar buscar os logs.
    definitions:
      AuditLogResponse:
        type: object
        properties:
          id:
            type: integer
            description: O ID do log.
          acao:
            type: string
            description: "A ação que foi registrada (ex: 'CRIAR_ELEICAO')."
          usuario_id:
            type: integer
            description: O ID do usuário que realizou a ação.
          timestamp:
            type: string
            format: date-time
            description: O momento em que a ação ocorreu (UTC).
          detalhes:
            type: string
            description: Detalhes adicionais sobre o evento, possivelmente em formato JSON.
    """
    logs = AuditService.get_all_logs()
    if logs is None:
        return jsonify({"error": "Falha ao buscar logs de auditoria"}), 500
        
    logs_data = [
        {
            "id": log.id,
            "acao": log.acao,
            "usuario_id": log.usuario_id,
            "timestamp": log.timestamp.isoformat(),
            "detalhes": log.detalhes
        } for log in logs
    ]
    return jsonify(logs_data), 200

@audit_bp.route('/eleicoes/<int:id>', methods=['GET'])
def get_election_audit_logs(id: int):
    """
    Auditoria de uma eleição específica.
    Retorna os logs de auditoria que pertencem a uma eleição específica, identificada pelo seu ID.
    ---
    tags:
      - audit
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: O ID da eleição a ser auditada.
    responses:
      200:
        description: Uma lista de logs de auditoria para a eleição especificada.
        schema:
          type: array
          items:
            $ref: '#/definitions/AuditLogResponse'
      404:
        description: A eleição com o ID fornecido não foi encontrada.
    """
    logs = AuditService.get_logs_for_election(id)

    if logs is None:
         return jsonify({"error": f"Eleição com id {id} não encontrada."}), 404

    logs_data = [
        {
            "id": log.id,
            "acao": log.acao,
            "usuario_id": log.usuario_id,
            "timestamp": log.timestamp.isoformat(),
            "detalhes": log.detalhes
        } for log in logs
    ]
    return jsonify(logs_data), 200

