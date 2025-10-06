import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


@pytest.fixture(scope="session")
def db_url() -> str:
    """Return an in-memory SQLite URL for database-related tests."""
    return "sqlite:///:memory:"


@pytest.fixture
def client():
    """Provide a Flask test client with a clean nonce store per test."""
    app.config["TESTING"] = True
    with app.app_context():
        app.extensions.pop("nonce_store", None)
    with app.test_client() as test_client:
        yield test_client
