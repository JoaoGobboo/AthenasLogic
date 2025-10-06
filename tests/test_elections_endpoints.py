from datetime import datetime, timedelta

import pytest


def _build_payload(offset_days: int = 1) -> dict:
    now = datetime.utcnow()
    return {
        "titulo": "Eleicao de Teste",
        "descricao": "Eleicao para testes automatizados",
        "data_inicio": now.isoformat(),
        "data_fim": (now + timedelta(days=offset_days)).isoformat(),
    }


def _create_election(client, payload: dict | None = None) -> dict:
    response = client.post("/api/eleicoes", json=payload or _build_payload())
    assert response.status_code == 201
    return response.json


@pytest.mark.usefixtures("client")
def test_create_election_returns_created_election(client):
    response = client.post("/api/eleicoes", json=_build_payload())
    assert response.status_code == 201
    body = response.json
    assert body["id"] > 0
    assert body["ativa"] is False
    assert body["titulo"] == "Eleicao de Teste"


def test_list_elections_returns_all(client):
    _create_election(client)
    _create_election(client, _build_payload(offset_days=2))

    response = client.get("/api/eleicoes")
    assert response.status_code == 200
    assert len(response.json) == 2


def test_show_election_returns_details(client):
    election = _create_election(client)
    response = client.get(f"/api/eleicoes/{election['id']}")
    assert response.status_code == 200
    assert response.json["id"] == election["id"]


def test_update_election_changes_mutable_fields(client):
    election = _create_election(client)
    payload = {
        "titulo": "Eleicao Atualizada",
        "descricao": "Descricao alterada",
        "data_inicio": election["data_inicio"],
        "data_fim": election["data_fim"],
    }
    response = client.put(f"/api/eleicoes/{election['id']}", json=payload)
    assert response.status_code == 200
    assert response.json["titulo"] == "Eleicao Atualizada"
    assert response.json["descricao"] == "Descricao alterada"


def test_start_election_sets_active_status(client):
    election = _create_election(client)
    response = client.post(f"/api/eleicoes/{election['id']}/start")
    assert response.status_code == 200
    assert response.json["ativa"] is True
    assert response.json["data_inicio"] is not None


def test_end_election_sets_inactive_status(client):
    election = _create_election(client)
    client.post(f"/api/eleicoes/{election['id']}/start")
    response = client.post(f"/api/eleicoes/{election['id']}/end")
    assert response.status_code == 200
    assert response.json["ativa"] is False


def test_delete_election_removes_resource(client):
    election = _create_election(client)
    delete_response = client.delete(f"/api/eleicoes/{election['id']}")
    assert delete_response.status_code == 204

    fetch_response = client.get(f"/api/eleicoes/{election['id']}")
    assert fetch_response.status_code == 404


def test_create_election_rejects_invalid_dates(client):
    now = datetime.utcnow()
    payload = {
        "titulo": "Eleicao Invalida",
        "descricao": "Datas inconsistentes",
        "data_inicio": now.isoformat(),
        "data_fim": (now - timedelta(days=1)).isoformat(),
    }
    response = client.post("/api/eleicoes", json=payload)
    assert response.status_code == 400


def test_start_election_returns_404_for_missing_resource(client):
    response = client.post("/api/eleicoes/999/start")
    assert response.status_code == 404
