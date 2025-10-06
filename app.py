import logging
import os

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from config.Database import build_sqlalchemy_uri
from models import db
from routes.auth import auth_bp
from routes.elections import elections_bp
from routes.health import health_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    preconfigured_uri = app.config.get("SQLALCHEMY_DATABASE_URI") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if preconfigured_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = preconfigured_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = build_sqlalchemy_uri()

    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError as exc:  # pragma: no cover - defensive log for prod visibility
            logging.error("Failed to create database tables: %s", exc)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(elections_bp)

    @app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:
        db.session.remove()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
