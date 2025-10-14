# routes/audit.py

from flask import Blueprint, jsonify
from ..services.audit_service import AuditService

audit_bp = Blueprint('audit_bp', __name__, url_prefix='/api/audit')

@audit_bp.route('/logs', methods=['GET'])
def get_audit_logs():
    """Endpoint para obter todos os logs de auditoria."""
    logs = AuditService.get_all_logs()
    if logs is None:
        return jsonify({"error": "Falha ao buscar logs de auditoria"}), 500
        
    # Serializando os objetos para JSON!
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
    """Endpoint para obter os logs de auditoria de uma eleição específica."""
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