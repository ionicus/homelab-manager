"""Pydantic schemas for AutomationJob model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AutomationJobBase(BaseModel):
    """Base schema for AutomationJob with common fields."""

    playbook_name: str = Field(
        ..., min_length=1, max_length=100, description="Ansible playbook name"
    )
    status: Optional[str] = Field(
        default="pending", description="Job status (pending, running, completed, failed)"
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


class AutomationJobResponse(AutomationJobBase):
    """Schema for automation job response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    created_at: Optional[datetime] = None
