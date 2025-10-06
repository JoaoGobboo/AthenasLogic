# Athenas Logic API

API Flask para autenticação via blockchain e operações eleitorais. O serviço expõe rotas de saúde e autenticação, integra com MySQL e Web3 e inclui suíte de testes com Pytest.

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Conta em provedor Ethereum (Infura, Alchemy, Ankr...) para acessar uma testnet

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz com, no mínimo:

```env
# Blockchain
INFURA_URL=https://sepolia.infura.io/v3/<SUA_CHAVE>
# Opcional: URL direta se não quiser usar INFURA_URL
WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/<SUA_CHAVE>
# Após o deploy, preencha com o endereço do contrato e a chave privada do owner
CONTRACT_ADDRESS=0x...
CONTRACT_OWNER_PRIVATE_KEY=0x...

# Banco de dados MySQL
DB_HOST=db
DB_PORT=3306
DB_NAME=athenas
DB_USER=usuario
DB_PASSWORD=senha123
```

> Atenção: nunca compartilhe a chave privada real da sua carteira. Utilize uma conta exclusiva para testes.

## Guia Rápido

### Ambiente Local

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest
python app.py
```

A aplicação ficará acessível em `http://localhost:5000`.

### Docker Compose

1. Garanta que o `.env` esteja configurado.
2. Construa e suba a stack:

   ```bash
   docker compose up --build
   ```

   Use `-d` para executar em background (`docker compose up --build -d`).

3. Rodar comandos isolados (ex.: testes) sem manter o container ativo:

   ```bash
   docker compose run --rm app python -m pytest
   ```

4. Parar tudo e remover containers:

   ```bash
   docker compose down
   ```

5. Limpeza completa (remove volumes do MySQL):

   ```bash
   docker compose down -v
   ```

6. Executar comandos dentro de containers já em execução:

   ```bash
   docker compose exec app python -m pytest
   ```

## Deploy do Contrato AthenaElection

1. Configure o `.env` com `INFURA_URL` (ou `WEB3_PROVIDER_URI`).
2. Gere/funde uma carteira de teste e exporte a chave privada para `DEPLOYER_PRIVATE_KEY`.
3. Rode o script de deploy:

   ```bash
   python scripts/deploy_contract.py --name "Eleicao API" --candidates Alice Bob
   ```

   O script usa o artifact `contracts/AthenaElection.json`, envia a transação e mostra o endereço implantado.
4. Salve o endereço retornado em `CONTRACT_ADDRESS` e reutilize a mesma chave como `CONTRACT_OWNER_PRIVATE_KEY` na API.

> Se preferir, o deploy pode ser feito manualmente no Remix seguindo o guia em `contracts/README.md`.

## Integração Blockchain na API

- Ao criar uma eleição (`POST /api/eleicoes`), informe candidatos opcionais:

  ```json
  {
    "titulo": "Eleicao do Conselho",
    "descricao": "Mandato 2026",
    "data_inicio": "2025-10-10T09:00:00",
    "data_fim": "2025-10-20T18:00:00",
    "candidatos": ["Alice", "Bob"]
  }
  ```

- Se `CONTRACT_ADDRESS` e `CONTRACT_OWNER_PRIVATE_KEY` estiverem configurados, a API:
  - Chama `configureElection` na criação (sincronizando nome/candidatos).
  - Chama `openElection` ao iniciar (`POST /api/eleicoes/{id}/start`).
  - Chama `closeElection` ao encerrar (`POST /api/eleicoes/{id}/end`).
  - A resposta inclui `blockchain_tx` com o hash da transação quando disponível.
- Sem essas variáveis, a API continua funcionando apenas com o banco de dados.

## Comandos Úteis de Docker

- Reconstruir apenas a imagem da API:

  ```bash
  docker compose build app
  ```

- Ver logs em tempo real:

  ```bash
  docker compose logs -f app
  ```

- Recriar apenas o serviço de banco de dados:

  ```bash
  docker compose up --build db
  ```

## Estrutura do Projeto

- `app.py`: ponto de entrada Flask
- `routes/`: blueprints agrupados por domínio (`auth`, `health`, `elections`)
- `services/`: regras de negócio (autenticação, healthcheck, eleições, integração blockchain)
- `config/`: conectores de banco e Web3
- `models/`: modelos SQLAlchemy
- `contracts/`: contrato AthenaElection (sol, JSON, README)
- `scripts/`: utilitários (deploy do contrato)
- `tests/`: suíte Pytest

## Troubleshooting

- **`RuntimeError: No blockchain provider configured`**: verifique `INFURA_URL` ou `WEB3_PROVIDER_URI`.
- **Falha ao conectar no banco**: confira credenciais/porta e use `docker compose logs db`.
- **Tabelas ausentes (erro 1146)**: execute `docker compose exec app python -c "from app import app, db; from models import *; with app.app_context(): db.create_all()"`.
- **Transação revertida**: confira se a carteira tem saldo e se você é o owner do contrato.

## Endpoints Principais

- `GET /health`
- `POST /auth/request_nonce`
- `POST /auth/verify`
- `POST /auth/logout`
- `POST /api/eleicoes`
- `GET /api/eleicoes`
- `GET /api/eleicoes/{id}`
- `PUT /api/eleicoes/{id}`
- `DELETE /api/eleicoes/{id}`
- `POST /api/eleicoes/{id}/start`
- `POST /api/eleicoes/{id}/end`
