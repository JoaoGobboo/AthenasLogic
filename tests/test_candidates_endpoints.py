from datetime import datetime, timedelta

import pytest


def _build_election_payload(offset_days: int = 1) -> dict:
    now = datetime.utcnow()
    return {
        "titulo": "Eleicao de Teste",
        "descricao": "Eleicao para testes automatizados",
        "data_inicio": now.isoformat(),
        "data_fim": (now + timedelta(days=offset_days)).isoformat(),
    }


def _create_election(client) -> dict:
    response = client.post("/api/eleicoes", json=_build_election_payload())
    assert response.status_code == 201
    return response.json


def _create_candidate(client, election_id: int, nome: str = "Candidato Teste") -> dict:
    response = client.post(f"/api/eleicoes/{election_id}/candidatos", json={"nome": nome})
    assert response.status_code == 201
    return response.json


@pytest.mark.usefixtures("client")
def test_create_candidate_returns_created_candidate(client):
    election = _create_election(client)
    response = client.post(f"/api/eleicoes/{election['id']}/candidatos", json={"nome": "Alice"})
    
    assert response.status_code == 201
    body = response.json
    assert body["id"] > 0
    assert body["nome"] == "Alice"
    assert body["eleicao_id"] == election["id"]
    assert body["votos_count"] == 0
    assert "blockchain_tx" not in body


def test_create_candidate_rejects_empty_name(client):
    election = _create_election(client)
    response = client.post(f"/api/eleicoes/{election['id']}/candidatos", json={"nome": ""})
    
    assert response.status_code == 400
    assert "error" in response.json


def test_create_candidate_rejects_missing_name(client):
    election = _create_election(client)
    response = client.post(f"/api/eleicoes/{election['id']}/candidatos", json={})
    
    assert response.status_code == 400
    assert "error" in response.json


def test_create_candidate_rejects_if_election_active(client):
    election = _create_election(client)
    client.post(f"/api/eleicoes/{election['id']}/start")
    
    response = client.post(f"/api/eleicoes/{election['id']}/candidatos", json={"nome": "Bob"})
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_create_candidate_returns_404_for_missing_election(client):
    response = client.post("/api/eleicoes/999/candidatos", json={"nome": "Alice"})
    
    assert response.status_code == 404


def test_list_candidates_returns_all_for_election(client):
    election = _create_election(client)
    _create_candidate(client, election["id"], "Alice")
    _create_candidate(client, election["id"], "Bob")
    _create_candidate(client, election["id"], "Charlie")
    
    response = client.get(f"/api/eleicoes/{election['id']}/candidatos")
    
    assert response.status_code == 200
    candidates = response.json
    assert len(candidates) == 3
    assert candidates[0]["nome"] == "Alice"
    assert candidates[1]["nome"] == "Bob"
    assert candidates[2]["nome"] == "Charlie"


def test_list_candidates_returns_empty_for_election_without_candidates(client):
    election = _create_election(client)
    
    response = client.get(f"/api/eleicoes/{election['id']}/candidatos")
    
    assert response.status_code == 200
    assert response.json == []


def test_list_candidates_returns_404_for_missing_election(client):
    response = client.get("/api/eleicoes/999/candidatos")
    
    assert response.status_code == 404


def test_update_candidate_changes_name(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    
    response = client.put(f"/api/candidatos/{candidate['id']}", json={"nome": "Alice Updated"})
    
    assert response.status_code == 200
    assert response.json["nome"] == "Alice Updated"
    assert response.json["id"] == candidate["id"]


def test_update_candidate_accepts_empty_payload(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    
    response = client.put(f"/api/candidatos/{candidate['id']}", json={})
    
    assert response.status_code == 200
    assert response.json["nome"] == "Alice"


def test_update_candidate_rejects_empty_name(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    
    response = client.put(f"/api/candidatos/{candidate['id']}", json={"nome": ""})
    
    assert response.status_code == 400
    assert "error" in response.json


def test_update_candidate_rejects_if_election_active(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    client.post(f"/api/eleicoes/{election['id']}/start")
    
    response = client.put(f"/api/candidatos/{candidate['id']}", json={"nome": "Alice Updated"})
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_update_candidate_returns_404_for_missing_candidate(client):
    response = client.put("/api/candidatos/999", json={"nome": "Updated"})
    
    assert response.status_code == 404


def test_delete_candidate_removes_resource(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    
    delete_response = client.delete(f"/api/candidatos/{candidate['id']}")
    assert delete_response.status_code == 204
    
    # Verify candidate is removed
    list_response = client.get(f"/api/eleicoes/{election['id']}/candidatos")
    assert list_response.status_code == 200
    assert len(list_response.json) == 0


def test_delete_candidate_rejects_if_election_active(client):
    election = _create_election(client)
    candidate = _create_candidate(client, election["id"], "Alice")
    client.post(f"/api/eleicoes/{election['id']}/start")
    
    response = client.delete(f"/api/candidatos/{candidate['id']}")
    
    assert response.status_code == 400
    assert "active election" in response.json["description"].lower()


def test_delete_candidate_returns_404_for_missing_candidate(client):
    response = client.delete("/api/candidatos/999")
    
    assert response.status_code == 404


def test_candidates_isolated_between_elections(client):
    election1 = _create_election(client)
    election2 = _create_election(client)
    
    _create_candidate(client, election1["id"], "Alice")
    _create_candidate(client, election1["id"], "Bob")
    _create_candidate(client, election2["id"], "Charlie")
    
    response1 = client.get(f"/api/eleicoes/{election1['id']}/candidatos")
    response2 = client.get(f"/api/eleicoes/{election2['id']}/candidatos")
    
    assert len(response1.json) == 2
    assert len(response2.json) == 1
    assert response1.json[0]["nome"] == "Alice"
    assert response2.json[0]["nome"] == "Charlie"
