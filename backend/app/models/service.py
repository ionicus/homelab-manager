"""Service model."""

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ServiceStatus(enum.Enum):
    """Service status enumeration."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class Service(Base):
    """Service running on a device."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    port = Column(Integer, nullable=True)
    protocol = Column(String(50), nullable=True)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.STOPPED)
    health_check_url = Column(String(500), nullable=True)

    # Relationship
    device = relationship("Device", backref="services")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "name": self.name,
            "port": self.port,
            "protocol": self.protocol,
            "status": self.status.value if self.status else None,
            "health_check_url": self.health_check_url,
        }

    def __repr__(self):
        """String representation."""
        return f"<Service {self.name} on device_id={self.device_id}>"
