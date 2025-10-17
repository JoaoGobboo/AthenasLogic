import pytest

from config import BlockChain
from services.auth_service import ServiceResponse




@pytest.mark.usefixtures("client")
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code in {200, 503}
    assert set(response.json.keys()) == {"blockchain", "database", "service"}


def test_request_nonce_endpoint_returns_nonce(client):
    address = "0x0000000000000000000000000000000000000000"
    response = client.post("/auth/request_nonce", json={"address": address})
    assert response.status_code == 200
    assert "nonce" in response.json


def test_verify_without_blockchain_provider_returns_503(client, monkeypatch):
    BlockChain.get_web3.cache_clear()
    monkeypatch.setenv("INFURA_URL", "")
    monkeypatch.setenv("WEB3_PROVIDER_URI", "")
    response = client.post(
        "/auth/verify",
        json={"address": "0x0000000000000000000000000000000000000000", "signature": "0x1"},
    )
    assert response.status_code == 503
    assert "error" in response.json


def test_logout_requires_address(client):
    response = client.post("/auth/logout", json={})
    assert response.status_code == 400
    assert response.json["success"] is False


def test_logout_succeeds_after_request_nonce(client):
    address = "0x0000000000000000000000000000000000000000"
    client.post("/auth/request_nonce", json={"address": address})
    response = client.post("/auth/logout", json={"address": address})
    assert response.status_code == 200
    assert response.json["success"] is True


def test_swagger_ui_available(client):
    response = client.get("/apidocs/")
    assert response.status_code == 200
    assert b"swagger" in response.data.lower()


def test_openapi_spec_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["info"]["title"] == "Athenas Logic API"

ADDRESS = "0x0000000000000000000000000000000000000001"


def _mock_successful_signature(monkeypatch):
    def fake_get_web3():
        return object()

    def fake_verify_signature_response(address, signature, store, web3):
        return ServiceResponse(payload={"success": True, "address": address}, status=200)

    monkeypatch.setattr("routes.auth.get_web3", fake_get_web3)
    monkeypatch.setattr("routes.auth.verify_signature_response", fake_verify_signature_response)


def _perform_login(client, monkeypatch):
    _mock_successful_signature(monkeypatch)
    response = client.post("/api/auth/login", json={"address": ADDRESS, "signature": "0xsignature"})
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("token")
    assert body.get("csrf_token")
    return body


def test_login_creates_session_and_returns_user(client, monkeypatch):
    body = _perform_login(client, monkeypatch)
    user = body["user"]
    assert user["endereco_wallet"].lower() == ADDRESS.lower()
    assert isinstance(user["id"], int)


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_user_for_valid_session(client, monkeypatch):
    body = _perform_login(client, monkeypatch)
    token = body["token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["id"] == body["user"]["id"]


def test_logout_session_revokes_token(client, monkeypatch):
    body = _perform_login(client, monkeypatch)
    token = body["token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": body["csrf_token"],
    }
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    me_again = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_again.status_code == 401


def test_update_profile_requires_token(client):
    response = client.put("/api/users/profile", json={"nome": "Alice"})
    assert response.status_code == 401


def test_update_profile_persists_changes(client, monkeypatch):
    body = _perform_login(client, monkeypatch)
    token = body["token"]
    payload = {"nome": "Alice", "email": "alice@example.com", "bio": "Entusiasta de blockchain"}
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": body["csrf_token"],
    }
    response = client.put("/api/users/profile", json=payload, headers=headers)
    assert response.status_code == 200
    updated = response.get_json()
    assert updated["nome"] == payload["nome"]
    assert updated["email"] == payload["email"]
    assert updated["bio"] == payload["bio"]
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.get_json()["nome"] == payload["nome"]
