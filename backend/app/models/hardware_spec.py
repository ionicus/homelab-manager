"""Hardware specification model."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class HardwareSpec(Base):
    """Hardware specifications for devices."""

    __tablename__ = "hardware_specs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    cpu_model = Column(String(255), nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    ram_gb = Column(Integer, nullable=True)
    storage_gb = Column(Integer, nullable=True)
    gpu_model = Column(String(255), nullable=True)

    # Relationship
    device = relationship("Device", backref="hardware_spec")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "cpu_model": self.cpu_model,
            "cpu_cores": self.cpu_cores,
            "ram_gb": self.ram_gb,
            "storage_gb": self.storage_gb,
            "gpu_model": self.gpu_model,
        }

    def __repr__(self):
        """String representation."""
        return f"<HardwareSpec device_id={self.device_id}>"
