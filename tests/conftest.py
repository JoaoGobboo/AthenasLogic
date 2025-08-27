# Fixtures globais para os testes
# Inclui setup do banco de dados SQLite em memória, client de API, mocks, etc.
import pytest

@pytest.fixture(scope='session')
def db_url():
    """
    Fixture global que retorna a URL de um banco de dados SQLite em memória para ser usada nos testes.
    Útil para isolar os testes de banco de dados real e garantir ambiente limpo a cada execução.
    """
    return 'sqlite:///:memory:'

# Adicione outras fixtures conforme necessário para os testes

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    """
    Fixture que fornece um client de teste para a aplicação Flask.
    Permite simular requisições HTTP sem subir o servidor real.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
