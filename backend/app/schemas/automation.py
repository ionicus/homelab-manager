"""Pydantic schemas for AutomationJob model."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate job status."""
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class AutomationJobCreate(AutomationJobBase):
    """Schema for creating a new automation job."""

    device_id: int = Field(..., description="ID of the device to run automation on")


class AutomationJobUpdate(BaseModel):
    """Schema for updating an automation job."""

    status: Optional[str] = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate job status."""
        if v is None:
            return v
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class AutomationJobResponse(BaseModel):
    """Schema for automation job response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    executor_type: str
    action_name: str
    action_config: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
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
