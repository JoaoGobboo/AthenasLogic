from pydantic import BaseModel, validator
from web3 import Web3
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()
INFURA_URL = os.getenv("INFURA_URL")

# Conexão com a blockchain via Alchemy/Infura
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

class CheckAuthDTO(BaseModel):
    address: str
    signature: str

    @validator("address")
    def validate_address(cls, v):
        if not Web3.is_address(v):
            raise ValueError("Endereço Ethereum inválido")
        return Web3.to_checksum_address(v)

class RequestNonceDTO(BaseModel):
    address: str

    @validator("address")
    def validate_address(cls, v):
        if not Web3.is_address(v):
            raise ValueError("Endereço Ethereum inválido")
        return Web3.to_checksum_address(v)
