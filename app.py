import logging
import os

from flask import Flask, jsonify
from flasgger import Swagger
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config.Database import build_sqlalchemy_uri
from models import db
from routes.auth import auth_bp
from routes.candidates import candidates_bp
from routes.elections import elections_bp
from routes.health import health_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Athenas Logic API",
        "description": "API para autenticaÃ§Ã£o via blockchain e operaÃ§Ãµes eleitorais.",
        "version": "1.0.0",
    },
    "schemes": ["http", "https"],
    "basePath": "/",
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "openapi",
            "route": "/openapi.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SWAGGER", {"title": "Athenas Logic API", "uiversion": 3})

    preconfigured_uri = app.config.get("SQLALCHEMY_DATABASE_URI") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if preconfigured_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = preconfigured_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = build_sqlalchemy_uri()

    db.init_app(app)
    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError as exc:  # pragma: no cover - defensive log for prod visibility
            logging.error("Failed to create database tables: %s", exc)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(elections_bp)
    app.register_blueprint(candidates_bp)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        description = exc.description or exc.name
        response = jsonify({"description": description})
        response.status_code = exc.code or 500
        return response

    @app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:
        db.session.remove()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
