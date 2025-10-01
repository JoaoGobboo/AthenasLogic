import logging
import time

from flask import Blueprint, jsonify

from config.BlockChain import get_web3, get_latest_block, is_blockchain_connected
from config.Database import check_db_connection, get_db_config
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
    response = build_health_response(
        start_time=START_TIME,
        version=VERSION,
        get_web3=get_web3,
        blockchain_connected=is_blockchain_connected,
        block_fetcher=get_latest_block,
        get_db_config=get_db_config,
        database_connected=check_db_connection,
        now=time.time,
    )

    _log_health_entries(response.logs)
    return jsonify(response.payload), response.status_code
