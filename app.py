import logging

from flask import Flask

from config.Database import build_sqlalchemy_uri
from models import db
from routes.auth import auth_bp
from routes.health import health_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_app() -> Flask:
    app = Flask(__name__)

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", build_sqlalchemy_uri())

    db.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    @app.teardown_appcontext
    def shutdown_session(exception: Exception | None = None) -> None:
        db.session.remove()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)