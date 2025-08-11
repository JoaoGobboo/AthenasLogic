from config.BlockChain import blockchain
from config.Database import connect_db, get_db_config
import logging

# To do list...
# - [x] Conenectar banco de dados e BlockChain
# - [] Verificar como integrar a API junto a blockchain, API, DB e BlockChain devem se comunica
# - [] Iniciar o desenvolvimento da API

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_blockchain():
    # Verifica a conexão com a rede Ethereum Testnet e registra o último bloco.
    if blockchain.is_connected():
        logging.info('✅ Blockchain conectada')
        logging.info(f'Último bloco: {blockchain.get_latest_block()}')
    else:
        logging.error('❌ Falha na conexão com blockchain')

def check_database():
    # Conecta ao banco de dados e lista as tabelas existentes.
    config = get_db_config()
    with connect_db(config) as connection:
        if connection:
            logging.info('✅ Banco conectado com sucesso!')
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                for table in cursor.fetchall():
                    logging.info(f"Tabela: {table}")
        else:
            logging.error('❌ Falha na conexão com banco')

def main():
    check_blockchain()
    check_database()

if __name__ == "__main__":
    main()
