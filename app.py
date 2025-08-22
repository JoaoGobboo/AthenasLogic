from flask import Flask
import logging
from routes.health import health_bp
from routes.auth import auth_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Registrar blueprint das rotas
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
