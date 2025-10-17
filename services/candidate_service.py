from __future__ import annotations

import logging

from flask import abort
from sqlalchemy import func, select
from werkzeug.exceptions import HTTPException

from dtos.candidate_dto import CreateCandidateDTO, UpdateCandidateDTO
from models import Candidato, Eleicao, Voto, db
from services.blockchain_integration import add_candidate_onchain, is_blockchain_enabled


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


def _candidate_vote_total(candidate_id: int) -> int:
    stmt = select(func.count(Voto.id)).where(Voto.candidato_id == candidate_id)
    return int(db.session.execute(stmt).scalar_one() or 0)


def ensure_candidate_indices(election_id: int) -> dict[int, int]:
    """Garantir que os índices locais reflitam a ordem 0-based usada no contrato."""
    candidates = (
        db.session.query(Candidato)
        .filter_by(eleicao_id=election_id)
        .order_by(Candidato.id.asc())
        .all()
    )

    mapping: dict[int, int] = {}
    updated_ids: list[int] = []
    for position, candidate in enumerate(candidates):
        mapping[candidate.id] = position
        if candidate.blockchain_index != position:
            candidate.blockchain_index = position
            updated_ids.append(candidate.id)

    if updated_ids:
        db.session.flush()
        logging.info(
            "Reindexed blockchain candidates for election_id=%s; updated_ids=%s",
            election_id,
            updated_ids,
        )

    return mapping


def validate_candidate_indices(election_id: int) -> bool:
    """Verifica se os índices persistidos estão coerentes sem alterar os dados."""
    candidates = (
        db.session.query(Candidato)
        .filter_by(eleicao_id=election_id)
        .order_by(Candidato.id.asc())
        .all()
    )
    return all(
        candidate.blockchain_index == position for position, candidate in enumerate(candidates)
    )


def serialize_candidate(candidate: Candidato) -> dict:
    return {
        "id": candidate.id,
        "nome": candidate.nome,
        "eleicao_id": candidate.eleicao_id,
        "votos_count": _candidate_vote_total(candidate.id),
        "blockchain_index": candidate.blockchain_index,
    }


def create_candidate(election_id: int, dto: CreateCandidateDTO) -> dict:
    election = db.session.get(Eleicao, election_id)
    if not election:
        abort(404, description="Election not found")

    if election.ativa:
        abort(400, description="Cannot add candidates to an active election")

    try:
        candidate = Candidato(
            nome=dto.nome,
            eleicao_id=election_id,
            votos_count=0,
        )
        db.session.add(candidate)
        db.session.flush()
        ensure_candidate_indices(election_id)
        receipt_hash = _sync_blockchain("add_candidate", add_candidate_onchain, dto.nome)
        db.session.commit()
    except HTTPException:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise

    return _attach_receipt(serialize_candidate(candidate), receipt_hash)


def list_candidates(election_id: int) -> list[dict]:
    election = db.session.get(Eleicao, election_id)
    if not election:
        abort(404, description="Election not found")

    ensure_candidate_indices(election_id)

    candidates = (
        db.session.query(Candidato)
        .filter_by(eleicao_id=election_id)
        .order_by(Candidato.id.asc())
        .all()
    )
    return [serialize_candidate(candidate) for candidate in candidates]


def get_candidate(candidate_id: int) -> Candidato | None:
    return db.session.get(Candidato, candidate_id)


def update_candidate(candidate_id: int, dto: UpdateCandidateDTO) -> dict:
    candidate = get_candidate(candidate_id)
    if not candidate:
        abort(404, description="Candidate not found")

    election = db.session.get(Eleicao, candidate.eleicao_id)
    if election and election.ativa:
        abort(400, description="Cannot update candidates in an active election")

    if dto.nome is not None:
        candidate.nome = dto.nome

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return serialize_candidate(candidate)


def delete_candidate(candidate_id: int) -> None:
    candidate = get_candidate(candidate_id)
    if not candidate:
        abort(404, description="Candidate not found")

    if is_blockchain_enabled():
        abort(501, description="Deleting candidates is unsupported while blockchain sync is enabled")

    election = db.session.get(Eleicao, candidate.eleicao_id)
    if election and election.ativa:
        abort(400, description="Cannot delete candidates from an active election")

    try:
        db.session.delete(candidate)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


__all__ = [
    "serialize_candidate",
    "create_candidate",
    "list_candidates",
    "get_candidate",
    "update_candidate",
    "delete_candidate",
    "ensure_candidate_indices",
    "validate_candidate_indices",
]
