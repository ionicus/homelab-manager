"""Route registration."""

from flask import Flask

from app.routes.auth import auth_bp
from app.routes.automation import automation_bp
from app.routes.devices import devices_bp
from app.routes.metrics import metrics_bp
from app.routes.network_interfaces import interfaces_bp
from app.routes.services import services_bp
from app.routes.workflows import workflows_bp


def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app."""
    api_prefix = app.config.get("API_PREFIX", "/api")

    # Auth routes (public login, protected user management)
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")

    # Protected routes
    app.register_blueprint(devices_bp, url_prefix=f"{api_prefix}/devices")
    app.register_blueprint(services_bp, url_prefix=f"{api_prefix}/services")
    app.register_blueprint(metrics_bp, url_prefix=f"{api_prefix}/metrics")
    app.register_blueprint(automation_bp, url_prefix=f"{api_prefix}/automation")
    app.register_blueprint(workflows_bp, url_prefix=f"{api_prefix}/workflows")
    app.register_blueprint(interfaces_bp, url_prefix=api_prefix)
