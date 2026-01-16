"""Workflow models for multi-step automation."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class WorkflowStatus(PyEnum):
    """Workflow instance status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class WorkflowTemplate(Base):
    """Template defining a reusable workflow.

    A workflow is a sequence of automation steps that can have dependencies
    and optional rollback actions.
    """

    __tablename__ = "workflow_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Steps define the workflow structure
    # Format: [{"order": 1, "action_name": "ping", "executor_type": "ansible",
    #           "depends_on": [], "rollback_action": null, "extra_vars": {}}]
    steps = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    instances = relationship(
        "WorkflowInstance", back_populates="template", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        """String representation."""
        return f"<WorkflowTemplate {self.name}>"


class WorkflowInstance(Base):
    """An execution instance of a workflow template.

    Tracks the state of a workflow execution including all jobs
    created for each step.
    """

    __tablename__ = "workflow_instances"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(
        Integer, ForeignKey("workflow_templates.id", ondelete="SET NULL"), nullable=True
    )
    # Store template snapshot in case template is modified/deleted
    template_snapshot = Column(JSON, nullable=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    # Target devices for this workflow execution
    device_ids = Column(JSON, nullable=False)
    # Whether to run rollback actions on failure
    rollback_on_failure = Column(Boolean, default=False)
    # Extra variables passed to all steps
    extra_vars = Column(JSON, nullable=True)
    # Execution timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    # Error message if failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="instances")
    jobs = relationship(
        "AutomationJob",
        back_populates="workflow_instance",
        foreign_keys="AutomationJob.workflow_instance_id",
    )

    def to_dict(self, include_jobs: bool = False):
        """Convert model to dictionary.

        Args:
            include_jobs: Whether to include job details

        Returns:
            Dictionary representation
        """
        result = {
            "id": self.id,
            "template_id": self.template_id,
            "template_name": self.template.name if self.template else None,
            "status": self.status.value if self.status else None,
            "device_ids": self.device_ids,
            "rollback_on_failure": self.rollback_on_failure,
            "extra_vars": self.extra_vars,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_jobs:
            result["jobs"] = [job.to_dict() for job in self.jobs]
        return result

    def __repr__(self):
        """String representation."""
        status_str = self.status.value if self.status else "unknown"
        return f"<WorkflowInstance {self.id} ({status_str})>"
