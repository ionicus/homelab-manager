"""Route registration."""

from flask import Flask

from app.routes.devices import devices_bp
from app.routes.services import services_bp
from app.routes.metrics import metrics_bp
from app.routes.provisioning import provisioning_bp


def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app."""
    api_prefix = app.config.get("API_PREFIX", "/api")

    app.register_blueprint(devices_bp, url_prefix=f"{api_prefix}/devices")
    app.register_blueprint(services_bp, url_prefix=f"{api_prefix}/services")
    app.register_blueprint(metrics_bp, url_prefix=f"{api_prefix}/metrics")
    app.register_blueprint(provisioning_bp, url_prefix=f"{api_prefix}/provision")
