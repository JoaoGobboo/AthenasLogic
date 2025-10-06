from pydantic import BaseModel, field_validator
from web3 import Web3


class CheckAuthDTO(BaseModel):
    address: str
    signature: str

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        if not Web3.is_address(value):
            raise ValueError("Invalid Ethereum address")
        return Web3.to_checksum_address(value)


class RequestNonceDTO(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        if not Web3.is_address(value):
            raise ValueError("Invalid Ethereum address")
        return Web3.to_checksum_address(value)
