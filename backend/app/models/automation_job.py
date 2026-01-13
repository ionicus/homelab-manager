"""Automation job model."""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus(enum.Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AutomationJob(Base):
    """Automation job for Ansible playbook execution."""

    __tablename__ = "automation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    playbook_name = Column(String(255), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    log_output = Column(Text, nullable=True)

    # Relationship
    device = relationship("Device", backref="automation_jobs")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "playbook_name": self.playbook_name,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "log_output": self.log_output,
            # For frontend compatibility
            "created_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        """String representation."""
        return f"<AutomationJob {self.id} - {self.status.value if self.status else 'unknown'}>"
