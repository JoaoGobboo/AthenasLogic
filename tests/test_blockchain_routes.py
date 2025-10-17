import pytest


@pytest.mark.usefixtures("client")
def test_verify_blockchain_hash_success(client, monkeypatch):
    monkeypatch.setattr(
        "routes.blockchain.verify_transaction_on_chain",
        lambda h: {
            "verified": True,
            "status": "success",
            "transactionHash": h,
            "blockNumber": 12,
            "gasUsed": 21000,
        },
    )

    response = client.get("/api/blockchain/verificar/0xabc")
    assert response.status_code == 200
    body = response.get_json()
    assert body["transactionHash"] == "0xabc"


@pytest.mark.usefixtures("client")
def test_verify_blockchain_hash_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "routes.blockchain.verify_transaction_on_chain",
        lambda h: {"verified": False, "status": "not_found", "message": "missing"},
    )

    response = client.get("/api/blockchain/verificar/0xmissing")
    assert response.status_code == 404


@pytest.mark.usefixtures("client")
def test_verify_blockchain_hash_handles_error(client, monkeypatch):
    monkeypatch.setattr(
        "routes.blockchain.verify_transaction_on_chain",
        lambda h: {"verified": False, "status": "error", "message": "bad"},
    )

    response = client.get("/api/blockchain/verificar/0xerror")
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
