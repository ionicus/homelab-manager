"""Validation utilities for network interfaces."""

import re
import ipaddress
from typing import Optional


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address format.

    Accepts format: XX:XX:XX:XX:XX:XX (case-insensitive)

    Args:
        mac: MAC address string

    Returns:
        True if valid, False otherwise
    """
    if not mac:
        return False

    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    return bool(re.match(pattern, mac))


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address (IPv4 or IPv6).

    Args:
        ip: IP address string

    Returns:
        True if valid IPv4 or IPv6, False otherwise
    """
    if not ip:
        return False

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_vlan_id(vlan_id: Optional[int]) -> bool:
    """
    Validate VLAN ID.

    Valid range: 1-4094 (0 and 4095 are reserved)

    Args:
        vlan_id: VLAN ID integer or None

    Returns:
        True if valid or None, False otherwise
    """
    if vlan_id is None:
        return True

    if not isinstance(vlan_id, int):
        return False

    return 1 <= vlan_id <= 4094


def ensure_single_primary(db, device_id: int, new_primary_id: Optional[int] = None):
    """
    Ensure only one primary interface per device.

    When setting a new primary interface, unsets all other interfaces
    for that device as non-primary.

    Args:
        db: Database session
        device_id: Device ID
        new_primary_id: ID of interface being set as primary (optional)
    """
    from app.models import NetworkInterface

    # Unset all other primary interfaces for this device
    interfaces = db.query(NetworkInterface).filter(
        NetworkInterface.device_id == device_id,
        NetworkInterface.is_primary == True
    )

    # If new_primary_id specified, exclude it from the unset operation
    if new_primary_id:
        interfaces = interfaces.filter(NetworkInterface.id != new_primary_id)

    interfaces.update({"is_primary": False})


def promote_primary_after_deletion(db, device_id: int):
    """
    Auto-promote another interface to primary after primary deletion.

    Called when a primary interface is deleted to ensure the device
    still has a primary interface (if any interfaces remain).

    Args:
        db: Database session
        device_id: Device ID
    """
    from app.models import NetworkInterface

    # Find any remaining interface for this device
    interface = db.query(NetworkInterface).filter(
        NetworkInterface.device_id == device_id
    ).first()

    if interface:
        interface.is_primary = True
