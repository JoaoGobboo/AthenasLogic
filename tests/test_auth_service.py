import pytest

from services.auth_service import generate_nonce_response, logout_response, verify_signature_response
from services.session_service import SessionStore


class DummyAccount:
    def recover_message(self, encoded_message, signature):  # pragma: no cover - simple stub
        return "0x0000000000000000000000000000000000000000"


class DummyEth:
    def __init__(self):
        self.account = DummyAccount()


class DummyWeb3:
    def __init__(self):
        self.eth = DummyEth()


@pytest.mark.usefixtures("client")
def test_generate_nonce_response_persists_nonce(client):
    with client.application.app_context():
        store = SessionStore()
        response = generate_nonce_response("0x1", store)
        assert "nonce" in response.payload
        assert store.peek_nonce("0x1") == response.payload["nonce"]


@pytest.mark.usefixtures("client")
def test_verify_signature_response_without_nonce_returns_error(client):
    with client.application.app_context():
        store = SessionStore()
        response = verify_signature_response(
            address="0x0000000000000000000000000000000000000000",
            signature="0x1",
            store=store,
            web3=DummyWeb3(),
        )
        assert response.status == 400
        assert response.payload["success"] is False


@pytest.mark.usefixtures("client")
def test_verify_signature_response_consumes_nonce(client):
    address = "0x0000000000000000000000000000000000000000"
    with client.application.app_context():
        store = SessionStore()
        store.save_nonce(address, "stub-nonce")
        response = verify_signature_response(
            address=address,
            signature="0x1",
            store=store,
            web3=DummyWeb3(),
        )
        assert response.status == 200
        assert response.payload["success"] is True
        assert store.peek_nonce(address) is None


@pytest.mark.usefixtures("client")
def test_logout_response_requires_address(client):
    with client.application.app_context():
        store = SessionStore()
        response = logout_response("", store)
        assert response.status == 400
        assert response.payload["success"] is False


@pytest.mark.usefixtures("client")
def test_logout_response_clears_nonce(client):
    address = "0x0000000000000000000000000000000000000000"
    with client.application.app_context():
        store = SessionStore()
        generate_nonce_response(address, store)
        response = logout_response(address, store)
        assert response.status == 200
        assert response.payload["success"] is True
        assert store.peek_nonce(address) is None
