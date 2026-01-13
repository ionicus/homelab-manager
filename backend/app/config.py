"""Application configuration."""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://homelab:homelab@localhost:5432/homelab_db"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = FLASK_ENV == "development"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )

    # API
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Ansible
    ANSIBLE_PLAYBOOK_DIR = os.getenv("ANSIBLE_PLAYBOOK_DIR", "../ansible/playbooks")
    ANSIBLE_INVENTORY_DIR = os.getenv("ANSIBLE_INVENTORY_DIR", "../ansible/inventory")

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
