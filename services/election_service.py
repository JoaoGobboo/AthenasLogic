from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from flask import abort
from werkzeug.exceptions import HTTPException

from dtos.election_dto import CreateElectionDTO, UpdateElectionDTO
from models import Eleicao, db
from services.blockchain_integration import (
    close_election_onchain,
    configure_election_onchain,
    is_blockchain_enabled,
    open_election_onchain,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _attach_receipt(payload: dict, receipt_hash: str | None) -> dict:
    if receipt_hash:
        payload = dict(payload)
        payload["blockchain_tx"] = receipt_hash
    return payload


def _sync_blockchain(action: str, callback, *args) -> str | None:
    if not is_blockchain_enabled():
        return None
    try:
        receipt = callback(*args)
    except Exception as exc:  # pragma: no cover - surfaced via API response
        logging.error("Blockchain sync failed during %s: %s", action, exc)
        abort(502, description=f"Blockchain sync failed during {action}: {exc}")
    if receipt is None:
        return None
    return receipt.transactionHash.hex()


def serialize_election(election: Eleicao) -> dict:
    return {
        "id": election.id,
        "titulo": election.titulo,
        "descricao": election.descricao,
        "data_inicio": _serialize_datetime(_normalize_dt(election.data_inicio)),
        "data_fim": _serialize_datetime(_normalize_dt(election.data_fim)),
        "ativa": bool(election.ativa),
    }


def create_election(dto: CreateElectionDTO) -> dict:
    try:
        election = Eleicao(
            titulo=dto.titulo,
            descricao=dto.descricao,
            data_inicio=_normalize_dt(dto.data_inicio),
            data_fim=_normalize_dt(dto.data_fim),
            ativa=dto.ativa if dto.ativa is not None else False,
        )
        db.session.add(election)
        db.session.flush()
        receipt_hash = _sync_blockchain(
            "configure_election",
            configure_election_onchain,
            dto.titulo,
            dto.candidatos or [],
        )
        db.session.commit()
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise

    return _attach_receipt(serialize_election(election), receipt_hash)


def list_elections() -> list[dict]:
    elections: Iterable[Eleicao] = (
        db.session.query(Eleicao).order_by(Eleicao.id.asc()).all()
    )
    return [serialize_election(election) for election in elections]


def get_election(election_id: int) -> Eleicao | None:
    return db.session.get(Eleicao, election_id)


def update_election(election_id: int, dto: UpdateElectionDTO) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")

    if dto.ativa is not None:
        abort(400, description="Election status must be changed via start/end endpoints")

    current_inicio = _normalize_dt(election.data_inicio)
    current_fim = _normalize_dt(election.data_fim)

    new_start = _normalize_dt(dto.data_inicio) if dto.data_inicio is not None else current_inicio
    new_end = _normalize_dt(dto.data_fim) if dto.data_fim is not None else current_fim
    if new_start and new_end and new_end <= new_start:
        abort(400, description="data_fim must be after data_inicio")

    if dto.titulo is not None:
        election.titulo = dto.titulo
    if dto.descricao is not None:
        election.descricao = dto.descricao
    if dto.data_inicio is not None:
        election.data_inicio = new_start
    if dto.data_fim is not None:
        election.data_fim = new_end

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return serialize_election(election)


def delete_election(election_id: int) -> None:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    if election.ativa:
        abort(400, description="Cannot delete an active election; end it first")
    if is_blockchain_enabled():
        abort(501, description="Deleting elections is unsupported while blockchain sync is enabled")

    try:
        db.session.delete(election)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def start_election(election_id: int) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    if election.ativa:
        abort(400, description="Election already active")

    now = _utcnow()
    normalized_end = _normalize_dt(election.data_fim)
    if normalized_end and normalized_end <= now:
        abort(400, description="Election end date must be in the future to start")

    try:
        election.data_inicio = now
        election.data_fim = normalized_end
        election.ativa = True
        db.session.flush()
        receipt_hash = _sync_blockchain("open_election", open_election_onchain)
        db.session.commit()
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise

    return _attach_receipt(serialize_election(election), receipt_hash)


def end_election(election_id: int) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    if not election.ativa:
        abort(400, description="Election already inactive")

    now = _utcnow()
    normalized_start = _normalize_dt(election.data_inicio)
    if normalized_start and now < normalized_start:
        abort(400, description="data_fim must be after data_inicio")

    try:
        election.data_fim = now
        election.data_inicio = normalized_start
        election.ativa = False
        db.session.flush()
        receipt_hash = _sync_blockchain("close_election", close_election_onchain)
        db.session.commit()
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise

    return _attach_receipt(serialize_election(election), receipt_hash)
