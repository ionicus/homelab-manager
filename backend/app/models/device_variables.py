"""Device variables model for storing per-device automation defaults."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class DeviceVariables(Base):
    """Store variable defaults for devices, optionally per-playbook.

    Variables are merged in order of precedence (lowest to highest):
    1. Global defaults (from playbook schema)
    2. Device defaults (playbook_name=NULL)
    3. Device playbook-specific overrides (playbook_name set)
    4. User-provided variables at execution time
    """

    __tablename__ = "device_variables"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    # NULL = device-wide defaults, set = playbook-specific overrides
    playbook_name = Column(String(100), nullable=True)
    variables = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure one record per device+playbook combination
    __table_args__ = (
        UniqueConstraint("device_id", "playbook_name", name="uq_device_playbook"),
    )

    # Relationship
    device = relationship("Device", backref="variable_sets")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "playbook_name": self.playbook_name,
            "variables": self.variables,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        """String representation."""
        scope = self.playbook_name or "device-defaults"
        return f"<DeviceVariables device={self.device_id} scope={scope}>"
