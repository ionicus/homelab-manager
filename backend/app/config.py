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

    # JWT - HttpOnly cookie configuration
    JWT_SECRET_KEY = _get_secret(
        "JWT_SECRET_KEY", "dev-only-jwt-key-not-for-production!"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )
    # Store JWT in HttpOnly cookies instead of localStorage (XSS protection)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"  # HTTPS only in prod
    JWT_COOKIE_SAMESITE = "Lax"  # CSRF protection
    JWT_COOKIE_CSRF_PROTECT = True  # Enable CSRF protection for cookie auth
    JWT_CSRF_IN_COOKIES = False  # Send CSRF token in response body, not cookie

    # API
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Ansible
    ANSIBLE_PLAYBOOK_DIR = os.getenv(
        "ANSIBLE_PLAYBOOK_DIR", "automation/ansible/playbooks"
    )

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")

    # File Uploads (max request size for avatar uploads)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size

    # Celery / Redis
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 600  # 10 minutes max per task


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
