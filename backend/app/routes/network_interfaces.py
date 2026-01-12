"""Network interface routes."""

from flask import Blueprint, request, jsonify

from app.database import Session
from app.models import NetworkInterface, InterfaceStatus, Device
from app.utils.validators import (
    validate_mac_address,
    validate_ip_address,
    validate_vlan_id,
    ensure_single_primary,
    promote_primary_after_deletion,
)

interfaces_bp = Blueprint("interfaces", __name__)


# ==================== Nested Routes (Device-centric) ====================


@interfaces_bp.route("/devices/<int:device_id>/interfaces", methods=["GET"])
def list_device_interfaces(device_id: int):
    """List all interfaces for a device."""
    db = Session()
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.device_id == device_id)
            .order_by(NetworkInterface.is_primary.desc(), NetworkInterface.interface_name)
            .all()
        )

        return jsonify([iface.to_dict() for iface in interfaces]), 200
    finally:
        db.close()


@interfaces_bp.route("/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["GET"])
def get_device_interface(device_id: int, interface_id: int):
    """Get a specific interface for a device."""
    db = Session()
    try:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            return jsonify({"error": "Interface not found"}), 404

        return jsonify(interface.to_dict()), 200
    finally:
        db.close()


@interfaces_bp.route("/devices/<int:device_id>/interfaces", methods=["POST"])
def create_device_interface(device_id: int):
    """Create a new interface for a device."""
    data = request.get_json()

    if not data or "interface_name" not in data or "mac_address" not in data:
        return jsonify({"error": "Missing required fields: interface_name, mac_address"}), 400

    # Validate MAC address
    if not validate_mac_address(data["mac_address"]):
        return jsonify({"error": "Invalid MAC address format. Use XX:XX:XX:XX:XX:XX"}), 400

    # Validate IP address if provided
    if data.get("ip_address") and not validate_ip_address(data["ip_address"]):
        return jsonify({"error": "Invalid IP address format"}), 400

    # Validate VLAN ID if provided
    if not validate_vlan_id(data.get("vlan_id")):
        return jsonify({"error": "Invalid VLAN ID. Must be between 1 and 4094"}), 400

    db = Session()
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Check if MAC address already exists for this device
        existing = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.device_id == device_id,
                NetworkInterface.mac_address == data["mac_address"],
            )
            .first()
        )
        if existing:
            return jsonify({"error": "Interface with this MAC address already exists for this device"}), 409

        # If this is first interface or explicitly set as primary, make it primary
        is_primary = data.get("is_primary", False)
        interface_count = db.query(NetworkInterface).filter(NetworkInterface.device_id == device_id).count()

        if interface_count == 0:
            is_primary = True  # First interface is always primary

        # If setting as primary, unset other primaries
        if is_primary:
            ensure_single_primary(db, device_id)

        interface = NetworkInterface(
            device_id=device_id,
            interface_name=data["interface_name"],
            mac_address=data["mac_address"],
            ip_address=data.get("ip_address"),
            subnet_mask=data.get("subnet_mask"),
            gateway=data.get("gateway"),
            vlan_id=data.get("vlan_id"),
            is_primary=is_primary,
            status=InterfaceStatus(data.get("status", "up")),
        )

        db.add(interface)
        db.commit()
        db.refresh(interface)

        return jsonify(interface.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {str(e)}"}), 400
    finally:
        db.close()


@interfaces_bp.route("/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["PUT"])
def update_device_interface(device_id: int, interface_id: int):
    """Update an interface."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate MAC address if provided
    if "mac_address" in data and not validate_mac_address(data["mac_address"]):
        return jsonify({"error": "Invalid MAC address format. Use XX:XX:XX:XX:XX:XX"}), 400

    # Validate IP address if provided
    if data.get("ip_address") and not validate_ip_address(data["ip_address"]):
        return jsonify({"error": "Invalid IP address format"}), 400

    # Validate VLAN ID if provided
    if "vlan_id" in data and not validate_vlan_id(data["vlan_id"]):
        return jsonify({"error": "Invalid VLAN ID. Must be between 1 and 4094"}), 400

    db = Session()
    try:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            return jsonify({"error": "Interface not found"}), 404

        # Check for MAC address conflicts if updating MAC
        if "mac_address" in data and data["mac_address"] != interface.mac_address:
            existing = (
                db.query(NetworkInterface)
                .filter(
                    NetworkInterface.device_id == device_id,
                    NetworkInterface.mac_address == data["mac_address"],
                    NetworkInterface.id != interface_id,
                )
                .first()
            )
            if existing:
                return jsonify({"error": "Interface with this MAC address already exists for this device"}), 409

        # Update fields
        if "interface_name" in data:
            interface.interface_name = data["interface_name"]
        if "mac_address" in data:
            interface.mac_address = data["mac_address"]
        if "ip_address" in data:
            interface.ip_address = data["ip_address"]
        if "subnet_mask" in data:
            interface.subnet_mask = data["subnet_mask"]
        if "gateway" in data:
            interface.gateway = data["gateway"]
        if "vlan_id" in data:
            interface.vlan_id = data["vlan_id"]
        if "status" in data:
            interface.status = InterfaceStatus(data["status"])

        # Handle primary flag changes
        if "is_primary" in data and data["is_primary"] and not interface.is_primary:
            ensure_single_primary(db, device_id, interface_id)
            interface.is_primary = True

        db.commit()
        db.refresh(interface)

        return jsonify(interface.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": f"Invalid enum value: {str(e)}"}), 400
    finally:
        db.close()


@interfaces_bp.route("/devices/<int:device_id>/interfaces/<int:interface_id>", methods=["DELETE"])
def delete_device_interface(device_id: int, interface_id: int):
    """Delete an interface."""
    db = Session()
    try:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            return jsonify({"error": "Interface not found"}), 404

        # Check if this is the only interface
        interface_count = db.query(NetworkInterface).filter(NetworkInterface.device_id == device_id).count()
        if interface_count == 1:
            return jsonify({"error": "Cannot delete the only interface. Device must have at least one interface."}), 400

        was_primary = interface.is_primary

        db.delete(interface)
        db.commit()

        # If we deleted the primary interface, promote another
        if was_primary:
            promote_primary_after_deletion(db, device_id)
            db.commit()

        return jsonify({"message": "Interface deleted successfully"}), 200
    finally:
        db.close()


@interfaces_bp.route("/devices/<int:device_id>/interfaces/<int:interface_id>/set-primary", methods=["PUT"])
def set_primary_interface(device_id: int, interface_id: int):
    """Set an interface as the primary interface for the device."""
    db = Session()
    try:
        interface = (
            db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.device_id == device_id,
            )
            .first()
        )

        if not interface:
            return jsonify({"error": "Interface not found"}), 404

        if interface.is_primary:
            return jsonify({"message": "Interface is already primary"}), 200

        # Unset other primaries and set this one
        ensure_single_primary(db, device_id, interface_id)
        interface.is_primary = True

        db.commit()
        db.refresh(interface)

        return jsonify(interface.to_dict()), 200
    finally:
        db.close()


# ==================== Flat Routes (Global queries) ====================


@interfaces_bp.route("/interfaces", methods=["GET"])
def list_all_interfaces():
    """List all interfaces with optional filtering."""
    db = Session()
    try:
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
                return jsonify({"error": f"Invalid status value: {status}"}), 400

        # Filter by is_primary
        is_primary = request.args.get("is_primary")
        if is_primary is not None:
            is_primary_bool = is_primary.lower() in ("true", "1", "yes")
            query = query.filter(NetworkInterface.is_primary == is_primary_bool)

        interfaces = query.order_by(NetworkInterface.device_id, NetworkInterface.is_primary.desc()).all()

        return jsonify([iface.to_dict() for iface in interfaces]), 200
    finally:
        db.close()


@interfaces_bp.route("/interfaces/<int:interface_id>", methods=["GET"])
def get_interface(interface_id: int):
    """Get a specific interface by ID."""
    db = Session()
    try:
        interface = db.query(NetworkInterface).filter(NetworkInterface.id == interface_id).first()

        if not interface:
            return jsonify({"error": "Interface not found"}), 404

        return jsonify(interface.to_dict()), 200
    finally:
        db.close()


@interfaces_bp.route("/interfaces/by-mac/<string:mac_address>", methods=["GET"])
def get_interface_by_mac(mac_address: str):
    """Find interfaces by MAC address."""
    if not validate_mac_address(mac_address):
        return jsonify({"error": "Invalid MAC address format. Use XX:XX:XX:XX:XX:XX"}), 400

    db = Session()
    try:
        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.mac_address == mac_address.upper())
            .all()
        )

        if not interfaces:
            return jsonify({"error": "No interfaces found with this MAC address"}), 404

        return jsonify([iface.to_dict() for iface in interfaces]), 200
    finally:
        db.close()


@interfaces_bp.route("/interfaces/by-ip/<string:ip_address>", methods=["GET"])
def get_interface_by_ip(ip_address: str):
    """Find interfaces by IP address."""
    if not validate_ip_address(ip_address):
        return jsonify({"error": "Invalid IP address format"}), 400

    db = Session()
    try:
        interfaces = (
            db.query(NetworkInterface)
            .filter(NetworkInterface.ip_address == ip_address)
            .all()
        )

        if not interfaces:
            return jsonify({"error": "No interfaces found with this IP address"}), 404

        return jsonify([iface.to_dict() for iface in interfaces]), 200
    finally:
        db.close()
