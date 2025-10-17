# -*- coding: utf-8 -*-

import logging

from sqlalchemy import select

from models import AuditLog, Eleicao, db


logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def get_all_logs() -> list[AuditLog]:
        """Retorna todos os logs de auditoria, ordenados pelo mais recente."""
        try:
            stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
            return list(db.session.execute(stmt).scalars())
        except Exception as exc:  # pragma: no cover - surfaced via API error handler
            logger.exception("Failed to fetch audit logs")
            raise exc

    @staticmethod
    def get_logs_for_election(election_id: int) -> list[AuditLog] | None:
        """Retorna os logs de auditoria para uma eleição específica."""
        try:
            election = db.session.get(Eleicao, election_id)
            if election is None:
                return None

            stmt = (
                select(AuditLog)
                .where(AuditLog.eleicao_id == election_id)
                .order_by(AuditLog.timestamp.desc())
            )
            return list(db.session.execute(stmt).scalars())
        except Exception as exc:  # pragma: no cover - surfaced via API error handler
            logger.exception("Failed to fetch audit logs for election_id=%s", election_id)
            raise exc
