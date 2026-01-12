"""Pydantic schemas for ProvisioningTask model."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


class ProvisioningTaskBase(BaseModel):
    """Base schema for ProvisioningTask with common fields."""

    playbook_name: str = Field(..., min_length=1, max_length=100, description="Ansible playbook name")
    status: Optional[str] = Field(default="pending", description="Task status (pending, running, completed, failed)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate task status."""
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class ProvisioningTaskCreate(ProvisioningTaskBase):
    """Schema for creating a new provisioning task."""

    device_id: int = Field(..., description="ID of the device to provision")


class ProvisioningTaskUpdate(BaseModel):
    """Schema for updating a provisioning task."""

    status: Optional[str] = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate task status."""
        if v is None:
            return v
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class ProvisioningTaskResponse(ProvisioningTaskBase):
    """Schema for provisioning task response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    created_at: Optional[datetime] = None
