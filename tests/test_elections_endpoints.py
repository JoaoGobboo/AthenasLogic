from datetime import datetime, timedelta, timezone
import uuid

import pytest
from models import Candidato, Eleicao, Voto, db
from services.auth_service import ServiceResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _build_payload(offset_days: int = 1) -> dict:
    now = _utc_now()
    return {
        "titulo": "Eleicao de Teste",
        "descricao": "Eleicao para testes automatizados",
        "data_inicio": now.isoformat(),
        "data_fim": (now + timedelta(days=offset_days)).isoformat(),
        "candidatos": ["Alice", "Bob"],
    }


AUTH_ADDRESS = "0x00000000000000000000000000000000000000bb"


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


def _create_election(client, headers, payload: dict | None = None) -> dict:
    response = client.post("/api/eleicoes", json=payload or _build_payload(), headers=headers)
    assert response.status_code == 201
    return response.json


@pytest.mark.usefixtures("client")
def test_create_election_returns_created_election(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    response = client.post("/api/eleicoes", json=_build_payload(), headers=headers)
    assert response.status_code == 201
    body = response.json
    assert body["id"] > 0
    assert body["ativa"] is False
    assert body["titulo"] == "Eleicao de Teste"
    assert "blockchain_tx" not in body


def test_list_elections_returns_all(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    _create_election(client, headers)
    _create_election(client, headers, _build_payload(offset_days=2))

    response = client.get("/api/eleicoes")
    assert response.status_code == 200
    assert len(response.json) == 2


def test_show_election_returns_details(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    response = client.get(f"/api/eleicoes/{election['id']}")
    assert response.status_code == 200
    assert response.json["id"] == election["id"]


def test_update_election_changes_mutable_fields(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    payload = {
        "titulo": "Eleicao Atualizada",
        "descricao": "Descricao alterada",
        "data_inicio": election["data_inicio"],
        "data_fim": election["data_fim"],
    }
    response = client.put(
        f"/api/eleicoes/{election['id']}",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json["titulo"] == "Eleicao Atualizada"
    assert response.json["descricao"] == "Descricao alterada"


def test_start_election_sets_active_status(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    response = client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)
    assert response.status_code == 200
    assert response.json["ativa"] is True
    assert response.json["data_inicio"] is not None
    assert "blockchain_tx" not in response.json


def test_end_election_sets_inactive_status(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)
    response = client.post(f"/api/eleicoes/{election['id']}/end", headers=headers)
    assert response.status_code == 200
    assert response.json["ativa"] is False
    assert "blockchain_tx" not in response.json


def test_delete_election_removes_resource(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    delete_response = client.delete(f"/api/eleicoes/{election['id']}", headers=headers)
    assert delete_response.status_code == 204

    fetch_response = client.get(f"/api/eleicoes/{election['id']}")
    assert fetch_response.status_code == 404


def test_create_election_rejects_invalid_dates(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    now = _utc_now()
    payload = {
        "titulo": "Eleicao Invalida",
        "descricao": "Datas inconsistentes",
        "data_inicio": now.isoformat(),
        "data_fim": (now - timedelta(days=1)).isoformat(),
        "candidatos": ["Alice"],
    }
    response = client.post("/api/eleicoes", json=payload, headers=headers)
    assert response.status_code == 400


def test_start_election_returns_404_for_missing_resource(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    response = client.post("/api/eleicoes/999/start", headers=headers)
    assert response.status_code == 404


def test_create_election_rolls_back_on_blockchain_failure(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    monkeypatch.setattr("services.election_service.is_blockchain_enabled", lambda: True)

    def failing_configure(_name: str, _candidates: list[str]):
        raise RuntimeError("rpc unavailable")

    monkeypatch.setattr("services.election_service.configure_election_onchain", failing_configure)

    response = client.post("/api/eleicoes", json=_build_payload(), headers=headers)

    assert response.status_code == 502

    with client.application.app_context():
        assert Eleicao.query.count() == 0


def test_update_election_rejects_start_after_existing_end(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    future_start = (datetime.fromisoformat(election["data_fim"]) + timedelta(days=1)).isoformat()

    response = client.put(
        f"/api/eleicoes/{election['id']}",
        json={"data_inicio": future_start},
        headers=headers,
    )

    assert response.status_code == 400


def test_delete_election_removes_candidates_and_votes(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)
    candidate_response = client.post(
        f"/api/eleicoes/{election['id']}/candidatos",
        json={"nome": "Alice"},
        headers=headers,
    )
    assert candidate_response.status_code == 201
    candidate = candidate_response.json

    with client.application.app_context():
        vote = Voto(
            eleicao_id=election["id"],
            candidato_id=candidate["id"],
            hash_blockchain=str(uuid.uuid4()),
        )
        db.session.add(vote)
        db.session.commit()

    response = client.delete(f"/api/eleicoes/{election['id']}", headers=headers)

    assert response.status_code == 204

    with client.application.app_context():
        assert Eleicao.query.count() == 0
        assert Candidato.query.count() == 0
        assert Voto.query.count() == 0


def test_start_election_rejects_when_end_date_in_past(client, monkeypatch):
    headers = _auth_headers(client, monkeypatch)
    election = _create_election(client, headers)

    with client.application.app_context():
        record = db.session.get(Eleicao, election["id"])
        record.data_fim = _utc_now() - timedelta(days=1)
        db.session.commit()

    response = client.post(f"/api/eleicoes/{election['id']}/start", headers=headers)

    assert response.status_code == 400
