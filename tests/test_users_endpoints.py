"""
Testes reais dos endpoints disponíveis
"""
import pytest

def test_health(client):
    print("[TESTE] Testando endpoint /health")
    resp = client.get('/health')
    assert resp.status_code in [200, 500], "Status code deve ser 200 (ok) ou 500 (erro de serviço)"
    assert 'blockchain' in resp.json, "Resposta deve conter chave 'blockchain'"
    assert 'database' in resp.json, "Resposta deve conter chave 'database'"
    assert 'service' in resp.json, "Resposta deve conter chave 'service'"

# Teste do endpoint /auth/request_nonce
# Usa um endereço Ethereum válido (pode ser qualquer string 0x... para teste)
def test_request_nonce(client):
    print("[TESTE] Testando endpoint /auth/request_nonce")
    address = "0x0000000000000000000000000000000000000000"
    resp = client.post('/auth/request_nonce', json={'address': address})
    assert resp.status_code == 200, "Status code deve ser 200 para request_nonce"
    assert 'nonce' in resp.json, "Resposta deve conter chave 'nonce'"

# Teste do endpoint /auth/logout
def test_logout(client):
    print("[TESTE] Testando endpoint /auth/logout")
    address = "0x0000000000000000000000000000000000000000"
    resp = client.post('/auth/logout', json={'address': address})
    assert resp.status_code == 200, "Status code deve ser 200 para logout"
    assert 'success' in resp.json, "Resposta deve conter chave 'success'"
