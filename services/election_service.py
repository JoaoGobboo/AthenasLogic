from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

from flask import abort

from dtos.election_dto import CreateElectionDTO, UpdateElectionDTO
from models import Eleicao, db
from services.blockchain_integration import (
    close_election_onchain,
    configure_election_onchain,
    is_blockchain_enabled,
    open_election_onchain,
)


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
        "data_inicio": _serialize_datetime(election.data_inicio),
        "data_fim": _serialize_datetime(election.data_fim),
        "ativa": bool(election.ativa),
    }


def create_election(dto: CreateElectionDTO) -> dict:
    election = Eleicao(
        titulo=dto.titulo,
        descricao=dto.descricao,
        data_inicio=dto.data_inicio,
        data_fim=dto.data_fim,
        ativa=dto.ativa if dto.ativa is not None else False,
    )
    db.session.add(election)
    db.session.commit()

    receipt_hash = _sync_blockchain(
        "configure_election",
        configure_election_onchain,
        dto.titulo,
        dto.candidatos or [],
    )
    return _attach_receipt(serialize_election(election), receipt_hash)


def list_elections() -> list[dict]:
    elections: Iterable[Eleicao] = Eleicao.query.order_by(Eleicao.id.asc()).all()
    return [serialize_election(election) for election in elections]


def get_election(election_id: int) -> Eleicao | None:
    return Eleicao.query.get(election_id)


def update_election(election_id: int, dto: UpdateElectionDTO) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")

    if dto.titulo is not None:
        election.titulo = dto.titulo
    if dto.descricao is not None:
        election.descricao = dto.descricao
    if dto.data_inicio is not None:
        election.data_inicio = dto.data_inicio
    if dto.data_fim is not None:
        comparison_date = dto.data_inicio if dto.data_inicio is not None else election.data_inicio
        if comparison_date and dto.data_fim <= comparison_date:
            abort(400, description="data_fim must be after data_inicio")
        election.data_fim = dto.data_fim
    if dto.ativa is not None:
        election.ativa = dto.ativa

    db.session.commit()
    return serialize_election(election)


def delete_election(election_id: int) -> None:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    db.session.delete(election)
    db.session.commit()


def start_election(election_id: int) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    if election.ativa:
        abort(400, description="Election already active")

    now = datetime.utcnow()
    election.data_inicio = now
    election.ativa = True
    db.session.commit()

    receipt_hash = _sync_blockchain("open_election", open_election_onchain)
    return _attach_receipt(serialize_election(election), receipt_hash)


def end_election(election_id: int) -> dict:
    election = get_election(election_id)
    if not election:
        abort(404, description="Election not found")
    if not election.ativa:
        abort(400, description="Election already inactive")

    now = datetime.utcnow()
    if election.data_inicio and now < election.data_inicio:
        abort(400, description="data_fim must be after data_inicio")
    election.data_fim = now
    election.ativa = False
    db.session.commit()

    receipt_hash = _sync_blockchain("close_election", close_election_onchain)
    return _attach_receipt(serialize_election(election), receipt_hash)
