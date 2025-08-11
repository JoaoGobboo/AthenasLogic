import mysql.connector
from mysql.connector import Error
import logging
from dotenv import load_dotenv
import os
from contextlib import contextmanager

load_dotenv()

def get_db_config():
    return {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }

@contextmanager
def connect_db(config):
    logging.info(f"Tentando conectar ao banco {config['database']} em {config['host']}:{config['port']} ...")
    conn = None
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            logging.info("Conexão ao banco de dados estabelecida com sucesso.")
            yield conn
        else:
            logging.warning("Falha ao estabelecer conexão com o banco.")
            yield None
    except Error as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        yield None
    finally:
        if conn and conn.is_connected():
            conn.close()
            logging.info("Conexão ao banco encerrada.")