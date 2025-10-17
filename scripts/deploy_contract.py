#!/usr/bin/env python
"""Implanta o contrato AthenaElection em uma testnet Ethereum."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractCustomError

ARTIFACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "AthenaElection.json"


def _load_artifact() -> dict:
    if not ARTIFACT_PATH.exists():
        print(f"Artifact not found at {ARTIFACT_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def _load_provider() -> str:
    provider_url = os.getenv("WEB3_PROVIDER_URI") or os.getenv("INFURA_URL")
    if not provider_url:
        print("Set WEB3_PROVIDER_URI or INFURA_URL in your environment before running this script.", file=sys.stderr)
        sys.exit(1)
    return provider_url


def _load_private_key() -> str:
    private_key = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("CONTRACT_OWNER_PRIVATE_KEY")
    if not private_key:
        print("Set DEPLOYER_PRIVATE_KEY (or reuse CONTRACT_OWNER_PRIVATE_KEY) in your environment.", file=sys.stderr)
        sys.exit(1)
    return private_key


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy AthenaElection contract to a testnet")
    parser.add_argument("--name", dest="name", default="Eleicao API", help="Nome inicial da eleição")
    parser.add_argument(
        "--candidates",
        dest="candidates",
        nargs="*",
        default=["Alice", "Bob"],
        help="Lista de candidatos iniciais",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Não aguarda o mining, apenas exibe o hash da transação",
    )
    return parser.parse_args()


def _normalize_candidates(candidates: Sequence[str]) -> list[str]:
    return [candidate.strip() for candidate in candidates if candidate and candidate.strip()]


def main() -> None:
    load_dotenv()
    args = _parse_args()

    artifact = _load_artifact()
    abi = artifact.get("abi")
    bytecode = artifact.get("data", {}).get("bytecode", {}).get("object")
    if not abi or not bytecode:
        print("Invalid contract artifact. Ensure AthenaElection.json contains ABI and bytecode.", file=sys.stderr)
        sys.exit(1)

    provider_url = _load_provider()
    private_key = _load_private_key()

    web3 = Web3(Web3.HTTPProvider(provider_url))
    if not web3.is_connected():
        print(f"Failed to connect to provider {provider_url}", file=sys.stderr)
        sys.exit(1)

    account = web3.eth.account.from_key(private_key)
    print(f"Using deployer address: {account.address}")

    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    candidates = _normalize_candidates(args.candidates)

    constructor = contract.constructor(args.name, candidates)
    nonce = web3.eth.get_transaction_count(account.address)
    gas_estimate = constructor.estimate_gas({"from": account.address})
    max_priority = web3.to_wei("1", "gwei")
    base_fee = web3.eth.gas_price

    txn = constructor.build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "maxFeePerGas": base_fee + max_priority,
            "maxPriorityFeePerGas": max_priority,
            "chainId": web3.eth.chain_id,
        }
    )

    signed_txn = account.sign_transaction(txn)
    # web3>=7 renames rawTransaction -> raw_transaction; keep compatibility with both
    if hasattr(signed_txn, "raw_transaction"):
        raw_tx = signed_txn.raw_transaction
    else:  # pragma: no cover - compatibility with older web3
        raw_tx = signed_txn.rawTransaction
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    print(f"Deployment transaction sent: {tx_hash.hex()}")

    if args.no_wait:
        return

    print("Waiting for transaction receipt...")
    try:
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    except ContractCustomError as exc:  # pragma: no cover - defensive guard
        print(f"Contract reverted: {exc}", file=sys.stderr)
        sys.exit(1)

    if receipt.status != 1:
        print(f"Deployment failed. Receipt: {receipt}", file=sys.stderr)
        sys.exit(1)

    print("Contract deployed successfully!")
    print(f"Address: {receipt.contractAddress}")
    print("Save this address in your .env as CONTRACT_ADDRESS and reuse the private key as CONTRACT_OWNER_PRIVATE_KEY.")


if __name__ == "__main__":
    main()
