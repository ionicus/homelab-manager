"""Pydantic schemas for Metric model."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


class MetricBase(BaseModel):
    """Base schema for Metric with common fields."""

    cpu_usage: Optional[float] = Field(default=None, ge=0, le=100, description="CPU usage percentage (0-100)")
    memory_usage: Optional[float] = Field(default=None, ge=0, le=100, description="Memory usage percentage (0-100)")
    disk_usage: Optional[float] = Field(default=None, ge=0, le=100, description="Disk usage percentage (0-100)")
    network_rx_bytes: Optional[int] = Field(default=None, ge=0, description="Network received bytes")
    network_tx_bytes: Optional[int] = Field(default=None, ge=0, description="Network transmitted bytes")

    @field_validator("cpu_usage", "memory_usage", "disk_usage")
    @classmethod
    def validate_percentage(cls, v: Optional[float]) -> Optional[float]:
        """Validate percentage values are within 0-100 range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    @field_validator("network_rx_bytes", "network_tx_bytes")
    @classmethod
    def validate_network_bytes(cls, v: Optional[int]) -> Optional[int]:
        """Validate network bytes are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Network bytes must be non-negative")
        return v


class MetricCreate(MetricBase):
    """Schema for creating a new metric."""

    device_id: int = Field(..., description="ID of the device this metric belongs to")


class MetricResponse(MetricBase):
    """Schema for metric response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    timestamp: datetime
