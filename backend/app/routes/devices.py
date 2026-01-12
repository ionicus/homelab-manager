"""Device routes."""

from flask import Blueprint, request, jsonify

from app.database import Session
from app.models import Device, DeviceType, DeviceStatus

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("", methods=["GET"])
def list_devices():
    """List all devices."""
    db = Session()
    try:
        devices = db.query(Device).all()
        return jsonify([device.to_dict() for device in devices]), 200
    finally:
        db.close()


@devices_bp.route("/<int:device_id>", methods=["GET"])
def get_device(device_id: int):
    """Get a specific device."""
    db = Session()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404
        return jsonify(device.to_dict()), 200
    finally:
        db.close()


@devices_bp.route("", methods=["POST"])
def create_device():
    """Create a new device."""
    data = request.get_json()

    if not data or "name" not in data or "type" not in data:
        return jsonify({"error": "Missing required fields: name, type"}), 400

    db = Session()
    try:
        # Check if device with same name already exists
        existing = db.query(Device).filter(Device.name == data["name"]).first()
        if existing:
            return jsonify({"error": "Device with this name already exists"}), 409

        device = Device(
            name=data["name"],
            type=DeviceType(data["type"]),
            status=DeviceStatus(data.get("status", "active")),
            ip_address=data.get("ip_address"),
            mac_address=data.get("mac_address"),
            device_metadata=data.get("metadata", {}),
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        return jsonify(device.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {str(e)}"}), 400
    finally:
        db.close()


@devices_bp.route("/<int:device_id>", methods=["PUT"])
def update_device(device_id: int):
    """Update a device."""
    data = request.get_json()

    db = Session()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Update fields
        if "name" in data:
            device.name = data["name"]
        if "type" in data:
            device.type = DeviceType(data["type"])
        if "status" in data:
            device.status = DeviceStatus(data["status"])
        if "ip_address" in data:
            device.ip_address = data["ip_address"]
        if "mac_address" in data:
            device.mac_address = data["mac_address"]
        if "metadata" in data:
            device.device_metadata = data["metadata"]

        db.commit()
        db.refresh(device)

        return jsonify(device.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {str(e)}"}), 400
    finally:
        db.close()


@devices_bp.route("/<int:device_id>", methods=["DELETE"])
def delete_device(device_id: int):
    """Delete a device."""
    db = Session()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        db.delete(device)
        db.commit()

        return jsonify({"message": "Device deleted successfully"}), 200
    finally:
        db.close()


@devices_bp.route("/<int:device_id>/services", methods=["GET"])
def get_device_services(device_id: int):
    """Get all services for a device."""
    db = Session()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        services = [service.to_dict() for service in device.services]
        return jsonify(services), 200
    finally:
        db.close()


@devices_bp.route("/<int:device_id>/metrics", methods=["GET"])
def get_device_metrics(device_id: int):
    """Get metrics for a device."""
    db = Session()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Get limit from query params, default to 100
        limit = request.args.get("limit", 100, type=int)

        # Get recent metrics
        metrics = (
            db.query(Device)
            .filter(Device.id == device_id)
            .order_by(Device.id.desc())
            .limit(limit)
            .all()
        )

        return jsonify([metric.to_dict() for metric in device.metrics[-limit:]]), 200
    finally:
        db.close()
