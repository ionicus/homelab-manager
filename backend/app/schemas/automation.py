"""Pydantic schemas for AutomationJob model."""

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Valid job statuses
VALID_STATUSES = ["pending", "running", "completed", "failed", "cancelled"]

# Pattern for safe action names: alphanumeric, underscore, hyphen only
SAFE_ACTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class AutomationJobBase(BaseModel):
    """Base schema for AutomationJob with common fields."""

    executor_type: str = Field(
        default="ansible",
        min_length=1,
        max_length=50,
        description="Executor type (ansible, ssh, etc.)",
    )
    action_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Action to execute",
    )
    action_config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Action-specific configuration",
    )
    status: Optional[str] = Field(
        default="pending",
        description="Job status (pending, running, completed, failed)",
    )

    @field_validator("action_name")
    @classmethod
    def validate_action_name(cls, v: str) -> str:
        """Validate action name contains only safe characters.

        Prevents path traversal and injection attacks.
        """
        if not SAFE_ACTION_NAME_PATTERN.match(v):
            raise ValueError(
                "Action name must contain only letters, numbers, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate job status."""
        if v.lower() not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v.lower()


class AutomationJobCreate(AutomationJobBase):
    """Schema for creating a new automation job."""

    device_id: Optional[int] = Field(
        default=None, description="ID of the device to run automation on"
    )
    device_ids: Optional[list[int]] = Field(
        default=None, description="IDs of multiple devices for batch execution"
    )
    extra_vars: Optional[dict[str, Any]] = Field(
        default=None, description="Extra variables to pass to the executor (e.g., Ansible extra-vars)"
    )

    @model_validator(mode="after")
    def validate_device_ids(self) -> "AutomationJobCreate":
        """Ensure at least one device ID is provided."""
        if self.device_id is None and (self.device_ids is None or len(self.device_ids) == 0):
            raise ValueError("Either device_id or device_ids must be provided")
        return self


class AutomationJobUpdate(BaseModel):
    """Schema for updating an automation job."""

    status: Optional[str] = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate job status."""
        if v is None:
            return v
        if v.lower() not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v.lower()


class AutomationJobResponse(BaseModel):
    """Schema for automation job response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    executor_type: str
    action_name: str
    action_config: Optional[dict[str, Any]] = None
    extra_vars: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    progress: int = 0
    task_count: int = 0
    tasks_completed: int = 0
    error_category: Optional[str] = None
    cancel_requested: bool = False
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    log_output: Optional[str] = None


class ExecutorInfo(BaseModel):
    """Schema for executor type information."""

    type: str = Field(..., description="Executor type identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Executor description")


class ActionInfo(BaseModel):
    """Schema for action information."""

    name: str = Field(..., description="Action identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Action description")
    config_schema: Optional[dict[str, Any]] = Field(
        default=None, description="JSON Schema for action config"
    )
