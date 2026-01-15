"""Device routes with improved error handling and validation."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models import Device, DeviceStatus, DeviceType, DeviceVariables
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceVariablesUpdate
from app.utils.errors import (
    ConflictError,
    DatabaseSession,
    NotFoundError,
    success_response,
)
from app.utils.pagination import (
    get_pagination_params,
    paginate_query,
    paginated_response,
)
from app.utils.validation import validate_request

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("", methods=["GET"])
@jwt_required()
def list_devices():
    """List devices with pagination.
    ---
    tags:
      - Devices
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Items per page (max 100)
    responses:
      200:
        description: Paginated list of devices
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/Device'
            pagination:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                total_pages:
                  type: integer
    """
    page, per_page = get_pagination_params()

    with DatabaseSession() as db:
        query = db.query(Device).order_by(Device.name)
        devices, total = paginate_query(query, page, per_page)
        return paginated_response(
            [device.to_dict() for device in devices], total, page, per_page
        )


@devices_bp.route("/<int:device_id>", methods=["GET"])
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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

        # Manually cascade delete related records (in case DB constraints aren't set)
        from app.models import (
            AutomationJob,
            HardwareSpec,
            Metric,
            NetworkInterface,
            Service,
        )
        from app.models.device_variables import DeviceVariables

        db.query(AutomationJob).filter(AutomationJob.device_id == device_id).delete(
            synchronize_session=False
        )
        db.query(Service).filter(Service.device_id == device_id).delete(
            synchronize_session=False
        )
        db.query(Metric).filter(Metric.device_id == device_id).delete(
            synchronize_session=False
        )
        db.query(NetworkInterface).filter(
            NetworkInterface.device_id == device_id
        ).delete(synchronize_session=False)
        db.query(HardwareSpec).filter(HardwareSpec.device_id == device_id).delete(
            synchronize_session=False
        )
        db.query(DeviceVariables).filter(DeviceVariables.device_id == device_id).delete(
            synchronize_session=False
        )

        db.delete(device)
        db.commit()

        return success_response(message="Device deleted successfully")


@devices_bp.route("/<int:device_id>/services", methods=["GET"])
@jwt_required()
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
@jwt_required()
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


# ===== Device Variables Endpoints =====


@devices_bp.route("/<int:device_id>/variables", methods=["GET"])
@jwt_required()
def get_device_variables(device_id: int):
    """Get all variable sets for a device.
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
        description: List of variable sets (device defaults + playbook-specific)
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                device_defaults:
                  type: object
                  description: Device-wide default variables
                playbook_overrides:
                  type: object
                  description: Playbook-specific variable overrides
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Get all variable sets for this device
        var_sets = (
            db.query(DeviceVariables)
            .filter(DeviceVariables.device_id == device_id)
            .all()
        )

        # Organize into defaults and playbook-specific
        device_defaults = {}
        playbook_overrides = {}

        for var_set in var_sets:
            if var_set.playbook_name is None:
                device_defaults = var_set.variables or {}
            else:
                playbook_overrides[var_set.playbook_name] = var_set.variables or {}

        return success_response(
            {
                "device_defaults": device_defaults,
                "playbook_overrides": playbook_overrides,
            }
        )


@devices_bp.route("/<int:device_id>/variables", methods=["PUT"])
@jwt_required()
@validate_request(DeviceVariablesUpdate)
def update_device_variables(device_id: int):
    """Update device-wide default variables.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            variables:
              type: object
              description: Key-value variable pairs
    responses:
      200:
        description: Variables updated
      404:
        description: Device not found
    """
    data = request.validated_data

    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Find or create device defaults (playbook_name = NULL)
        var_set = (
            db.query(DeviceVariables)
            .filter(
                DeviceVariables.device_id == device_id,
                DeviceVariables.playbook_name.is_(None),
            )
            .first()
        )

        if var_set:
            var_set.variables = data.variables
        else:
            var_set = DeviceVariables(
                device_id=device_id,
                playbook_name=None,
                variables=data.variables,
            )
            db.add(var_set)

        db.commit()
        db.refresh(var_set)

        return success_response(var_set.to_dict())


@devices_bp.route("/<int:device_id>/variables/<playbook_name>", methods=["GET"])
@jwt_required()
def get_device_playbook_variables(device_id: int, playbook_name: str):
    """Get playbook-specific variable overrides for a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: playbook_name
        in: path
        type: string
        required: true
    responses:
      200:
        description: Playbook-specific variables
      404:
        description: Device or variables not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        var_set = (
            db.query(DeviceVariables)
            .filter(
                DeviceVariables.device_id == device_id,
                DeviceVariables.playbook_name == playbook_name,
            )
            .first()
        )

        if not var_set:
            # Return empty if no overrides exist
            return success_response(
                {
                    "device_id": device_id,
                    "playbook_name": playbook_name,
                    "variables": {},
                }
            )

        return success_response(var_set.to_dict())


@devices_bp.route("/<int:device_id>/variables/<playbook_name>", methods=["PUT"])
@jwt_required()
@validate_request(DeviceVariablesUpdate)
def update_device_playbook_variables(device_id: int, playbook_name: str):
    """Update playbook-specific variable overrides for a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: playbook_name
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            variables:
              type: object
    responses:
      200:
        description: Variables updated
      404:
        description: Device not found
    """
    data = request.validated_data

    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Find or create playbook-specific overrides
        var_set = (
            db.query(DeviceVariables)
            .filter(
                DeviceVariables.device_id == device_id,
                DeviceVariables.playbook_name == playbook_name,
            )
            .first()
        )

        if var_set:
            var_set.variables = data.variables
        else:
            var_set = DeviceVariables(
                device_id=device_id,
                playbook_name=playbook_name,
                variables=data.variables,
            )
            db.add(var_set)

        db.commit()
        db.refresh(var_set)

        return success_response(var_set.to_dict())


@devices_bp.route("/<int:device_id>/variables/<playbook_name>", methods=["DELETE"])
@jwt_required()
def delete_device_playbook_variables(device_id: int, playbook_name: str):
    """Delete playbook-specific variable overrides for a device.
    ---
    tags:
      - Devices
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: playbook_name
        in: path
        type: string
        required: true
    responses:
      200:
        description: Variables deleted
      404:
        description: Device or variables not found
    """
    with DatabaseSession() as db:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        var_set = (
            db.query(DeviceVariables)
            .filter(
                DeviceVariables.device_id == device_id,
                DeviceVariables.playbook_name == playbook_name,
            )
            .first()
        )

        if not var_set:
            raise NotFoundError("Variables", f"{device_id}/{playbook_name}")

        db.delete(var_set)
        db.commit()

        return success_response(message="Variables deleted successfully")
