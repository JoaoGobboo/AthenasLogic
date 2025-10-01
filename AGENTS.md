# Repository Guidelines

## Project Structure & Module Organization
The Flask entrypoint lives in `app.py`; HTTP blueprints reside in `routes/` organized by domain (auth, health, elections). Domain entities and serializers live in `models/` and `dtos/`, while shared connectors for MySQL and blockchain access sit in `config/`. Tests in `tests/` mirror route and model modules, and container assets (`Dockerfile`, `docker-compose.yml`) support reproducible environments.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a virtual environment for local work.
- `pip install -r requirements.txt`: install Flask, Web3, and connector dependencies.
- `python app.py`: boot the Flask dev server on http://localhost:5000.
- `docker compose up --build`: run the stack (API + services) via Docker.
- `pytest`: execute the full test suite; add `-k <pattern>` to focus specific modules.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation. Keep modules and files in snake_case (`routes/auth.py`), classes in PascalCase, and constants uppercase. Route handlers should stay thin—delegate database and blockchain logic to helpers in `config/` and data structures in `models/` or `dtos/`. Prefer f-strings for logging and reuse the configured logger in `app.py`.

## Testing Guidelines
Pytest powers the suite; place new cases under `tests/` using `test_<feature>.py`. Mirror source module names for quick discovery and extend fixtures from `tests/conftest.py` for test clients or in-memory databases. Add regression coverage for every new route, model, and blockchain interaction to guard against API regressions.

## Commit & Pull Request Guidelines
Commits should be concise and imperative, optionally prefixed with a scope (`fix:`, `feat:`) as seen in history. Before opening a PR, consolidate work into meaningful commits. Provide context: the problem, proposed solution, any env or DB changes, and screenshots or curl samples for API behavior. Link related issues or tickets so reviewers can trace requirements.

## Security & Configuration Tips
Load secrets from a local `.env` file consumed by `config/Database.py`; never commit credentials. Prefer Docker Compose when validating database interactions, and refresh RPC endpoints or keys before promoting to new environments.
