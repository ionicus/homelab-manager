"""Device model."""

import enum
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String

from app.database import Base


class DeviceType(enum.Enum):
    """Device type enumeration."""

    SERVER = "server"
    VM = "vm"
    CONTAINER = "container"
    NETWORK = "network"
    STORAGE = "storage"


class DeviceStatus(enum.Enum):
    """Device status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class Device(Base):
    """Device model representing physical or virtual systems."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(Enum(DeviceType), nullable=False)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.ACTIVE)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    mac_address = Column(String(17), nullable=True)
    device_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self):
        """Convert model to dictionary."""
        # Compute primary interface values for backward compatibility
        primary_interface = None
        if hasattr(self, "network_interfaces"):
            primary_interface = next(
                (ni for ni in self.network_interfaces if ni.is_primary), None
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            # Backward compatibility: prefer primary interface, fall back to old fields
            "ip_address": (
                primary_interface.ip_address if primary_interface else self.ip_address
            ),
            "mac_address": (
                primary_interface.mac_address if primary_interface else self.mac_address
            ),
            "metadata": self.device_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        """String representation."""
        return f"<Device {self.name} ({self.type.value if self.type else 'unknown'})>"
