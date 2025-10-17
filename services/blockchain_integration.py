from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt

from config.BlockChain import get_web3

_CONTRACT_ADDRESS_ENV = "CONTRACT_ADDRESS"
_PRIVATE_KEY_ENV = "CONTRACT_OWNER_PRIVATE_KEY"
_ABI_PATH_ENV = "CONTRACT_ABI_PATH"
_DEFAULT_ARTIFACT = Path(__file__).resolve().parents[1] / "contracts" / "AthenaElection.json"


@dataclass(frozen=True)
class BlockchainConfig:
    address: str
    private_key: str
    abi: list[dict]


def _load_artifact() -> dict:
    artifact_path = os.getenv(_ABI_PATH_ENV)
    if artifact_path:
        path = Path(artifact_path)
    else:
        path = _DEFAULT_ARTIFACT
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard.
        raise RuntimeError(f"Contract artifact not found at {path}") from exc


def _load_config() -> Optional[BlockchainConfig]:
    address = os.getenv(_CONTRACT_ADDRESS_ENV)
    private_key = os.getenv(_PRIVATE_KEY_ENV)
    if not address or not private_key:
        return None

    artifact = _load_artifact()
    abi = artifact.get("abi")
    if not abi:
        raise RuntimeError("Contract ABI not found in artifact")

    try:
        checksum_address = Web3.to_checksum_address(address)
    except (TypeError, ValueError) as exc:
        logging.warning(
            "Invalid CONTRACT_ADDRESS provided; disabling blockchain features. error=%s",
            exc,
        )
        return None
    return BlockchainConfig(address=checksum_address, private_key=private_key, abi=abi)


def is_blockchain_enabled() -> bool:
    return _load_config() is not None


def _get_contract_and_account() -> tuple[Web3, Contract, str]:
    config = _load_config()
    if config is None:
        raise RuntimeError("Blockchain contract is not configured. Set CONTRACT_ADDRESS and CONTRACT_OWNER_PRIVATE_KEY.")

    web3 = get_web3()
    contract = web3.eth.contract(address=config.address, abi=config.abi)
    account = web3.eth.account.from_key(config.private_key)
    return web3, contract, account


def _send_transaction(transaction_builder) -> TxReceipt:
    web3, contract, account = _get_contract_and_account()

    function = transaction_builder(contract)
    nonce = web3.eth.get_transaction_count(account.address)

    try:
        estimated_gas = function.estimate_gas({"from": account.address})
    except Exception as exc:  # pragma: no cover - propagated to caller
        logging.error("Failed to estimate gas for contract transaction: %s", exc)
        raise

    max_priority = web3.to_wei("1", "gwei")
    base_fee = web3.eth.gas_price
    tx = function.build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gas": int(estimated_gas * 1.2),
            "maxFeePerGas": base_fee + max_priority,
            "maxPriorityFeePerGas": max_priority,
            "chainId": web3.eth.chain_id,
        }
    )

    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    logging.info("Blockchain transaction mined: %s", tx_hash.hex())
    return receipt


def configure_election_onchain(name: str, candidates: Optional[Iterable[str]] = None) -> Optional[TxReceipt]:
    if not is_blockchain_enabled():
        return None

    candidate_list = list(candidates or [])

    def builder(contract: Contract):
        return contract.functions.configureElection(name, candidate_list)

    return _send_transaction(builder)


def open_election_onchain() -> Optional[TxReceipt]:
    if not is_blockchain_enabled():
        return None

    def builder(contract: Contract):
        return contract.functions.openElection()

    return _send_transaction(builder)


def close_election_onchain() -> Optional[TxReceipt]:
    if not is_blockchain_enabled():
        return None

    def builder(contract: Contract):
        return contract.functions.closeElection()

    return _send_transaction(builder)

def record_vote_onchain(candidate_index: int) -> Optional[TxReceipt]:
    if not is_blockchain_enabled():
        return None

    def builder(contract: Contract):
        return contract.functions.vote(int(candidate_index))

    return _send_transaction(builder)


def add_candidate_onchain(name: str) -> Optional[TxReceipt]:
    if not is_blockchain_enabled():
        return None

    def builder(contract: Contract):
        return contract.functions.addCandidate(name)

    return _send_transaction(builder)


def verify_transaction_on_chain(tx_hash: str) -> dict:
    """Consulta o status de uma transacao na blockchain."""
    if not is_blockchain_enabled():
        return {"verified": False, "status": "error", "message": "Blockchain nao esta configurada."}

    try:
        web3 = get_web3()
        receipt = web3.eth.get_transaction_receipt(tx_hash)

        if receipt:
            return {
                "verified": True,
                "status": "success" if receipt.get("status") == 1 else "failed",
                "blockNumber": receipt.get("blockNumber"),
                "gasUsed": receipt.get("gasUsed"),
                "transactionHash": web3.to_hex(receipt.get("transactionHash")),
            }
        return {"verified": False, "status": "not_found", "message": "Transacao nao encontrada ou pendente."}

    except Exception as exc:  # pragma: no cover - defensive fallback
        logging.error("Erro ao verificar hash '%s' na blockchain: %s", tx_hash, exc)
        return {"verified": False, "status": "error", "message": f"Erro ao processar o hash: {exc}"}
