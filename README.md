# Athenas Logic API

API Flask para autentica��o via blockchain e opera��es eleitorais. O servi�o exp�e rotas de sa�de e autentica��o, integra com MySQL e Web3, e inclui su�te de testes com Pytest.

## Pr�-requisitos

- Python 3.11+
- Docker e Docker Compose
- Acesso a um endpoint Ethereum (Infura, Alchemy etc.) para funcionalidades que dependem da blockchain

## Vari�veis de Ambiente

Crie um arquivo `.env` na raiz com o m�nimo necess�rio:

```env
# Blockchain
INFURA_URL=https://seu-endpoint-ethereum

# Banco de dados MySQL
DB_HOST=db
DB_PORT=3306
DB_NAME=athenas
DB_USER=usuario
DB_PASSWORD=senha123
```

> No modo Docker, `DB_HOST` deve apontar para o servi�o `db` definido no `docker-compose.yml`.

## Guia R�pido

### Ambiente Local

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest
python app.py
```

A aplica��o estar� acess�vel em `http://localhost:5000`.

### Docker Compose

1. Garanta que o `.env` esteja configurado (veja se��o anterior).
2. Construa e suba a stack:

   ```bash
   docker compose up --build
   ```

   Use `-d` para executar em background (`docker compose up --build -d`).

3. Para executar um comando isolado sem manter o container rodando (ex.: rodar testes e sair):

   ```bash
   docker compose run --rm app python -m pytest
   ```

4. Para parar tudo e remover containers:

   ```bash
   docker compose down
   ```

5. Para uma limpeza completa (inclui volumes do MySQL):

   ```bash
   docker compose down -v
   ```

6. Executar comandos dentro de um container j� em execu��o (ex.: re-rodar testes):

   ```bash
   docker compose exec app python -m pytest
   ```

## Comandos �teis de Docker

- Reconstruir apenas a imagem da API:

  ```bash
  docker compose build app
  ```

- Ver logs em tempo real:

  ```bash
  docker compose logs -f app
  ```

- Recriar apenas o servi�o de banco de dados:

  ```bash
  docker compose up --build db
  ```

## Estrutura do Projeto

- `app.py`: ponto de entrada Flask
- `routes/`: blueprints agrupados por dom�nio (`auth`, `health`)
- `services/`: regras de neg�cio desacopladas das rotas
- `config/`: conectores de banco e blockchain
- `models/`: modelos SQLAlchemy
- `tests/`: su�te Pytest
- `contracts/`: artefatos do smart contract AthenaElection
## Troubleshooting

- **`RuntimeError: No blockchain provider configured`**: verifique se `INFURA_URL` (ou `WEB3_PROVIDER_URI`) est� definido no `.env`.
- **Falha ao conectar no banco**: confirme credenciais e disponibilidade do servi�o MySQL. Em Docker, execute `docker compose logs db`.
- **Tabelas ausentes (erro 1146)**: execute `docker compose exec app python -c "from app import app, db; from models import *; with app.app_context(): db.create_all()"` para recriar as tabelas.

## Endpoints Principais

- `GET /health`: status do servi�o, blockchain e banco.
- `POST /auth/request_nonce`: solicita nonce de autentica��o.
- `POST /auth/verify`: verifica assinatura e conclui login.
- `POST /auth/logout`: encerra sess�o.
- `POST /api/eleicoes`: cria nova elei��o.
- `GET /api/eleicoes`: lista elei��es.
- `GET /api/eleicoes/{id}`: detalhes de uma elei��o.
- `PUT /api/eleicoes/{id}`: atualiza elei��o.
- `DELETE /api/eleicoes/{id}`: remove elei��o.
- `POST /api/eleicoes/{id}/start`: inicia elei��o.
- `POST /api/eleicoes/{id}/end`: encerra elei��o.
