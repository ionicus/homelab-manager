"""Device routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import Device, DeviceStatus, DeviceType
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.utils.errors import (
    ConflictError,
    DatabaseSession,
    NotFoundError,
    success_response,
)
from app.utils.validation import validate_request

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("", methods=["GET"])
def list_devices():
    """List all devices.
    ---
    tags:
      - Devices
    responses:
      200:
        description: List of all devices
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/Device'
    """
    with DatabaseSession() as db:
        devices = db.query(Device).all()
        return success_response([device.to_dict() for device in devices])


@devices_bp.route("/<int:device_id>", methods=["GET"])
def get_device(device_id: int):
    """Get a specific device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
    responses:
      200:
        description: Device details
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/Device'
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)
        return success_response(device.to_dict())


@devices_bp.route("", methods=["POST"])
@validate_request(DeviceCreate)
def create_device():
    """Create a new device.
    ---
    tags:
      - Devices
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - type
          properties:
            name:
              type: string
              description: Unique device name
              example: server-01
            type:
              type: string
              enum: [server, vm, container, network, storage]
              description: Device type
              example: server
            status:
              type: string
              enum: [active, inactive, maintenance]
              description: Device status
              example: active
            ip_address:
              type: string
              description: Primary IP address
              example: 192.168.1.10
            mac_address:
              type: string
              description: Primary MAC address
              example: "AA:BB:CC:DD:EE:FF"
            metadata:
              type: object
              description: Additional key-value metadata
    responses:
      201:
        description: Device created successfully
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/Device'
      400:
        description: Validation error
      409:
        description: Device with this name already exists
    """
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
    """Update a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Device name
            type:
              type: string
              enum: [server, vm, container, network, storage]
            status:
              type: string
              enum: [active, inactive, maintenance]
            ip_address:
              type: string
            mac_address:
              type: string
            metadata:
              type: object
    responses:
      200:
        description: Device updated successfully
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/Device'
      404:
        description: Device not found
      400:
        description: Validation error
    """
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
    """Delete a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
    responses:
      200:
        description: Device deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Device deleted successfully
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        db.delete(device)
        db.commit()

        return success_response(message="Device deleted successfully")


@devices_bp.route("/<int:device_id>/services", methods=["GET"])
def get_device_services(device_id: int):
    """Get all services for a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
    responses:
      200:
        description: List of services running on the device
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/Service'
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        services = [service.to_dict() for service in device.services]
        return success_response(services)


@devices_bp.route("/<int:device_id>/metrics", methods=["GET"])
def get_device_metrics(device_id: int):
    """Get metrics for a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
      - name: limit
        in: query
        type: integer
        default: 100
        description: Maximum number of metrics to return
    responses:
      200:
        description: List of device metrics
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/Metric'
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Get limit from query params, default to 100
        limit = request.args.get("limit", 100, type=int)

        # Get recent metrics from device's relationship
        metrics = device.metrics[-limit:] if device.metrics else []

        return success_response([metric.to_dict() for metric in metrics])
