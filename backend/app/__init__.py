"""Homelab Manager Flask Application."""

import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.routes import register_blueprints
from app.utils.errors import APIError, handle_database_exception

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, origins=app.config["CORS_ORIGINS"])
    JWTManager(app)

    # Register blueprints
    register_blueprints(app)

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
        return jsonify({"error": f"Invalid value: {str(error)}"}), 400

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
