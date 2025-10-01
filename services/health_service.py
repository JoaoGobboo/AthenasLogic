from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from web3 import Web3


@dataclass(frozen=True)
class HealthLogEntry:
    level: str
    message: str


@dataclass(frozen=True)
class HealthResponse:
    payload: dict
    status_code: int
    logs: tuple[HealthLogEntry, ...] = ()


def build_health_response(
    *,
    start_time: float,
    version: str,
    get_web3: Callable[[], Web3],
    blockchain_connected: Callable[[Web3], bool],
    block_fetcher: Callable[[Web3], int],
    get_db_config: Callable[[], dict],
    database_connected: Callable[[dict], bool],
    now: Callable[[], float],
) -> HealthResponse:
    logs: list[HealthLogEntry] = []

    latest_block: int | None = None
    blockchain_status = False
    try:
        web3 = get_web3()
    except Exception as exc:  # pragma: no cover - defensive guard
        logs.append(HealthLogEntry(level="error", message=f"Erro ao inicializar Web3: {exc}"))
    else:
        try:
            blockchain_status = blockchain_connected(web3)
        except Exception as exc:  # pragma: no cover - defensive guard
            logs.append(HealthLogEntry(level="error", message=f"Erro ao verificar blockchain: {exc}"))
            blockchain_status = False
        else:
            if blockchain_status:
                try:
                    latest_block = block_fetcher(web3)
                    logs.append(HealthLogEntry(level="info", message="Blockchain conectada"))
                    logs.append(HealthLogEntry(level="info", message=f"Ultimo bloco: {latest_block}"))
                except Exception as exc:  # pragma: no cover - defensive guard
                    logs.append(HealthLogEntry(level="error", message=f"Erro ao obter ultimo bloco: {exc}"))
                    blockchain_status = False
            else:
                logs.append(HealthLogEntry(level="error", message="Falha na conexao com blockchain"))

    database_status = False
    try:
        db_config = get_db_config()
        database_status = database_connected(db_config)
    except Exception as exc:  # pragma: no cover - defensive guard
        logs.append(HealthLogEntry(level="error", message=f"Erro na conexao com banco: {exc}"))
    else:
        if database_status:
            logs.append(HealthLogEntry(level="info", message="Banco conectado com sucesso"))
        else:
            logs.append(HealthLogEntry(level="error", message="Falha na conexao com banco"))

    uptime_seconds = max(round(now() - start_time, 2), 0.0)
    status_code = 200 if blockchain_status and database_status else 500

    payload = {
        "blockchain": {
            "connected": blockchain_status,
            "latest_block": latest_block,
        },
        "database": {
            "connected": database_status,
        },
        "service": {
            "uptime_seconds": uptime_seconds,
            "version": version,
        },
    }

    return HealthResponse(payload=payload, status_code=status_code, logs=tuple(logs))
