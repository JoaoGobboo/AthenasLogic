from __future__ import annotations

import time
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
    config_checker: Callable[[dict], bool],
    now: Callable[[], float],
    retry_attempts: int = 1,
    retry_delay: float = 0.0,
    require_blockchain: bool = False,
    require_database: bool = True,
    sleep: Callable[[float], None] | None = None,
) -> HealthResponse:
    logs: list[HealthLogEntry] = []

    attempts = max(1, retry_attempts)
    delay = retry_delay if retry_delay > 0 else 0.0
    sleeper = sleep or time.sleep

    latest_block: int | None = None
    blockchain_status = False
    blockchain_status_label = "unhealthy"
    blockchain_configured = True

    web3: Web3 | None = None
    for attempt in range(1, attempts + 1):
        try:
            web3 = get_web3()
            blockchain_configured = True
            if attempt > 1:
                logs.append(
                    HealthLogEntry(
                        level="info",
                        message=f"Conexão com Web3 restabelecida após {attempt} tentativas",
                    )
                )
            break
        except Exception as exc:  # pragma: no cover - defensive guard
            message = str(exc)
            if isinstance(exc, RuntimeError) and "No blockchain provider configured" in message:
                blockchain_configured = False
                blockchain_status_label = "not_configured"
                logs.append(
                    HealthLogEntry(
                        level="warning",
                        message="Provider da blockchain não configurado; pulando verificação",
                    )
                )
                web3 = None
                break
            blockchain_configured = True
            logs.append(
                HealthLogEntry(
                    level="error",
                    message=(
                        f"Falha ao inicializar Web3 (tentativa {attempt}/{attempts}): {exc}"
                    ),
                )
            )
            web3 = None
            if attempt < attempts and delay:
                sleeper(delay)

    if web3 is not None:
        for attempt in range(1, attempts + 1):
            try:
                blockchain_status = bool(blockchain_connected(web3))
                break
            except Exception as exc:  # pragma: no cover - defensive guard
                logs.append(
                    HealthLogEntry(
                        level="error",
                        message=(
                            f"Erro ao verificar blockchain (tentativa {attempt}/{attempts}): {exc}"
                        ),
                    )
                )
                blockchain_status = False
                if attempt < attempts and delay:
                    sleeper(delay)

        if blockchain_status:
            try:
                latest_block = block_fetcher(web3)
                logs.append(HealthLogEntry(level="info", message="Blockchain conectada"))
                logs.append(HealthLogEntry(level="info", message=f"Ultimo bloco: {latest_block}"))
                blockchain_status_label = "healthy"
            except Exception as exc:  # pragma: no cover - defensive guard
                logs.append(HealthLogEntry(level="error", message=f"Erro ao obter ultimo bloco: {exc}"))
                blockchain_status = False
                blockchain_status_label = "unhealthy"
        elif blockchain_configured:
            logs.append(HealthLogEntry(level="error", message="Falha na conexao com blockchain"))

    if not blockchain_configured:
        blockchain_status = False

    database_configured = False
    database_status = False
    database_status_label = "unhealthy"
    db_config: dict | None = None
    try:
        db_config = get_db_config()
        database_configured = config_checker(db_config)
    except Exception as exc:  # pragma: no cover - defensive guard
        logs.append(HealthLogEntry(level="error", message=f"Erro ao carregar configuracao do banco: {exc}"))
    else:
        if not database_configured:
            logs.append(HealthLogEntry(level="info", message="Banco nao configurado; verificacao ignorada"))
            database_status_label = "not_configured"
        else:
            for attempt in range(1, attempts + 1):
                try:
                    database_status = database_connected(db_config)
                    if database_status:
                        logs.append(HealthLogEntry(level="info", message="Banco conectado com sucesso"))
                        database_status_label = "healthy"
                    else:
                        logs.append(HealthLogEntry(level="error", message="Falha na conexao com banco"))
                        database_status_label = "unhealthy"
                    break
                except Exception as exc:  # pragma: no cover - defensive guard
                    logs.append(
                        HealthLogEntry(
                            level="error",
                            message=(
                                f"Erro na conexao com banco (tentativa {attempt}/{attempts}): {exc}"
                            ),
                        )
                    )
                    database_status = False
                    database_status_label = "unhealthy"
                    if attempt < attempts and delay:
                        sleeper(delay)

    uptime_seconds = max(round(now() - start_time, 2), 0.0)
    database_ready = (
        database_status
        or not database_configured
        or not require_database
    )
    blockchain_ready = (
        blockchain_status
        or not blockchain_configured
        or not require_blockchain
    )
    status_code = 200 if database_ready and blockchain_ready else 503

    payload = {
        "blockchain": {
            "connected": blockchain_status,
            "latest_block": latest_block,
            "configured": blockchain_configured,
            "status": blockchain_status_label,
        },
        "database": {
            "configured": database_configured,
            "connected": database_status if database_configured else False,
            "status": database_status_label,
        },
        "service": {
            "uptime_seconds": uptime_seconds,
            "version": version,
        },
    }

    return HealthResponse(payload=payload, status_code=status_code, logs=tuple(logs))
