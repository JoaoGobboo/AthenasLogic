"""Seed script for audit-related tables.

Creates a sample usuario, eleicao, and a few audit log entries so that
local manual tests (curl, swagger) have data to display.

Usage:
    SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db python scripts/seed_audit_logs.py
If SQLALCHEMY_DATABASE_URI is not provided, defaults to the path above.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_URI = f"sqlite:///{PROJECT_ROOT / 'instance' / 'app.db'}"


def _normalize_sqlite_uri(uri: str) -> str:
    path = Path(uri.removeprefix("sqlite:///"))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


TARGET_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", DEFAULT_URI)
if TARGET_URI.startswith("sqlite:///"):
    TARGET_URI = _normalize_sqlite_uri(TARGET_URI)

os.environ["SQLALCHEMY_DATABASE_URI"] = TARGET_URI

from app import app, db
from models import AuditLog, Eleicao, Usuario


def _ensure_sqlite_directory(uri: str) -> None:
    if uri.startswith("sqlite:///"):
        db_path = uri.removeprefix("sqlite:///")
        directory = os.path.dirname(db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def _get_or_create_user(wallet: str) -> Usuario:
    user = Usuario.query.filter_by(endereco_wallet=wallet).first()
    if user:
        return user
    user = Usuario(endereco_wallet=wallet)
    db.session.add(user)
    db.session.flush()
    return user


def _get_or_create_election(title: str) -> Eleicao:
    eleicao = Eleicao.query.filter_by(titulo=title).first()
    if eleicao:
        return eleicao
    now = datetime.utcnow()
    eleicao = Eleicao(
        titulo=title,
        descricao="Eleicao ficticia para testes de auditoria",
        data_inicio=now - timedelta(days=1),
        data_fim=now + timedelta(days=1),
        ativa=True,
    )
    db.session.add(eleicao)
    db.session.flush()
    return eleicao


def _create_audit_logs(user: Usuario, eleicao: Eleicao) -> None:
    existing = AuditLog.query.filter_by(usuario_id=user.id).all()
    if existing:
        return

    base_timestamp = datetime.utcnow()
    entries = [
        (
            "CRIAR_ELEICAO",
            base_timestamp - timedelta(minutes=10),
            {
                "eleicao_id": eleicao.id,
                "descricao": "Eleicao criada para validacao manual",
            },
        ),
        (
            "ATUALIZAR_ELEICAO",
            base_timestamp - timedelta(minutes=5),
            {
                "eleicao_id": eleicao.id,
                "descricao": "Descricao ajustada",
            },
        ),
        (
            "FINALIZAR_ELEICAO",
            base_timestamp - timedelta(minutes=1),
            {
                "eleicao_id": eleicao.id,
                "descricao": "Votacao encerrada automaticamente",
            },
        ),
    ]
    for acao, timestamp, payload in entries:
        log = AuditLog(
            acao=acao,
            usuario_id=user.id,
            timestamp=timestamp,
            detalhes=json.dumps(payload, ensure_ascii=True),
        )
        db.session.add(log)


if __name__ == "__main__":
    uri = os.getenv("SQLALCHEMY_DATABASE_URI", DEFAULT_URI)
    _ensure_sqlite_directory(uri)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    with app.app_context():
        db.engine.dispose()
        db.create_all()
        usuario = _get_or_create_user("0xTESTUSERAUDIT")
        eleicao = _get_or_create_election("Eleicao Piloto 2025")
        _create_audit_logs(usuario, eleicao)
        db.session.commit()
        print("Seed concluido com sucesso.")
        print(f"Usuario id={usuario.id}, Eleicao id={eleicao.id}")
        print(f"AuditLogs total = {AuditLog.query.count()}")
