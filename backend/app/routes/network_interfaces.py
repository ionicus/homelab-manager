"""Network interface routes with improved error handling and validation."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models import Device, InterfaceStatus, NetworkInterface
from app.schemas.network_interface import (
    NetworkInterfaceCreate,
    NetworkInterfaceUpdate,
)
from app.utils.errors import (
    ConflictError,
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.validation import validate_request
from app.utils.validators import (
    ensure_single_primary,
    promote_primary_after_deletion,
    validate_ip_address,
    validate_mac_address,
)

interfaces_bp = Blueprint("interfaces", __name__)


# ==================== Nested Routes (Device-centric) ====================


@interfaces_bp.route("/devices/<int:device_id>/interfaces", methods=["GET"])
@jwt_required()
def list_device_interfaces(device_id: int):
    """List all interfaces for a device.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
    responses:
      200:
        description: List of network interfaces
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/NetworkInterface'
      404:
        description: Device not found
    """
    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.device_id == device_id)
            .order_by(
                NetworkInterface.is_primary.desc(), NetworkInterface.interface_name
            )
            .all()
        )

        return success_response([iface.to_dict() for iface in interfaces])


@interfaces_bp.route(
    "/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["GET"]
)
@jwt_required()
def get_device_interface(device_id: int, interface_id: int):
    """Get a specific interface for a device.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
        description: Device ID
      - name: interface_id
        in: path
        type: integer
        required: true
        description: Interface ID
    responses:
      200:
        description: Interface details
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/NetworkInterface'
      404:
        description: Interface not found
    """
    with DatabaseSession() as db:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            raise NotFoundError("Interface", interface_id)

        return success_response(interface.to_dict())


@interfaces_bp.route("/devices/<int:device_id>/interfaces", methods=["POST"])
@jwt_required()
@validate_request(NetworkInterfaceCreate)
def create_device_interface(device_id: int):
    """Create a new interface for a device.
    ---
    tags:
      - Network Interfaces
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
          required:
            - interface_name
            - mac_address
          properties:
            interface_name:
              type: string
              example: eth0
            mac_address:
              type: string
              example: "AA:BB:CC:DD:EE:FF"
            ip_address:
              type: string
              example: 192.168.1.10
            subnet_mask:
              type: string
              example: 255.255.255.0
            gateway:
              type: string
              example: 192.168.1.1
            vlan_id:
              type: integer
              example: 100
            is_primary:
              type: boolean
              default: false
            status:
              type: string
              enum: [up, down, disabled]
              default: up
    responses:
      201:
        description: Interface created successfully
      400:
        description: Validation error
      404:
        description: Device not found
      409:
        description: Interface with this MAC address already exists
    """
    data = request.validated_data

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Check if MAC address already exists for this device
        existing = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.device_id == device_id,
                NetworkInterface.mac_address == data.mac_address,
            )
            .first()
        )
        if existing:
            raise ConflictError(
                "Interface with this MAC address already exists for this device"
            )

        # If this is first interface or explicitly set as primary, make it primary
        is_primary = data.is_primary if data.is_primary is not None else False
        interface_count = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.device_id == device_id)
            .count()
        )

        if interface_count == 0:
            is_primary = True  # First interface is always primary

        # If setting as primary, unset other primaries
        if is_primary:
            ensure_single_primary(db, device_id)

        interface = NetworkInterface(
            device_id=device_id,
            interface_name=data.interface_name,
            mac_address=data.mac_address,
            ip_address=data.ip_address,
            subnet_mask=data.subnet_mask,
            gateway=data.gateway,
            vlan_id=data.vlan_id,
            is_primary=is_primary,
            status=InterfaceStatus(data.status) if data.status else InterfaceStatus.UP,
        )

        db.add(interface)
        db.commit()
        db.refresh(interface)

        return success_response(interface.to_dict(), status_code=201)


@interfaces_bp.route(
    "/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["PUT"]
)
@jwt_required()
@validate_request(NetworkInterfaceUpdate)
def update_device_interface(device_id: int, interface_id: int):
    """Update an interface.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: interface_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            interface_name:
              type: string
            mac_address:
              type: string
            ip_address:
              type: string
            subnet_mask:
              type: string
            gateway:
              type: string
            vlan_id:
              type: integer
            is_primary:
              type: boolean
            status:
              type: string
              enum: [up, down, disabled]
    responses:
      200:
        description: Interface updated successfully
      404:
        description: Interface not found
      409:
        description: MAC address conflict
    """
    data = request.validated_data

    with DatabaseSession() as db:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            raise NotFoundError("Interface", interface_id)

        # Check for MAC address conflicts if updating MAC
        if data.mac_address and data.mac_address != interface.mac_address:
            existing = (
                db.query(NetworkInterface)
                .filter(
                    NetworkInterface.device_id == device_id,
                    NetworkInterface.mac_address == data.mac_address,
                    NetworkInterface.id != interface_id,
                )
                .first()
            )
            if existing:
                raise ConflictError(
                    "Interface with this MAC address already exists for this device"
                )

        # Update fields (only if provided)
        if data.interface_name is not None:
            interface.interface_name = data.interface_name
        if data.mac_address is not None:
            interface.mac_address = data.mac_address
        if data.ip_address is not None:
            interface.ip_address = data.ip_address
        if data.subnet_mask is not None:
            interface.subnet_mask = data.subnet_mask
        if data.gateway is not None:
            interface.gateway = data.gateway
        if data.vlan_id is not None:
            interface.vlan_id = data.vlan_id
        if data.status is not None:
            interface.status = InterfaceStatus(data.status)

        # Handle primary flag changes
        if data.is_primary is not None and data.is_primary and not interface.is_primary:
            ensure_single_primary(db, device_id, interface_id)
            interface.is_primary = True

        db.commit()
        db.refresh(interface)

        return success_response(interface.to_dict())


@interfaces_bp.route(
    "/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["DELETE"]
)
@jwt_required()
def delete_device_interface(device_id: int, interface_id: int):
    """Delete an interface.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: interface_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Interface deleted successfully
      400:
        description: Cannot delete the only interface
      404:
        description: Interface not found
    """
    with DatabaseSession() as db:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            raise NotFoundError("Interface", interface_id)

        # Check if this is the only interface
        interface_count = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.device_id == device_id)
            .count()
        )
        if interface_count == 1:
            raise ValidationError(
                "Cannot delete the only interface. "
                "Device must have at least one interface."
            )

        was_primary = interface.is_primary

        db.delete(interface)
        db.commit()

        # If we deleted the primary interface, promote another
        if was_primary:
            promote_primary_after_deletion(db, device_id)
            db.commit()

        return success_response(message="Interface deleted successfully")


@interfaces_bp.route(
    "/devices/<int:device_id>/interfaces/<int:interface_id>/set-primary",
    methods=["PUT"],
)
@jwt_required()
def set_primary_interface(device_id: int, interface_id: int):
    """Set an interface as the primary interface for the device.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: path
        type: integer
        required: true
      - name: interface_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Interface set as primary
      404:
        description: Interface not found
    """
    with DatabaseSession() as db:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            raise NotFoundError("Interface", interface_id)

        if interface.is_primary:
            return success_response(message="Interface is already primary")

        # Unset other primaries and set this one
        ensure_single_primary(db, device_id, interface_id)
        interface.is_primary = True

        db.commit()
        db.refresh(interface)

        return success_response(interface.to_dict())


# ==================== Flat Routes (Global queries) ====================


@interfaces_bp.route("/interfaces", methods=["GET"])
@jwt_required()
def list_all_interfaces():
    """List all interfaces with optional filtering.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: device_id
        in: query
        type: integer
        description: Filter by device ID
      - name: status
        in: query
        type: string
        enum: [up, down, disabled]
        description: Filter by status
      - name: is_primary
        in: query
        type: boolean
        description: Filter by primary status
    responses:
      200:
        description: List of interfaces
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/NetworkInterface'
    """
    with DatabaseSession() as db:
        query = db.query(NetworkInterface)

        # Filter by device_id
        device_id = request.args.get("device_id", type=int)
        if device_id:
            query = query.filter(NetworkInterface.device_id == device_id)

        # Filter by status
        status = request.args.get("status")
        if status:
            try:
                query = query.filter(NetworkInterface.status == InterfaceStatus(status))
            except ValueError:
                raise ValidationError(f"Invalid status value: {status}") from None

        # Filter by is_primary
        is_primary = request.args.get("is_primary")
        if is_primary is not None:
            is_primary_bool = is_primary.lower() in ("true", "1", "yes")
            query = query.filter(NetworkInterface.is_primary == is_primary_bool)

        interfaces = query.order_by(
            NetworkInterface.device_id, NetworkInterface.is_primary.desc()
        ).all()

        return success_response([iface.to_dict() for iface in interfaces])


@interfaces_bp.route("/interfaces/<int:interface_id>", methods=["GET"])
@jwt_required()
def get_interface(interface_id: int):
    """Get a specific interface by ID.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: interface_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Interface details
      404:
        description: Interface not found
    """
    with DatabaseSession() as db:
        interface = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.id == interface_id)
            .first()
        )

        if not interface:
            raise NotFoundError("Interface", interface_id)

        return success_response(interface.to_dict())


@interfaces_bp.route("/interfaces/by-mac/<string:mac_address>", methods=["GET"])
@jwt_required()
def get_interface_by_mac(mac_address: str):
    """Find interfaces by MAC address.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: mac_address
        in: path
        type: string
        required: true
        description: MAC address (XX:XX:XX:XX:XX:XX format)
    responses:
      200:
        description: Interfaces with matching MAC address
      400:
        description: Invalid MAC address format
      404:
        description: No interfaces found
    """
    if not validate_mac_address(mac_address):
        raise ValidationError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")

    with DatabaseSession() as db:
        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.mac_address == mac_address.upper())
            .all()
        )

        if not interfaces:
            raise NotFoundError("Interface with MAC address", mac_address)

        return success_response([iface.to_dict() for iface in interfaces])


@interfaces_bp.route("/interfaces/by-ip/<string:ip_address>", methods=["GET"])
@jwt_required()
def get_interface_by_ip(ip_address: str):
    """Find interfaces by IP address.
    ---
    tags:
      - Network Interfaces
    parameters:
      - name: ip_address
        in: path
        type: string
        required: true
        description: IP address
    responses:
      200:
        description: Interfaces with matching IP address
      400:
        description: Invalid IP address format
      404:
        description: No interfaces found
    """
    if not validate_ip_address(ip_address):
        raise ValidationError("Invalid IP address format")

    with DatabaseSession() as db:
        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.ip_address == ip_address)
            .all()
        )

        if not interfaces:
            raise NotFoundError("Interface with IP address", ip_address)

        return success_response([iface.to_dict() for iface in interfaces])
