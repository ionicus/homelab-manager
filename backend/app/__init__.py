"""Homelab Manager Flask Application."""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import Config
from app.routes import register_blueprints


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, origins=app.config["CORS_ORIGINS"])
    JWTManager(app)

    # Register blueprints
    register_blueprints(app)

    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "homelab-manager"}, 200

    return app
