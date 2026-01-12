#!/usr/bin/env python3
"""Helper script to manage test data in the database.

Usage:
    python scripts/manage_test_data.py flush    # Delete all TEST_ prefixed devices
    python scripts/manage_test_data.py create   # Create sample test data
    python scripts/manage_test_data.py reset    # Flush and create fresh test data
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Session
from app.models import Device, DeviceType, DeviceStatus


def flush_test_data():
    """Delete all devices with names starting with TEST_."""
    db = Session()
    try:
        deleted = db.query(Device).filter(Device.name.like("TEST_%")).delete(synchronize_session=False)
        db.commit()
        print(f"✓ Deleted {deleted} test devices")
    finally:
        db.close()


def create_test_data():
    """Create sample test devices."""
    db = Session()
    try:
        test_devices = [
            Device(
                name="TEST_server-01",
                type=DeviceType.SERVER,
                status=DeviceStatus.ACTIVE,
                ip_address="192.168.1.100",
                mac_address="00:11:22:33:44:55",
                device_metadata={"location": "rack-1", "datacenter": "homelab", "purpose": "testing"},
            ),
            Device(
                name="TEST_docker-vm",
                type=DeviceType.VM,
                status=DeviceStatus.ACTIVE,
                ip_address="192.168.1.101",
                device_metadata={"hypervisor": "proxmox", "cores": 4, "ram_gb": 8},
            ),
            Device(
                name="TEST_nginx-container",
                type=DeviceType.CONTAINER,
                status=DeviceStatus.ACTIVE,
                ip_address="172.17.0.2",
                device_metadata={"image": "nginx:latest", "port": 80},
            ),
            Device(
                name="TEST_main-switch",
                type=DeviceType.NETWORK,
                status=DeviceStatus.ACTIVE,
                ip_address="192.168.1.1",
                mac_address="AA:BB:CC:DD:EE:FF",
                device_metadata={"model": "UniFi Switch 24", "ports": 24},
            ),
        ]

        for device in test_devices:
            db.add(device)

        db.commit()
        print(f"✓ Created {len(test_devices)} test devices")

        for device in test_devices:
            db.refresh(device)
            print(f"  - {device.name} (ID: {device.id}, Type: {device.type.value})")

    finally:
        db.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/manage_test_data.py [flush|create|reset]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "flush":
        flush_test_data()
    elif command == "create":
        create_test_data()
    elif command == "reset":
        print("Resetting test data...")
        flush_test_data()
        create_test_data()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: flush, create, reset")
        sys.exit(1)


if __name__ == "__main__":
    main()
