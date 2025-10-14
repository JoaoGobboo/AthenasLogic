# services/audit_service.py

from ..models.audit_log import AuditLog
from ..models.eleicao import Eleicao # Supondo que você tenha um modelo Eleicao
from sqlalchemy import desc

class AuditService:

    @staticmethod
    def get_all_logs():
        """Retorna todos os logs de auditoria, ordenados pelo mais recente."""
        try:
            logs = AuditLog.query.order_by(desc(AuditLog.timestamp)).all()
            return logs
        except Exception as e:
            # É uma boa prática logar o erro real em um sistema de produção
            print(f"Erro ao buscar logs de auditoria: {e}")
            return None

    @staticmethod
    def get_logs_for_election(election_id: int):
        """
        Retorna os logs de auditoria para uma eleição específica.
        
        NOTA: Esta função assume que o campo 'detalhes' no AuditLog 
        contém alguma referência à eleição, como 'eleicao_id: {id}'.
        Se a relação for mais complexa, esta query precisará ser ajustada.
        """
        try:
            # Verifica se a eleição existe primeiro
            eleicao = Eleicao.query.get(election_id)
            if not eleicao:
                return None # Ou levantar um erro específico de "Não Encontrado"

            # Busca por logs onde o campo 'detalhes' menciona a eleição
            # Esta é uma abordagem. Uma melhor seria ter um `eleicao_id` no próprio AuditLog
            search_pattern = f'%eleicao_id": {election_id}%' # Exemplo se 'detalhes' for um JSON string
            
            logs = AuditLog.query.filter(AuditLog.detalhes.like(search_pattern)).order_by(desc(AuditLog.timestamp)).all()
            return logs
        except Exception as e:
            print(f"Erro ao buscar logs para a eleição {election_id}: {e}")
            return []