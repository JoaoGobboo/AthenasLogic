from flask import Flask, jsonify
from config.BlockChain import blockchain
from config.Database import connect_db, get_db_config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def check_blockchain():
    if blockchain.is_connected():
        logging.info('✅ Blockchain conectada')
        logging.info(f'Último bloco: {blockchain.get_latest_block()}')
        return True, blockchain.get_latest_block()
    else:
        logging.error('❌ Falha na conexão com blockchain')
        return False, None

def check_database():
    config = get_db_config()
    try:
        with connect_db(config) as connection:
            if connection:
                logging.info('✅ Banco conectado com sucesso!')
                with connection.cursor() as cursor:
                    cursor.execute("SHOW TABLES")
                    tables = [table[0] for table in cursor.fetchall()]
                    for table in tables:
                        logging.info(f"Tabela: {table}")
                return True
            else:
                logging.error('❌ Falha na conexão com banco')
                return False
    except Exception as e:
        logging.error(f'❌ Erro na conexão com banco: {e}')
        return False

@app.route("/health", methods=["GET"])
def healthcheck():
    bc_status, latest_block = check_blockchain()
    db_status = check_database()

    status_code = 200 if bc_status and db_status else 500

    return jsonify({
        "blockchain": {
            "connected": bc_status,
            "latest_block": latest_block
        },
        "database": {
            "connected": db_status
        }
    }), status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
