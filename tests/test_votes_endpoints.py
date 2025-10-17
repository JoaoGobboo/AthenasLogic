from datetime import datetime, timedelta, timezone

import pytest

from models import Candidato, Eleicao, Voto, db


def _seed_election(*, ativa: bool = True) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    election = Eleicao(
        titulo="Eleicao Teste",
        descricao="Eleicao para testes de votos",
        data_inicio=now - timedelta(hours=1),
        data_fim=now + timedelta(days=1),
        ativa=ativa,
    )
    db.session.add(election)
    db.session.flush()

    candidate = Candidato(
        nome="Candidata 1",
        eleicao_id=election.id,
        votos_count=0,
    )
    db.session.add(candidate)
    db.session.commit()
    return election.id, candidate.id


@pytest.mark.usefixtures("client")
def test_cast_vote_success(client):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xABC123"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["eleicao_id"] == election_id
    assert body["candidato_id"] == candidate_id
    assert body["hash_blockchain"] == "0xabc123"

    with client.application.app_context():
        candidate = db.session.get(Candidato, candidate_id)
        assert candidate.votos_count == 1
        vote = db.session.query(Voto).filter_by(eleicao_id=election_id).one()
        assert vote.hash_blockchain == "0xabc123"


@pytest.mark.usefixtures("client")
def test_cast_vote_requires_active_election(client):
    with client.application.app_context():
        election_id, candidate_id = _seed_election(ativa=False)

    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xdead"},
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("client")
def test_cast_vote_rejects_duplicate_hash(client):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    payload = {"candidato_id": candidate_id, "hash_blockchain": "0xdup01"}
    first = client.post(f"/api/eleicoes/{election_id}/votar", json=payload)
    assert first.status_code == 201

    second = client.post(f"/api/eleicoes/{election_id}/votar", json=payload)
    assert second.status_code == 409


@pytest.mark.usefixtures("client")
def test_election_results_returns_vote_totals(client):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()
        other_candidate = Candidato(nome="Candidata 2", eleicao_id=election_id, votos_count=0)
        db.session.add(other_candidate)
        db.session.commit()
        other_candidate_id = other_candidate.id

    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xvote1"},
    )
    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": other_candidate_id, "hash_blockchain": "0xvote2"},
    )

    response = client.get(f"/api/eleicoes/{election_id}/resultados")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_votos"] == 2
    votes_by_candidate = {item["id"]: item["votos"] for item in data["results"]}
    assert votes_by_candidate[candidate_id] == 1
    assert votes_by_candidate[other_candidate_id] == 1


@pytest.mark.usefixtures("client")
def test_election_status_returns_summary(client):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xstatus"},
    )

    response = client.get(f"/api/eleicoes/{election_id}/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_votos"] == 1
    assert data["total_candidatos"] >= 1
    assert data["election"]["ativa"] is True


@pytest.mark.usefixtures("client")
def test_verify_vote_route_handles_not_found(client, monkeypatch):
    def fake_verify(tx_hash: str):
        return {"verified": False, "status": "not_found", "message": "missing"}

    monkeypatch.setattr("routes.votes.vote_service.verify_vote_on_chain", fake_verify)

    response = client.get("/api/votos/0xNOTFOUND/verificar")
    assert response.status_code == 404


@pytest.mark.usefixtures("client")
def test_verify_vote_route_success(client, monkeypatch):
    def fake_verify(tx_hash: str):
        return {
            "verified": True,
            "status": "success",
            "transactionHash": tx_hash,
        }

    monkeypatch.setattr("routes.votes.vote_service.verify_vote_on_chain", fake_verify)

    response = client.get("/api/votos/0xOK/verificar")
    assert response.status_code == 200
    data = response.get_json()
    assert data["verified"] is True
