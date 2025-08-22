from flask import Blueprint, jsonify
import time
import logging
from config.BlockChain import web3, is_blockchain_connected, get_latest_block
from config.Database import get_db_config, get_tables

health_bp = Blueprint('health', __name__)
START_TIME = time.time()
VERSION = "1.0.0"

def check_blockchain():
    if is_blockchain_connected(web3):
        latest_block = get_latest_block(web3)
        logging.info('✅ Blockchain conectada')
        logging.info(f'Último bloco: {latest_block}')
        return True, latest_block
    else:
        logging.error('❌ Falha na conexão com blockchain')
        return False, None

def check_database():
    config = get_db_config()
    try:
        tables = get_tables(config)
        if tables:
            logging.info('✅ Banco conectado com sucesso!')
            for table in tables:
                logging.info(f"Tabela: {table}")
            return True
        else:
            logging.error('❌ Falha na conexão com banco')
            return False
    except Exception as e:
        logging.error(f'❌ Erro na conexão com banco: {e}')
        return False

@health_bp.route("/health", methods=["GET"])
def healthcheck():
    bc_status, latest_block = check_blockchain()
    db_status = check_database()

    status_code = 200 if bc_status and db_status else 500
    uptime = round(time.time() - START_TIME, 2)

    return jsonify({
        "blockchain": {
            "connected": bc_status,
            "latest_block": latest_block
        },
        "database": {
            "connected": db_status
        },
        "service": {
            "uptime_seconds": uptime,
            "version": VERSION
        }
    }), status_code
