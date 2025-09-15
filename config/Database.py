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
def connect_db(config: dict):
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

def check_db_connection(config: dict) -> bool:
    """Verifica se consegue conectar ao banco sem fazer query."""
    with connect_db(config) as connection:
        return connection is not None

def get_tables(config: dict) -> list[str]:
    """Retorna lista de tabelas do banco, ou lista vazia se falhar."""
    with connect_db(config) as connection:
        if not connection:
            return []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                return [table[0] for table in cursor.fetchall()]
        except Error as e:
            logging.error(f"Erro ao executar SHOW TABLES: {e}")
            return []
