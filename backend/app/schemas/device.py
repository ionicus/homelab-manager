"""Pydantic schemas for Device model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    """Base schema for Device with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    type: str = Field(
        ..., description="Device type (server, vm, container, network, storage)"
    )
    status: str | None = Field(
        default="inactive", description="Device status (active, inactive, maintenance)"
    )


class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""

    ip_address: str | None = Field(
        default=None, description="Primary IP address (legacy field)"
    )
    mac_address: str | None = Field(
        default=None, description="Primary MAC address (legacy field)"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional device metadata"
    )


class DeviceUpdate(BaseModel):
    """Schema for updating an existing device."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = Field(default=None)
    status: str | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    mac_address: str | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str | None = None
    mac_address: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DeviceVariablesUpdate(BaseModel):
    """Schema for updating device automation variables."""

    variables: dict[str, Any] = Field(
        ..., description="Key-value pairs for automation variables"
    )


class DeviceVariablesResponse(BaseModel):
    """Schema for device variables response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    playbook_name: str | None = None
    variables: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None
