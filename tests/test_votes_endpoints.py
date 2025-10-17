from datetime import datetime, timedelta, timezone

import pytest

from models import Candidato, Eleicao, Voto, db
from services.auth_service import ServiceResponse


AUTH_ADDRESS = "0x00000000000000000000000000000000000000cc"


def _auth_headers(client, monkeypatch) -> dict:
    def fake_get_web3():
        return object()

    def fake_verify_signature_response(address, signature, store, web3):
        return ServiceResponse(payload={"success": True, "address": address}, status=200)

    monkeypatch.setattr("routes.auth.get_web3", fake_get_web3)
    monkeypatch.setattr("routes.auth.verify_signature_response", fake_verify_signature_response)

    response = client.post(
        "/api/auth/login",
        json={"address": AUTH_ADDRESS, "signature": "0xsignature"},
    )
    assert response.status_code == 200
    data = response.get_json()
    return {
        "Authorization": f"Bearer {data['token']}",
        "X-CSRF-Token": data["csrf_token"],
    }


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
def test_cast_vote_success(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    headers = _auth_headers(client, monkeypatch)
    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xABC123"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["eleicao_id"] == election_id
    assert body["candidato_id"] == candidate_id
    assert body["hash_blockchain"] == "0xabc123"

    with client.application.app_context():
        total_votes = db.session.query(Voto).filter_by(candidato_id=candidate_id).count()
        assert total_votes == 1
        vote = db.session.query(Voto).filter_by(eleicao_id=election_id).one()
        assert vote.hash_blockchain == "0xabc123"


@pytest.mark.usefixtures("client")
def test_cast_vote_requires_active_election(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election(ativa=False)

    headers = _auth_headers(client, monkeypatch)
    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xdead"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("client")
def test_cast_vote_rejects_duplicate_hash(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    headers = _auth_headers(client, monkeypatch)
    payload = {"candidato_id": candidate_id, "hash_blockchain": "0xdup01"}
    first = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json=payload,
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json=payload,
        headers=headers,
    )
    assert second.status_code == 409


@pytest.mark.usefixtures("client")
def test_election_results_returns_vote_totals(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()
        other_candidate = Candidato(nome="Candidata 2", eleicao_id=election_id, votos_count=0)
        db.session.add(other_candidate)
        db.session.commit()
        other_candidate_id = other_candidate.id

    headers = _auth_headers(client, monkeypatch)
    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xvote1"},
        headers=headers,
    )
    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": other_candidate_id, "hash_blockchain": "0xvote2"},
        headers=headers,
    )

    response = client.get(f"/api/eleicoes/{election_id}/resultados")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_votos"] == 2
    votes_by_candidate = {item["id"]: item["votos"] for item in data["results"]}
    assert votes_by_candidate[candidate_id] == 1
    assert votes_by_candidate[other_candidate_id] == 1


@pytest.mark.usefixtures("client")
def test_election_status_returns_summary(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    headers = _auth_headers(client, monkeypatch)
    client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xstatus"},
        headers=headers,
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


class _DummyReceipt:
    def __init__(self, value: str) -> None:
        self.transactionHash = _HexStub(value)


class _HexStub:
    def __init__(self, value: str) -> None:
        self._value = value

    def hex(self) -> str:
        return self._value


@pytest.mark.usefixtures("client")
def test_cast_vote_attaches_blockchain_hash_when_sync_succeeds(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()
        candidate = db.session.get(Candidato, candidate_id)
        candidate.blockchain_index = None
        db.session.commit()

    headers = _auth_headers(client, monkeypatch)

    monkeypatch.setattr("services.vote_service.is_blockchain_enabled", lambda: True)
    monkeypatch.setattr(
        "services.vote_service.record_vote_onchain",
        lambda index: _DummyReceipt(f"0xmock{index}")
    )

    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xABCDEF"},
        headers=headers,
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["blockchain_tx"] == "0xmock0"


@pytest.mark.usefixtures("client")
def test_cast_vote_returns_502_when_blockchain_sync_fails(client, monkeypatch):
    with client.application.app_context():
        election_id, candidate_id = _seed_election()

    headers = _auth_headers(client, monkeypatch)

    monkeypatch.setattr("services.vote_service.is_blockchain_enabled", lambda: True)

    def failing_sync(_index: int):  # pragma: no cover - path under test
        raise RuntimeError("rpc unavailable")

    monkeypatch.setattr("services.vote_service.record_vote_onchain", failing_sync)

    response = client.post(
        f"/api/eleicoes/{election_id}/votar",
        json={"candidato_id": candidate_id, "hash_blockchain": "0xdeadbeef"},
        headers=headers,
    )

    assert response.status_code == 502
    body = response.get_json()
    assert "blockchain" in body.get("description", "").lower()
