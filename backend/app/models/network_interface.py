"""Network Interface model."""

import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class InterfaceStatus(enum.Enum):
    """Network interface status enumeration."""

    UP = "up"
    DOWN = "down"
    DISABLED = "disabled"


class NetworkInterface(Base):
    """Network interface on a device."""

    __tablename__ = "network_interfaces"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    interface_name = Column(String(50), nullable=False)  # e.g., eth0, ens18, wlan0
    mac_address = Column(String(17), nullable=False, index=True)  # Format: 00:11:22:33:44:55
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 compatible
    subnet_mask = Column(String(45), nullable=True)  # e.g., 255.255.255.0 or /24
    gateway = Column(String(45), nullable=True)
    vlan_id = Column(Integer, nullable=True)  # VLAN tag
    is_primary = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(Enum(InterfaceStatus), default=InterfaceStatus.UP)

    # Relationship
    device = relationship("Device", backref="network_interfaces")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "interface_name": self.interface_name,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "gateway": self.gateway,
            "vlan_id": self.vlan_id,
            "is_primary": self.is_primary,
            "status": self.status.value if self.status else None,
        }

    def __repr__(self):
        """String representation."""
        return f"<NetworkInterface {self.interface_name} on device_id={self.device_id}>"
