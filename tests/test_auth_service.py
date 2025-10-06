from services.auth_service import (
    NonceStore,
    generate_nonce_response,
    logout_response,
    verify_signature_response,
)


class DummyAccount:
    def recover_message(self, encoded_message, signature):
        return "0x0000000000000000000000000000000000000000"


class DummyEth:
    def __init__(self):
        self.account = DummyAccount()


class DummyWeb3:
    def __init__(self):
        self.eth = DummyEth()


def test_generate_nonce_response_creates_nonce():
    response = generate_nonce_response("0x1", state={})
    assert "nonce" in response.payload
    assert response.state["0x1"] == response.payload["nonce"]


def test_verify_signature_response_without_nonce_returns_error():
    response = verify_signature_response(
        address="0x0000000000000000000000000000000000000000",
        signature="0x1",
        state={},
        web3=DummyWeb3(),
    )
    assert response.status == 400
    assert response.payload["success"] is False


def test_logout_response_requires_address():
    response = logout_response("", state={})
    assert response.status == 400
    assert response.payload["success"] is False


def test_nonce_store_replace_and_snapshot():
    store = NonceStore()
    store.replace({"0x1": "nonce"})
    snapshot = store.snapshot()
    assert snapshot == {"0x1": "nonce"}
    store.clear()
    assert store.snapshot() == {}
