"""Homelab Manager Flask Application."""

import logging

from flasgger import Swagger
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import SQLAlchemyError

from app.cli import register_cli
from app.config import Config
from app.routes import register_blueprints
from app.utils.errors import APIError, handle_database_exception

logger = logging.getLogger(__name__)

# Initialize rate limiter (attached to app in create_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
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

    # Initialize extensions
    CORS(app, origins=app.config["CORS_ORIGINS"])
    JWTManager(app)
    limiter.init_app(app)
    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

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
