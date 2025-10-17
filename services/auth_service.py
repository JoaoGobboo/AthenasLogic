from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Callable

from eth_account.messages import encode_defunct
from web3 import Web3

@dataclass(frozen=True)
class ServiceResponse:
    payload: dict
    status: int = 200


def default_nonce_factory(length: int = 16, alphabet: str = string.ascii_letters + string.digits) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_nonce_response(
    address: str,
    store,
    nonce_factory: Callable[[], str] | None = None,
) -> ServiceResponse:
    factory = nonce_factory or default_nonce_factory
    nonce = factory()
    store.save_nonce(address, nonce)
    return ServiceResponse(payload={"nonce": nonce})


def verify_signature_response(
    address: str,
    signature: str,
    store,
    web3: Web3,
) -> ServiceResponse:
    message = store.peek_nonce(address)
    if not message:
        return ServiceResponse(
            payload={"success": False, "error": "No nonce found for this address"},
            status=400,
        )

    try:
        encoded_message = encode_defunct(text=message)
        recovered_address = web3.eth.account.recover_message(encoded_message, signature=signature)
    except Exception as exc:
        return ServiceResponse(
            payload={"success": False, "error": str(exc)},
            status=400,
        )

    expected_address = Web3.to_checksum_address(address)
    resolved_address = Web3.to_checksum_address(recovered_address)
    if resolved_address != expected_address:
        return ServiceResponse(
            payload={"success": False, "error": "Invalid signature"},
            status=401,
        )

    store.pop_nonce(address)
    return ServiceResponse(
        payload={"success": True, "address": expected_address},
    )


def logout_response(address: str, store) -> ServiceResponse:
    if not address:
        return ServiceResponse(
            payload={"success": False, "error": "Address is required"},
            status=400,
        )
    store.pop_nonce(address)
    return ServiceResponse(
        payload={"success": True, "message": "Logged out successfully"},
    )
