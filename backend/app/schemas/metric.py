"""Pydantic schemas for Metric model."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetricBase(BaseModel):
    """Base schema for Metric with common fields."""

    cpu_usage: float | None = Field(
        default=None, ge=0, le=100, description="CPU usage percentage (0-100)"
    )
    memory_usage: float | None = Field(
        default=None, ge=0, le=100, description="Memory usage percentage (0-100)"
    )
    disk_usage: float | None = Field(
        default=None, ge=0, le=100, description="Disk usage percentage (0-100)"
    )
    network_rx_bytes: int | None = Field(
        default=None, ge=0, description="Network received bytes"
    )
    network_tx_bytes: int | None = Field(
        default=None, ge=0, description="Network transmitted bytes"
    )

    @field_validator("cpu_usage", "memory_usage", "disk_usage")
    @classmethod
    def validate_percentage(cls, v: float | None) -> float | None:
        """Validate percentage values are within 0-100 range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    @field_validator("network_rx_bytes", "network_tx_bytes")
    @classmethod
    def validate_network_bytes(cls, v: int | None) -> int | None:
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
