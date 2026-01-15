"""Application configuration with strict dev/prod separation."""

import os
import sys
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


def validate_production_config():
    """Validate that all required production settings are configured.

    Raises:
        RuntimeError: If required production settings are missing
    """
    required_vars = [
        ("SECRET_KEY", "Application secret key"),
        ("JWT_SECRET_KEY", "JWT signing key"),
        ("DATABASE_URL", "Database connection string"),
    ]

    missing = []
    for var, description in required_vars:
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")

    if missing:
        print("\n" + "=" * 60, file=sys.stderr)
        print("PRODUCTION CONFIGURATION ERROR", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(
            "The following required environment variables are not set:\n",
            file=sys.stderr,
        )
        print("\n".join(missing), file=sys.stderr)
        print("\n" + "=" * 60 + "\n", file=sys.stderr)
        raise RuntimeError("Missing required production configuration")

    # Warn about insecure settings
    warnings = []
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if "*" in cors_origins:
        warnings.append("  - CORS_ORIGINS contains wildcard (*) - this is insecure")
    if "localhost" in cors_origins or "127.0.0.1" in cors_origins:
        warnings.append("  - CORS_ORIGINS contains localhost - remove for production")

    if warnings:
        print("\n" + "=" * 60, file=sys.stderr)
        print("PRODUCTION CONFIGURATION WARNINGS", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("\n".join(warnings), file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)


class Config:
    """Base configuration - production-safe defaults only."""

    # Environment
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Flask - secrets required in production
    SECRET_KEY = _get_secret("SECRET_KEY", "dev-only-secret-key-not-for-production!")

    # Database - no default, must be explicitly set
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Never log SQL in base config

    # CORS - empty by default, must be explicitly configured
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]

    # JWT Configuration
    JWT_SECRET_KEY = _get_secret(
        "JWT_SECRET_KEY", "dev-only-jwt-key-not-for-production!"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_COOKIE_NAME = "access_token"
    JWT_COOKIE_SECURE = True  # Always secure by default
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = False

    # API
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    HOST = os.getenv("HOST", "127.0.0.1")  # Localhost by default (safe)
    PORT = int(os.getenv("PORT", "5000"))

    # Ansible
    ANSIBLE_PLAYBOOK_DIR = os.getenv(
        "ANSIBLE_PLAYBOOK_DIR", "automation/ansible/playbooks"
    )

    # Logging - production defaults
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")  # Conservative default
    LOG_FILE = os.getenv("LOG_FILE")  # No file logging by default
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # Structured logging for production

    # File Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))

    # Celery / Redis
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"
    )
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "600"))


class DevelopmentConfig(Config):
    """Development configuration with convenient defaults."""

    DEBUG = True

    # Database - development default
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://homelab:homelab@localhost:5432/homelab_db"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "true").lower() == "true"

    # CORS - allow localhost in development
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")
        if origin.strip()
    ]

    # JWT - less strict in development
    JWT_COOKIE_SECURE = False  # Allow HTTP in development

    # API - bind to all interfaces in development
    HOST = os.getenv("HOST", "0.0.0.0")

    # Logging - verbose in development
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # Human-readable in development

    # Celery - longer timeout for debugging
    CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800"))


class ProductionConfig(Config):
    """Production configuration with security hardening."""

    DEBUG = False

    # Validate configuration on class load
    @classmethod
    def init_app(cls, app):
        """Initialize production application with validation."""
        validate_production_config()

    # Database - require explicit configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ECHO = False

    # Database connection pooling for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,  # Validate connections before use
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    }

    # CORS - must be explicitly configured
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]

    # JWT - strict security
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"  # Stricter CSRF protection in production

    # API - only localhost by default (reverse proxy handles external)
    HOST = os.getenv("HOST", "127.0.0.1")

    # Logging - production appropriate
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")


class TestingConfig(Config):
    """Testing configuration with isolated database."""

    TESTING = True
    DEBUG = True

    # Use in-memory SQLite for tests
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # CORS - allow all in tests
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

    # JWT - disable security for easier testing
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

    # Logging - minimal in tests
    LOG_LEVEL = "ERROR"
    LOG_FILE = None
    LOG_FORMAT = "text"

    # Celery - use eager mode for synchronous testing
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
