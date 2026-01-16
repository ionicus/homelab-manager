"""Automation job model."""

import enum

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


class JobStatus(enum.Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    # Multiple device IDs for batch execution (JSON array)
    # When set, the job runs on all devices; device_id is the "primary" for the relationship
    device_ids = Column(JSON, nullable=True)
    executor_type = Column(String(50), nullable=False, default="ansible")
    action_name = Column(String(255), nullable=False)
    action_config = Column(JSON, nullable=True)
    extra_vars = Column(
        JSON, nullable=True
    )  # Extra variables for executor (e.g., Ansible extra-vars)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    log_output = Column(Text, nullable=True)

    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100 percentage
    task_count = Column(Integer, default=0)  # Total tasks in playbook
    tasks_completed = Column(Integer, default=0)  # Tasks finished so far

    # Error categorization
    error_category = Column(String(50), nullable=True)  # connectivity, permission, etc.

    # Cancellation support
    cancel_requested = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)

    # Celery task tracking
    celery_task_id = Column(String(255), nullable=True)

    # Vault secret for ansible-vault encrypted content
    vault_secret_id = Column(Integer, ForeignKey("vault_secrets.id"), nullable=True)

    # Workflow integration
    workflow_instance_id = Column(
        Integer, ForeignKey("workflow_instances.id", ondelete="SET NULL"), nullable=True
    )
    step_order = Column(Integer, nullable=True)  # Order within workflow
    depends_on_job_ids = Column(JSON, nullable=True)  # Job IDs this depends on
    is_rollback = Column(Boolean, default=False)  # Whether this is a rollback action

    # Relationships
    device = relationship("Device", backref="automation_jobs")
    vault_secret = relationship("VaultSecret")
    workflow_instance = relationship(
        "WorkflowInstance",
        back_populates="jobs",
        foreign_keys=[workflow_instance_id],
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "device_ids": self.device_ids,
            "executor_type": self.executor_type,
            "action_name": self.action_name,
            "action_config": self.action_config,
            "extra_vars": self.extra_vars,
            "status": self.status.value if self.status else None,
            "started_at": (self.started_at.isoformat() if self.started_at else None),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "log_output": self.log_output,
            # Progress tracking
            "progress": self.progress,
            "task_count": self.task_count,
            "tasks_completed": self.tasks_completed,
            # Error info
            "error_category": self.error_category,
            # Cancellation
            "cancel_requested": self.cancel_requested,
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
            # Celery tracking
            "celery_task_id": self.celery_task_id,
            # Vault
            "vault_secret_id": self.vault_secret_id,
            # Workflow
            "workflow_instance_id": self.workflow_instance_id,
            "step_order": self.step_order,
            "depends_on_job_ids": self.depends_on_job_ids,
            "is_rollback": self.is_rollback,
        }

    def __repr__(self):
        """String representation."""
        status_str = self.status.value if self.status else "unknown"
        return f"<AutomationJob {self.id} ({self.executor_type}) - {status_str}>"
