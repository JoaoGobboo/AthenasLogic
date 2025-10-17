from datetime import datetime, timedelta, timezone
import uuid

import pytest
from models import Candidato, Eleicao, Voto, db
from services.auth_service import ServiceResponse
from services.candidate_service import ensure_candidate_indices, validate_candidate_indices


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _build_election_payload(offset_days: int = 1) -> dict:
    now = _utc_now()
    return {
        "titulo": "Eleicao de Teste",
        "descricao": "Eleicao para testes automatizados",
        "data_inicio": now.isoformat(),
        "data_fim": (now + timedelta(days=offset_days)).isoformat(),
    }


AUTH_ADDRESS = "0x00000000000000000000000000000000000000aa"


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


def _create_election(client, headers) -> dict:
    response = client.post("/api/eleicoes", json=_build_election_payload(), headers=headers)
    assert response.status_code == 201
    return response.json


def _create_candidate(client, election_id: int, headers, nome: str = "Candidato Teste") -> dict:
    response = client.post(
        f"/api/eleicoes/{election_id}/candidatos",
        json={"nome": nome},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json


@pytest.mark.usefixtures("client")
def test_create_candidate_returns_created_candidate(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={"nome": "Alice"},
        headers=headers,
    )
    
    assert response.status_code == 201
    body = response.json
    assert body["id"] > 0
    assert body["nome"] == "Alice"
    assert body["eleicao_id"] == election["id"]
    assert body["votos_count"] == 0
    assert body["blockchain_index"] == 0
    assert "blockchain_tx" not in body


def test_create_candidate_rejects_empty_name(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={"nome": ""},
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "error" in response.json


def test_create_candidate_rejects_missing_name(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={},
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "error" in response.json


def test_create_candidate_rejects_if_election_active(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)

    response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={"nome": "Bob"},
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_create_candidate_returns_404_for_missing_election(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    response = client.post(
        "/api/eleicoes/999/candidatos",
        json={"nome": "Alice"},
        headers=headers,
    )
    
    assert response.status_code == 404


def test_list_candidates_returns_all_for_election(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    _create_candidate(client, election["id"], headers, "Alice")
    _create_candidate(client, election["id"], headers, "Bob")
    _create_candidate(client, election["id"], headers, "Charlie")

    response = client.get(f"/api/eleicoes/{election['id']}/candidatos")

    assert response.status_code == 200
    candidates = response.json
    assert len(candidates) == 3
    assert candidates[0]["nome"] == "Alice"
    assert candidates[1]["nome"] == "Bob"
    assert candidates[2]["nome"] == "Charlie"
    assert [candidate["blockchain_index"] for candidate in candidates] == [0, 1, 2]


def test_list_candidates_repairs_inconsistent_blockchain_indices(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Desalinhado")

    with client.application.app_context():
        record = db.session.get(Candidato, candidate["id"])
        record.blockchain_index = 7
        db.session.commit()

    response = client.get(f"/api/eleicoes/{election['id']}/candidatos")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload[0]["blockchain_index"] == 0


def test_ensure_candidate_indices_updates_persisted_records(client):
    with client.application.app_context():
        election = Eleicao(
            titulo="Índices",
            descricao="Verificação de coerência",
            data_inicio=_utc_now(),
            data_fim=_utc_now(),
            ativa=False,
        )
        db.session.add(election)
        db.session.flush()

        candidate = Candidato(
            nome="SemIndice",
            eleicao_id=election.id,
            blockchain_index=5,
        )
        db.session.add(candidate)
        db.session.commit()

        mapping = ensure_candidate_indices(election.id)
        assert mapping[candidate.id] == 0
        assert validate_candidate_indices(election.id) is True


def test_list_candidates_returns_empty_for_election_without_candidates(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    
    response = client.get(f"/api/eleicoes/{election['id']}/candidatos")
    
    assert response.status_code == 200
    assert response.json == []


def test_list_candidates_returns_404_for_missing_election(client):
    response = client.get("/api/eleicoes/999/candidatos")
    
    assert response.status_code == 404


def test_update_candidate_changes_name(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")

    response = client.put(
        f"/api/candidatos/{candidate['id']}",
        json={"nome": "Alice Updated"},
        headers=headers,
    )
    
    assert response.status_code == 200
    assert response.json["nome"] == "Alice Updated"
    assert response.json["id"] == candidate["id"]
    assert response.json["blockchain_index"] == 0


def test_update_candidate_accepts_empty_payload(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")

    response = client.put(f"/api/candidatos/{candidate['id']}", json={}, headers=headers)
    
    assert response.status_code == 200
    assert response.json["nome"] == "Alice"
    assert response.json["blockchain_index"] == 0


def test_update_candidate_rejects_empty_name(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")

    response = client.put(
        f"/api/candidatos/{candidate['id']}",
        json={"nome": ""},
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "error" in response.json


def test_update_candidate_rejects_if_election_active(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")
    client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)

    response = client.put(
        f"/api/candidatos/{candidate['id']}",
        json={"nome": "Alice Updated"},
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_update_candidate_returns_404_for_missing_candidate(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    response = client.put(
        "/api/candidatos/999",
        json={"nome": "Updated"},
        headers=headers,
    )
    
    assert response.status_code == 404


def test_delete_candidate_removes_resource(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")

    delete_response = client.delete(f"/api/candidatos/{candidate['id']}", headers=headers)
    assert delete_response.status_code == 204
    
    # Verify candidate is removed
    list_response = client.get(f"/api/eleicoes/{election['id']}/candidatos")
    assert list_response.status_code == 200
    assert len(list_response.json) == 0


def test_delete_candidate_rejects_if_election_active(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")
    client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)

    response = client.delete(f"/api/candidatos/{candidate['id']}", headers=headers)
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_delete_candidate_returns_404_for_missing_candidate(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    response = client.delete("/api/candidatos/999", headers=headers)
    
    assert response.status_code == 404


def test_candidates_isolated_between_elections(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election1 = _create_election(client, headers)
    election2 = _create_election(client, headers)

    _create_candidate(client, election1["id"], headers, "Alice")
    _create_candidate(client, election1["id"], headers, "Bob")
    _create_candidate(client, election2["id"], headers, "Charlie")
    
    response1 = client.get(f"/api/eleicoes/{election1['id']}/candidatos")
    response2 = client.get(f"/api/eleicoes/{election2['id']}/candidatos")
    
    assert len(response1.json) == 2
    assert len(response2.json) == 1
    assert response1.json[0]["nome"] == "Alice"
    assert response2.json[0]["nome"] == "Charlie"


def test_create_candidate_rolls_back_on_blockchain_failure(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)

    monkeypatch.setattr("services.candidate_service.is_blockchain_enabled", lambda: True)

    def failing_add_candidate(_name: str):
        raise RuntimeError("rpc unavailable")

    monkeypatch.setattr("services.candidate_service.add_candidate_onchain", failing_add_candidate)

    response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={"nome": "Alice"},
        headers=headers,
    )

    assert response.status_code == 502

    with client.application.app_context():
        assert Candidato.query.count() == 0


def test_delete_candidate_removes_associated_votes(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate = _create_candidate(client, election["id"], headers, "Alice")

    with client.application.app_context():
        vote = Voto(
            eleicao_id=election["id"],
            candidato_id=candidate["id"],
            hash_blockchain=str(uuid.uuid4()),
        )
        db.session.add(vote)
        db.session.commit()

    response = client.delete(f"/api/candidatos/{candidate['id']}", headers=headers)

    assert response.status_code == 204

    with client.application.app_context():
        assert Candidato.query.count() == 0
        assert Voto.query.count() == 0
