"""Pydantic schemas for Device model."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class DeviceBase(BaseModel):
    """Base schema for Device with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Device name")
    type: str = Field(..., description="Device type (server, vm, container, network, storage)")
    status: Optional[str] = Field(default="inactive", description="Device status (active, inactive, maintenance)")


class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""

    ip_address: Optional[str] = Field(default=None, description="Primary IP address (legacy field)")
    mac_address: Optional[str] = Field(default=None, description="Primary MAC address (legacy field)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional device metadata")


class DeviceUpdate(BaseModel):
    """Schema for updating an existing device."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    mac_address: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class DeviceResponse(DeviceBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
