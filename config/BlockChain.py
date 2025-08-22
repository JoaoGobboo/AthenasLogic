from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

def connect_blockchain(provider_url: str) -> Web3:
    return Web3(Web3.HTTPProvider(provider_url))

def is_blockchain_connected(web3: Web3) -> bool:
    return web3.is_connected()

def get_latest_block(web3: Web3) -> int:
    return web3.eth.block_number

# instância funcional "singleton"
INFURA_URL = os.getenv("INFURA_URL")
web3 = connect_blockchain(INFURA_URL)