"""Homelab Manager Flask Application."""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.extensions import limiter
from app.utils.errors import APIError, handle_database_exception

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add source location for errors
        if record.levelno >= logging.ERROR:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable log formatter for development."""

    def __init__(self):
        super().__init__(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(app):
    """Configure application logging based on environment."""
    log_level = getattr(
        logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO
    )
    log_file = app.config.get("LOG_FILE")
    log_format = app.config.get("LOG_FORMAT", "text")

    # Select formatter based on environment
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log file is configured)
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10,
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create log file {log_file}: {e}")

    # Set third-party logger levels
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level <= logging.DEBUG else logging.WARNING
    )

    logger.info(
        f"Logging configured: level={logging.getLevelName(log_level)}, format={log_format}"
    )


SWAGGER_TEMPLATE = {
    "info": {
        "title": "Homelab Manager API",
        "description": "API for managing homelab infrastructure including devices, "
        "network interfaces, services, metrics, and automation.",
        "version": "0.2.0",
        "contact": {
            "name": "Homelab Manager",
            "url": "https://github.com/ionicus/homelab-manager",
        },
    },
    "basePath": "/api",
    "schemes": ["http", "https"],
    "tags": [
        {"name": "Devices", "description": "Device management operations"},
        {"name": "Network Interfaces", "description": "Network interface operations"},
        {"name": "Services", "description": "Service tracking operations"},
        {"name": "Metrics", "description": "Performance metrics operations"},
        {"name": "Automation", "description": "Automation and playbook execution"},
    ],
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Call init_app if the config class has one (production validation)
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Set up logging first
    setup_logging(app)

    # Log startup info
    flask_env = app.config.get("FLASK_ENV", "development")
    logger.info(f"Starting homelab-manager in {flask_env} mode")

    # Initialize extensions
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    jwt = JWTManager(app)
    limiter.init_app(app)

    # Request logging middleware
    @app.before_request
    def log_request_info():
        """Log incoming request details (debug level)."""
        if app.debug:
            logger.debug(
                f"Request: {request.method} {request.path} "
                f"from {request.remote_addr}"
            )

    @app.after_request
    def log_response_info(response):
        """Log response status for errors."""
        if response.status_code >= 400:
            logger.warning(
                f"Response: {request.method} {request.path} -> {response.status_code}"
            )
        return response

    # JWT error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        logger.warning(f"Invalid JWT token: {error_string}")
        return jsonify({"error": "Invalid token", "details": error_string}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        logger.warning(f"Missing JWT token: {error_string}")
        return jsonify({"error": "Missing authorization token"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logger.warning(f"Expired JWT token for user: {jwt_payload.get('sub')}")
        return jsonify({"error": "Token has expired"}), 401

    # Only enable Swagger in non-production
    if flask_env != "production":
        Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

    # Late imports to avoid circular imports
    from app.cli import register_cli
    from app.routes import register_blueprints

    # Register blueprints
    register_blueprints(app)

    # Register CLI commands
    register_cli(app)

    # Register error handlers
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        logger.warning(f"API Error {error.status_code}: {error.message}")
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Handle SQLAlchemy database errors."""
        logger.error(f"Database error: {str(error)}")
        return handle_database_exception(error)

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError exceptions (usually enum validation)."""
        logger.warning(f"ValueError: {str(error)}")
        # Don't expose raw error message in production
        return jsonify({"error": "Invalid input provided"}), 400

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded errors."""
        logger.warning(f"Rate limit exceeded: {error.description}")
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected exceptions."""
        logger.exception(f"Unexpected error: {str(error)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "homelab-manager"}, 200

    return app
