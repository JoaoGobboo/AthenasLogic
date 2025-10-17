from __future__ import annotations

import logging
from typing import Optional

from flask import abort
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from dtos.vote_dto import CastVoteDTO
from models import Candidato, Eleicao, Voto, db
from services.blockchain_integration import (
    is_blockchain_enabled,
    record_vote_onchain,
    verify_transaction_on_chain,
)
from services.election_service import serialize_election


logger = logging.getLogger(__name__)


def _normalize_hash(value: str) -> str:
    return value.lower()


def _sync_vote_on_blockchain(candidate_index: int) -> str | None:
    if not is_blockchain_enabled():
        return None
    try:
        receipt = record_vote_onchain(candidate_index)
    except Exception as exc:  # pragma: no cover - surfaced via API response
        logger.error("Blockchain vote failed: %s", exc)
        abort(502, description=f"Blockchain sync failed during vote: {exc}")
    if receipt is None:
        return None
    return receipt.transactionHash.hex()


def register_vote(election_id: int, dto: CastVoteDTO) -> dict:
    election: Optional[Eleicao] = db.session.get(Eleicao, election_id)
    if election is None:
        abort(404, description="Election not found")
    if not election.ativa:
        abort(400, description="Election is not active")

    candidate: Optional[Candidato] = db.session.get(Candidato, dto.candidato_id)
    if candidate is None or candidate.eleicao_id != election_id:
        abort(404, description="Candidate not found for this election")

    vote = Voto(
        eleicao_id=election_id,
        candidato_id=candidate.id,
        hash_blockchain=_normalize_hash(dto.hash_blockchain),
    )
    candidate.votos_count = (candidate.votos_count or 0) + 1
    db.session.add(vote)

    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        abort(409, description="Vote already registered")

    receipt_hash = _sync_vote_on_blockchain(candidate.id)

    try:
        db.session.commit()
    except HTTPException:
        db.session.rollback()
        raise
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Failed to register vote: %s", exc)
        raise

    db.session.refresh(vote)
    db.session.refresh(candidate)
    payload = {
        "id": vote.id,
        "eleicao_id": election_id,
        "candidato_id": candidate.id,
        "hash_blockchain": vote.hash_blockchain,
        "total_votos_candidato": candidate.votos_count,
    }
    if receipt_hash:
        payload["blockchain_tx"] = receipt_hash
    return payload


def get_election_results(election_id: int) -> dict:
    election: Optional[Eleicao] = db.session.get(Eleicao, election_id)
    if election is None:
        abort(404, description="Election not found")

    candidates = (
        db.session.query(Candidato)
        .filter_by(eleicao_id=election_id)
        .order_by(Candidato.votos_count.desc(), Candidato.id.asc())
        .all()
    )
    total_votes = sum(candidate.votos_count or 0 for candidate in candidates)
    return {
        "election": serialize_election(election),
        "results": [
            {
                "id": candidate.id,
                "nome": candidate.nome,
                "votos": candidate.votos_count,
            }
            for candidate in candidates
        ],
        "total_votos": total_votes,
    }


def get_election_status(election_id: int) -> dict:
    election: Optional[Eleicao] = db.session.get(Eleicao, election_id)
    if election is None:
        abort(404, description="Election not found")

    total_votes = (
        db.session.query(func.count(Voto.id))
        .filter_by(eleicao_id=election_id)
        .scalar()
        or 0
    )
    total_candidates = (
        db.session.query(func.count(Candidato.id))
        .filter_by(eleicao_id=election_id)
        .scalar()
        or 0
    )
    return {
        "election": serialize_election(election),
        "total_votos": int(total_votes),
        "total_candidatos": int(total_candidates),
    }


def verify_vote_on_chain(tx_hash: str) -> dict:
    cleaned = tx_hash.strip()
    if not cleaned:
        return {
            "verified": False,
            "status": "error",
            "message": "Transaction hash is required",
        }
    return verify_transaction_on_chain(cleaned)


__all__ = [
    "register_vote",
    "get_election_results",
    "get_election_status",
    "verify_vote_on_chain",
]
