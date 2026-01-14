"""Application configuration."""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str, min_length: int = 32) -> str:
    """Require environment variable to be set with minimum length.

    Args:
        name: Environment variable name
        min_length: Minimum required length for the value

    Returns:
        The environment variable value

    Raises:
        RuntimeError: If the variable is not set or too short
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    if len(value) < min_length:
        raise RuntimeError(
            f"Environment variable {name} must be at least {min_length} characters"
        )
    return value


def _get_secret(name: str, dev_default: str) -> str:
    """Get a secret, requiring it in production.

    In development mode, returns a default value.
    In production, requires the secret to be explicitly set.

    Args:
        name: Environment variable name
        dev_default: Default value for development only

    Returns:
        The secret value
    """
    flask_env = os.getenv("FLASK_ENV", "development")
    if flask_env == "production":
        return _require_env(name)
    return os.getenv(name, dev_default)


class Config:
    """Base configuration."""

    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = _get_secret("SECRET_KEY", "dev-only-secret-key-not-for-production!")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://homelab:homelab@localhost:5432/homelab_db"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = FLASK_ENV == "development"

    # CORS - restrict to specific origins (no wildcards in production)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # JWT
    JWT_SECRET_KEY = _get_secret(
        "JWT_SECRET_KEY", "dev-only-jwt-key-not-for-production!"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )

    # API
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Ansible
    ANSIBLE_PLAYBOOK_DIR = os.getenv(
        "ANSIBLE_PLAYBOOK_DIR", "automation/ansible/playbooks"
    )
    ANSIBLE_INVENTORY_DIR = os.getenv(
        "ANSIBLE_INVENTORY_DIR", "automation/ansible/inventory"
    )

    # Monitoring
    METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
    ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
