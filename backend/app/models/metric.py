"""Metric model."""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class Metric(Base):
    """System metrics for devices."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    cpu_usage = Column(Float, nullable=True)  # Percentage
    memory_usage = Column(Float, nullable=True)  # Percentage
    disk_usage = Column(Float, nullable=True)  # Percentage
    network_rx_bytes = Column(BigInteger, nullable=True)
    network_tx_bytes = Column(BigInteger, nullable=True)

    # Relationship
    device = relationship("Device", backref="metrics")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "network_rx_bytes": self.network_rx_bytes,
            "network_tx_bytes": self.network_tx_bytes,
        }

    def __repr__(self):
        """String representation."""
        return f"<Metric device_id={self.device_id} at {self.timestamp}>"
