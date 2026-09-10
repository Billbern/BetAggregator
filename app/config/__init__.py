import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_DB_URI = "sqlite:///betaggregator.dev.db"


class Config:
    """Base configuration; every value can be overridden via environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-change-me")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _DEFAULT_DB_URI)

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_BACKEND_URL = os.environ.get(
        "CELERY_BACKEND_URL", "redis://localhost:6379/1"
    )

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get(
        "SOCKETIO_CORS_ALLOWED_ORIGINS", "*"
    )


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    LOG_LEVEL = "WARNING"


class StagingConfig(Config):
    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "testing": TestingConfig,
    "test": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
}
