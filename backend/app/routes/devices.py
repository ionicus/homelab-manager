"""Device routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import Device, DeviceType, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    ConflictError,
    success_response,
    not_found_error,
)
from app.utils.validation import validate_request

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("", methods=["GET"])
def list_devices():
    """List all devices."""
    with DatabaseSession() as db:
        devices = db.query(Device).all()
        return success_response([device.to_dict() for device in devices])


@devices_bp.route("/<int:device_id>", methods=["GET"])
def get_device(device_id: int):
    """Get a specific device."""
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)
        return success_response(device.to_dict())


@devices_bp.route("", methods=["POST"])
@validate_request(DeviceCreate)
def create_device():
    """Create a new device."""
    data = request.validated_data

    with DatabaseSession() as db:
        # Check if device with same name already exists
        existing = db.query(Device).filter(Device.name == data.name).first()
        if existing:
            raise ConflictError("Device with this name already exists")

        device = Device(
            name=data.name,
            type=DeviceType(data.type),
            status=DeviceStatus(data.status) if data.status else DeviceStatus.INACTIVE,
            ip_address=data.ip_address,
            mac_address=data.mac_address,
            device_metadata=data.metadata or {},
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        return success_response(device.to_dict(), status_code=201)


@devices_bp.route("/<int:device_id>", methods=["PUT"])
@validate_request(DeviceUpdate)
def update_device(device_id: int):
    """Update a device."""
    data = request.validated_data

    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Update fields (only if provided in request)
        if data.name is not None:
            device.name = data.name
        if data.type is not None:
            device.type = DeviceType(data.type)
        if data.status is not None:
            device.status = DeviceStatus(data.status)
        if data.ip_address is not None:
            device.ip_address = data.ip_address
        if data.mac_address is not None:
            device.mac_address = data.mac_address
        if data.metadata is not None:
            device.device_metadata = data.metadata

        db.commit()
        db.refresh(device)

        return success_response(device.to_dict())


@devices_bp.route("/<int:device_id>", methods=["DELETE"])
def delete_device(device_id: int):
    """Delete a device."""
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        db.delete(device)
        db.commit()

        return success_response(message="Device deleted successfully")


@devices_bp.route("/<int:device_id>/services", methods=["GET"])
def get_device_services(device_id: int):
    """Get all services for a device."""
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        services = [service.to_dict() for service in device.services]
        return success_response(services)


@devices_bp.route("/<int:device_id>/metrics", methods=["GET"])
def get_device_metrics(device_id: int):
    """Get metrics for a device."""
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Get limit from query params, default to 100
        limit = request.args.get("limit", 100, type=int)

        # Get recent metrics from device's relationship
        metrics = device.metrics[-limit:] if device.metrics else []

        return success_response([metric.to_dict() for metric in metrics])
