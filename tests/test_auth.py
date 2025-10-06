import pytest
from pydantic import ValidationError
from web3 import Web3

from dtos.auth_dto import CheckAuthDTO, RequestNonceDTO


def test_request_nonce_dto_normalizes_address():
    dto = RequestNonceDTO(address="0x0000000000000000000000000000000000000000")
    assert dto.address == Web3.to_checksum_address("0x0000000000000000000000000000000000000000")


def test_check_auth_dto_normalizes_address():
    dto = CheckAuthDTO(address="0x0000000000000000000000000000000000000000", signature="0x123")
    assert dto.address == Web3.to_checksum_address("0x0000000000000000000000000000000000000000")


def test_request_nonce_dto_invalid_address():
    with pytest.raises(ValidationError):
        RequestNonceDTO(address="invalid_address")


def test_check_auth_dto_invalid_address():
    with pytest.raises(ValidationError):
        CheckAuthDTO(address="invalid_address", signature="0x123")
