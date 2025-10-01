from functools import lru_cache
import os

from dotenv import load_dotenv
from web3 import Web3


def connect_blockchain(provider_url: str) -> Web3:
    """Create a Web3 instance for the given provider URL."""
    return Web3(Web3.HTTPProvider(provider_url))


def is_blockchain_connected(web3: Web3) -> bool:
    return web3.is_connected()


def get_latest_block(web3: Web3) -> int:
    return web3.eth.block_number


def resolve_provider_url(provider_url: str | None = None) -> str:
    load_dotenv()
    resolved = provider_url or os.getenv("INFURA_URL")
    if not resolved:
        raise RuntimeError("INFURA_URL is not configured")
    return resolved


@lru_cache(maxsize=1)
def get_web3(provider_url: str | None = None) -> Web3:
    resolved_url = resolve_provider_url(provider_url)
    return connect_blockchain(resolved_url)
