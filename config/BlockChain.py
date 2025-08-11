from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

class Blockchain:
    def __init__(self, provider_url):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))

    def is_connected(self):
        return self.web3.is_connected()

    def get_latest_block(self):
        return self.web3.eth.block_number

# Instância singleton pronta para uso
infura_url = os.getenv('INFURA_URL')
blockchain = Blockchain(infura_url)