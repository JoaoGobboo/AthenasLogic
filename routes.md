# Guia de Rotas da Athenas Logic API

Este documento resume todos os endpoints expostos pela API, requisitos de autenticação, fluxos comuns e exemplos `curl`.

## Convenções Gerais
- Base URL local: `http://localhost:5000`
- Autenticação:
  - Endpoints públicos: `/health`, `/auth/request_nonce`, `/auth/verify`, `/auth/logout` (legado), `/api/votos/<hash>/verificar`, `/api/blockchain/verificar/<hash>`
  - Endpoints protegidos: exigem `Authorization: Bearer <token>` e, para métodos mutáveis (`POST`, `PUT`, `DELETE`), também `X-CSRF-Token: <csrf_token>` obtido no login.
- Respostas de erro seguem o formato `{ "error": "..." }` ou `{ "description": "..." }` conforme origem.

## Fluxo de Autenticação via Carteira
1. Solicitar nonce (`POST /auth/request_nonce`)
2. Assinar o nonce off-chain
3. Validar assinatura (`POST /auth/verify`)
4. Criar sessão (`POST /api/auth/login`)
5. Consumir endpoints protegidos com Bearer + CSRF
6. Finalizar sessão (`POST /api/auth/logout`)

```bash
# 1) Solicitar nonce
token_address="0xSEU_ENDERECO"
curl -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"address\": \"${token_address}\"}" \
  http://localhost:5000/auth/request_nonce

# 2) Assine o nonce retornado na carteira (fora da API)
# 3) Validar assinatura
token_signature="0xASSINATURA"
curl -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"address\": \"${token_address}\", \"signature\": \"${token_signature}\"}" \
  http://localhost:5000/auth/verify

# 4) Criar sessão e receber token + csrf_token
curl -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"address\": \"${token_address}\", \"signature\": \"${token_signature}\"}" \
  http://localhost:5000/api/auth/login

# Salve as variáveis
API_TOKEN="<token>"
CSRF_TOKEN="<csrf_token>"
```

### Sessão e Perfil
```bash
# Obter usuário autenticado
curl -H "Authorization: Bearer ${API_TOKEN}" \
  http://localhost:5000/api/auth/me

# Encerrar sessão
curl -X POST \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://localhost:5000/api/auth/logout

# Atualizar perfil
curl -X PUT \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"nome": "Alice", "email": "alice@example.com", "bio": "Entusiasta"}' \
  http://localhost:5000/api/users/profile
```

## Saúde do Serviço
```bash
curl http://localhost:5000/health
```

## Gestão de Eleições (`/api/eleicoes`)
Endpoints mutáveis requerem Bearer + CSRF.

```bash
# Criar eleição
curl -X POST \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{
        "titulo": "Eleicao Conselho",
        "descricao": "Mandato 2026",
        "data_inicio": "2026-01-10T09:00:00Z",
        "data_fim": "2026-01-20T18:00:00Z",
        "candidatos": ["Alice", "Bob"]
      }' \
  http://localhost:5000/api/eleicoes

# Listar eleições
curl http://localhost:5000/api/eleicoes

# Detalhar eleição
ELEICAO_ID=1
curl http://localhost:5000/api/eleicoes/${ELEICAO_ID}

# Atualizar eleição
curl -X PUT \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"descricao": "Atualizado"}' \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}

# Iniciar/encerrar eleição
curl -X POST \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}/start

curl -X POST \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}/end

# Excluir eleição (requer blockchain desabilitado e eleição inativa)
curl -X DELETE \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}

# Resultados e status
curl http://localhost:5000/api/eleicoes/${ELEICAO_ID}/resultados
curl http://localhost:5000/api/eleicoes/${ELEICAO_ID}/status
```

## Candidatos (`/api/eleicoes/{id}/candidatos` e `/api/candidatos/{id}`)
```bash
# Criar candidato
curl -X POST \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"nome": "Alice"}' \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}/candidatos

# Listar candidatos
curl http://localhost:5000/api/eleicoes/${ELEICAO_ID}/candidatos

# Atualizar candidato
CANDIDATO_ID=1
curl -X PUT \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"nome": "Alice Atualizada"}' \
  http://localhost:5000/api/candidatos/${CANDIDATO_ID}

# Remover candidato
curl -X DELETE \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  http://localhost:5000/api/candidatos/${CANDIDATO_ID}
```

## Votação (`/api/eleicoes/{id}/votar`)
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -d '{"candidato_id": 1, "hash_blockchain": "0xABC123"}' \
  http://localhost:5000/api/eleicoes/${ELEICAO_ID}/votar
```

### Consulta de votos e blockchain
```bash
# Verificar transação registrada na API
curl http://localhost:5000/api/votos/0xABC123/verificar

# Verificar transação diretamente na blockchain (se configurada)
curl http://localhost:5000/api/blockchain/verificar/0xABC123
```

## Auditoria (`/api/audit`)
Requer Bearer (leitura não precisa de CSRF).
```bash
# Todos os logs
curl -H "Authorization: Bearer ${API_TOKEN}" \
  http://localhost:5000/api/audit/logs

# Logs por eleição
curl -H "Authorization: Bearer ${API_TOKEN}" \
  http://localhost:5000/api/audit/eleicoes/${ELEICAO_ID}
```

## Logout de Nonce (legado)
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"address\": \"${token_address}\"}" \
  http://localhost:5000/auth/logout
```

---
Para rodar migrações estruturais (tabela de sessões e coluna `eleicao_id`), execute:
```bash
PYTHONPATH=. SQLALCHEMY_DATABASE_URI="<sua-uri>" python scripts/run_migrations.py
```
