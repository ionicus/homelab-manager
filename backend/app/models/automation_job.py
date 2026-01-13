"""Automation job model."""

import enum

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus(enum.Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AutomationJob(Base):
    """Automation job for executing automation actions.

    Supports multiple executor backends (Ansible, SSH, etc.) via the
    executor_type field.
    """

    __tablename__ = "automation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    executor_type = Column(String(50), nullable=False, default="ansible")
    action_name = Column(String(255), nullable=False)
    action_config = Column(JSON, nullable=True)
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
            "executor_type": self.executor_type,
            "action_name": self.action_name,
            "action_config": self.action_config,
            # Backwards compatibility: keep playbook_name for frontend
            "playbook_name": self.action_name,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "log_output": self.log_output,
            # For frontend compatibility
            "created_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        """String representation."""
        status_str = self.status.value if self.status else "unknown"
        return f"<AutomationJob {self.id} ({self.executor_type}) - {status_str}>"
