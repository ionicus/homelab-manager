"""Service routes."""

from flask import Blueprint, request, jsonify

from app.database import Session
from app.models import Service, ServiceStatus, Device

services_bp = Blueprint("services", __name__)


@services_bp.route("", methods=["GET"])
def list_services():
    """List all services."""
    db = Session()
    try:
        services = db.query(Service).all()
        return jsonify([service.to_dict() for service in services]), 200
    finally:
        db.close()


@services_bp.route("/<int:service_id>", methods=["GET"])
def get_service(service_id: int):
    """Get a specific service."""
    db = Session()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return jsonify({"error": "Service not found"}), 404
        return jsonify(service.to_dict()), 200
    finally:
        db.close()


@services_bp.route("", methods=["POST"])
def create_service():
    """Create a new service."""
    data = request.get_json()

    if not data or "device_id" not in data or "name" not in data:
        return jsonify({"error": "Missing required fields: device_id, name"}), 400

    db = Session()
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data["device_id"]).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        service = Service(
            device_id=data["device_id"],
            name=data["name"],
            port=data.get("port"),
            protocol=data.get("protocol"),
            status=ServiceStatus(data.get("status", "stopped")),
            health_check_url=data.get("health_check_url"),
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        return jsonify(service.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {str(e)}"}), 400
    finally:
        db.close()


@services_bp.route("/<int:service_id>", methods=["DELETE"])
def delete_service(service_id: int):
    """Delete a service."""
    db = Session()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return jsonify({"error": "Service not found"}), 404

        db.delete(service)
        db.commit()

        return jsonify({"message": "Service deleted successfully"}), 200
    finally:
        db.close()


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
