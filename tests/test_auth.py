"""
Testes reais dos DTOs de autenticação (Pydantic)
"""
import pytest
from dtos.auth_dto import RequestNonceDTO, CheckAuthDTO

def test_request_nonce_dto_valid():
    print("[TESTE] Validando DTO RequestNonceDTO com endereço válido")
    dto = RequestNonceDTO(address="0x0000000000000000000000000000000000000000")
    assert dto.address.startswith("0x"), "O endereço retornado deve começar com 0x"

def test_check_auth_dto_valid():
    print("[TESTE] Validando DTO CheckAuthDTO com dados válidos")
    dto = CheckAuthDTO(address="0x0000000000000000000000000000000000000000", signature="0x123")
    assert dto.address.startswith("0x"), "O endereço retornado deve começar com 0x"
    assert isinstance(dto.signature, str), "A assinatura deve ser uma string"

import pytest
from pydantic import ValidationError

def test_request_nonce_dto_invalid():
    print("[TESTE] Validando DTO RequestNonceDTO com endereço inválido (espera-se erro)")
    with pytest.raises(ValidationError):
        RequestNonceDTO(address="invalid_address")
