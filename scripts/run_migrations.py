"""Simple migration runner to align schema with latest models.

Usage:
    SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://... python scripts/run_migrations.py
"""
from __future__ import annotations

import json
import logging
from contextlib import suppress

from sqlalchemy import Index, inspect, select, text

from app import app, db
from models import AuditLog, SessionToken


logger = logging.getLogger(__name__)


def _ensure_session_store(inspector) -> None:
    if "session_store" not in inspector.get_table_names():
        logger.info("Creating session_store table")
        SessionToken.__table__.create(bind=db.engine)
    Index("ix_session_store_expires_at", SessionToken.expires_at).create(bind=db.engine, checkfirst=True)


def _ensure_audit_log_column(inspector) -> None:
    column_names = {column["name"] for column in inspector.get_columns("audit_logs")}
    if "eleicao_id" not in column_names:
        logger.info("Adding eleicao_id column to audit_logs")
        dialect = db.engine.dialect.name
        column_sql = "ALTER TABLE audit_logs ADD COLUMN eleicao_id INTEGER"
        if dialect.startswith("mysql"):
            column_sql = "ALTER TABLE audit_logs ADD COLUMN eleicao_id INT NULL"
        db.session.execute(text(column_sql))
        db.session.commit()
    Index("ix_audit_logs_eleicao_id", AuditLog.eleicao_id).create(bind=db.engine, checkfirst=True)


def _backfill_audit_logs() -> None:
    logs = db.session.execute(
        select(AuditLog).where(AuditLog.eleicao_id.is_(None), AuditLog.detalhes.isnot(None))
    ).scalars()
    updated = 0
    for log in logs:
        with suppress(json.JSONDecodeError):
            payload = json.loads(log.detalhes)
            eleicao_id = payload.get("eleicao_id")
            if isinstance(eleicao_id, int):
                log.eleicao_id = eleicao_id
                updated += 1
    if updated:
        db.session.commit()
        logger.info("Backfilled %s audit log entries with eleicao_id", updated)
    else:
        db.session.rollback()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        inspector = inspect(db.engine)
        _ensure_session_store(inspector)
        if "audit_logs" in inspector.get_table_names():
            _ensure_audit_log_column(inspector)
            _backfill_audit_logs()
        else:
            logger.warning("audit_logs table not found; skipping column migration")


if __name__ == "__main__":
    main()
