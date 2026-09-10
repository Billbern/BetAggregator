import logging
import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate, socketio


def create_app(config_name: str | None = None) -> Flask:
    """Application factory.

    ``config_name`` selects a config class directly (used by tests), and
    otherwise falls back to the ``APP_ENV`` environment variable
    (default: "development").
    """
    config_name = config_name or os.environ.get("APP_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(
        app,
        async_mode=app.config.get("SOCKETIO_ASYNC_MODE", "threading"),
        cors_allowed_origins=app.config.get("SOCKETIO_CORS_ALLOWED_ORIGINS", "*"),
    )
    _configure_logging(app)

    # Importing models registers them with SQLAlchemy's metadata (needed by Alembic).
    from app import models  # noqa: F401

    from app.routes import main_bp

    app.register_blueprint(main_bp)
    return app


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
        force=True,
    )
