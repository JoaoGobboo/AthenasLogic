import pytest

from config import BlockChain


@pytest.mark.usefixtures("client")
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code in {200, 500}
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
