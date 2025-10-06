import os
import sys

import pytest
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite://")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import db


@pytest.fixture(scope="session", autouse=True)
def configure_database():
    for key in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT"):
        os.environ.pop(key, None)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    with app.app_context():
        db.engine.dispose()
        db.drop_all()
        db.create_all()
    yield
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        app.extensions.pop("nonce_store", None)
    with app.test_client() as test_client:
        yield test_client
