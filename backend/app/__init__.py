"""TrafficPredictor Flask application factory.

This module creates and configures the Flask application with all
necessary extensions, blueprints, and error handlers.
"""

from __future__ import annotations

import logging
import sys

from flask import Flask
from flask_cors import CORS

from backend.app.config import Settings
from backend.app.dependencies import get_service_container
from backend.app.errors import register_error_handlers
from backend.app.routes.health_routes import health_bp
from backend.app.routes.traffic_routes import traffic_bp


def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Args:
        level: The logging level to use. Defaults to "INFO".
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        stream=sys.stdout,
    )
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)


def create_app(settings: Settings | None = None) -> Flask:
    """Create and configure the Flask application.

    This factory function sets up:
    - Application configuration
    - CORS middleware
    - Error handlers
    - Blueprints (routes)
    - Service container for dependency injection

    Args:
        settings: Optional Settings instance. If not provided,
                  settings will be loaded from environment variables.

    Returns:
        A configured Flask application instance.
    """
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    settings = settings or Settings.from_env()
    app.config["APP_SETTINGS"] = settings
    logger.info("Application configuration loaded")

    # Configure CORS
    CORS(app)
    logger.info("CORS enabled")

    # Register error handlers
    register_error_handlers(app)
    logger.info("Error handlers registered")

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(traffic_bp, url_prefix="/api")
    logger.info("Blueprints registered: health, traffic")

    # Initialize service container (lazy loading)
    # Services will be created on first access via get_service_container()

    logger.info("TrafficPredictor application created successfully")
    return app