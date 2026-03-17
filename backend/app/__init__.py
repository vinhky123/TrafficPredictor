from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .config import Settings
from .routes.health_routes import health_bp
from .routes.traffic_routes import traffic_bp


def create_app(settings: Settings | None = None) -> Flask:
    app = Flask(__name__)

    settings = settings or Settings.from_env()
    app.config["APP_SETTINGS"] = settings

    CORS(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(traffic_bp, url_prefix="/api")

    return app
