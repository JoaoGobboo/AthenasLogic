import pytest


@pytest.mark.usefixtures("client")
def test_health_endpoint_returns_200_when_blockchain_not_configured(client, monkeypatch):
    def _missing_provider():  # pragma: no cover - path under test
        raise RuntimeError("No blockchain provider configured. Set INFURA_URL or WEB3_PROVIDER_URI.")

    monkeypatch.setattr("routes.health.get_web3", _missing_provider)
    monkeypatch.setattr("routes.health.get_db_config", lambda: {})
    monkeypatch.setattr("routes.health.is_db_config_complete", lambda cfg: False)
    monkeypatch.setattr("services.health_service.time.sleep", lambda _delay: None)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["blockchain"]["status"] == "not_configured"
    assert body["database"]["status"] == "not_configured"


@pytest.mark.usefixtures("client")
def test_healthz_returns_503_when_dependencies_unavailable(client, monkeypatch):
    monkeypatch.setattr("routes.health.get_web3", lambda: object())
    monkeypatch.setattr("routes.health.is_blockchain_connected", lambda _web3: False)
    monkeypatch.setattr("routes.health.get_latest_block", lambda _web3: 0)
    monkeypatch.setattr(
        "routes.health.get_db_config",
        lambda: {"host": "db", "user": "u", "password": "p", "database": "d"},
    )
    monkeypatch.setattr("routes.health.is_db_config_complete", lambda cfg: True)
    monkeypatch.setattr("routes.health.check_db_connection", lambda cfg: False)
    monkeypatch.setattr("services.health_service.time.sleep", lambda _delay: None)

    response = client.get("/healthz")
    assert response.status_code == 503
    body = response.get_json()
    assert body["database"]["status"] == "unhealthy"
    assert body["blockchain"]["status"] == "unhealthy"
