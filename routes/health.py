# -*- coding: utf-8 -*-

import logging
import time

from flask import Blueprint, jsonify

from config.BlockChain import get_web3, get_latest_block, is_blockchain_connected
from config.Database import check_db_connection, get_db_config, is_db_config_complete
from services.health_service import HealthLogEntry, build_health_response


health_bp = Blueprint("health", __name__)
START_TIME = time.time()
VERSION = "1.0.0"


def _log_health_entries(entries: tuple[HealthLogEntry, ...]) -> None:
    dispatch = {
        "debug": logging.debug,
        "info": logging.info,
        "warning": logging.warning,
        "error": logging.error,
        "critical": logging.critical,
    }
    for entry in entries:
        logger = dispatch.get(entry.level.lower(), logging.info)
        logger(entry.message)


@health_bp.route("/health", methods=["GET"])
def healthcheck() -> tuple:
    """Retorna o estado de saúde da aplicação.
    ---
    tags:
      - Health
    responses:
      200:
        description: Serviço saudável
        schema:
          type: object
          properties:
            blockchain:
              type: object
              properties:
                connected:
                  type: boolean
                latest_block:
                  type: integer
                  format: int64
                  x-nullable: true
            database:
              type: object
              properties:
                connected:
                  type: boolean
            service:
              type: object
              properties:
                uptime_seconds:
                  type: number
                  format: float
                version:
                  type: string
      503:
        description: Dependências indisponíveis
    """
    response = build_health_response(
        start_time=START_TIME,
        version=VERSION,
        get_web3=get_web3,
        blockchain_connected=is_blockchain_connected,
        block_fetcher=get_latest_block,
        get_db_config=get_db_config,
        database_connected=check_db_connection,
        config_checker=is_db_config_complete,
        now=time.time,
    )

    _log_health_entries(response.logs)
    return jsonify(response.payload), response.status_code


@health_bp.route("/healthz", methods=["GET"])
def healthcheck_ready() -> tuple:
    """Readiness probe que exige dependências externas ativas."""
    response = build_health_response(
        start_time=START_TIME,
        version=VERSION,
        get_web3=get_web3,
        blockchain_connected=is_blockchain_connected,
        block_fetcher=get_latest_block,
        get_db_config=get_db_config,
        database_connected=check_db_connection,
        config_checker=is_db_config_complete,
        now=time.time,
        retry_attempts=3,
        retry_delay=0.2,
        require_blockchain=True,
        require_database=True,
    )

    _log_health_entries(response.logs)
    return jsonify(response.payload), response.status_code
