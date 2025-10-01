from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Callable, Mapping

from eth_account.messages import encode_defunct
from web3 import Web3

NonceState = Mapping[str, str]


@dataclass(frozen=True)
class ServiceResponse:
    payload: dict
    state: dict[str, str]
    status: int = 200


def _clone_state(state: NonceState) -> dict[str, str]:
    return dict(state) if state else {}


def default_nonce_factory(length: int = 16, alphabet: str = string.ascii_letters + string.digits) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_nonce_response(
    address: str,
    state: NonceState,
    nonce_factory: Callable[[], str] | None = None,
) -> ServiceResponse:
    factory = nonce_factory or default_nonce_factory
    nonce = factory()
    new_state = _clone_state(state)
    new_state[address] = nonce
    return ServiceResponse(payload={"nonce": nonce}, state=new_state)


def verify_signature_response(
    address: str,
    signature: str,
    state: NonceState,
    web3: Web3,
) -> ServiceResponse:
    message = state.get(address) if state else None
    if not message:
        return ServiceResponse(
            payload={"success": False, "error": "No nonce found for this address"},
            state=_clone_state(state),
            status=400,
        )

    try:
        encoded_message = encode_defunct(text=message)
        recovered_address = web3.eth.account.recover_message(encoded_message, signature=signature)
    except Exception as exc:
        return ServiceResponse(
            payload={"success": False, "error": str(exc)},
            state=_clone_state(state),
            status=400,
        )

    expected_address = Web3.to_checksum_address(address)
    resolved_address = Web3.to_checksum_address(recovered_address)
    if resolved_address != expected_address:
        return ServiceResponse(
            payload={"success": False, "error": "Invalid signature"},
            state=_clone_state(state),
            status=401,
        )

    new_state = _clone_state(state)
    new_state.pop(address, None)
    return ServiceResponse(
        payload={"success": True, "address": expected_address},
        state=new_state,
    )


def logout_response(address: str, state: NonceState) -> ServiceResponse:
    if not address:
        return ServiceResponse(
            payload={"success": False, "error": "Address is required"},
            state=_clone_state(state),
            status=400,
        )

    new_state = _clone_state(state)
    new_state.pop(address, None)
    return ServiceResponse(
        payload={"success": True, "message": "Logged out successfully"},
        state=new_state,
    )
