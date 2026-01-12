"""Service routes."""

from flask import Blueprint, request, jsonify

from app.database import Session
from app.models import Service, ServiceStatus

services_bp = Blueprint("services", __name__)


@services_bp.route("/<int:service_id>/status", methods=["PUT"])
def update_service_status(service_id: int):
    """Update service status."""
    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({"error": "Missing required field: status"}), 400

    db = Session()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return jsonify({"error": "Service not found"}), 404

        service.status = ServiceStatus(data["status"])
        db.commit()
        db.refresh(service)

        return jsonify(service.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": f"Invalid status value: {str(e)}"}), 400
    finally:
        db.close()
