"""Pydantic schemas for Service model."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceBase(BaseModel):
    """Base schema for Service with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    port: int | None = Field(
        default=None, ge=1, le=65535, description="Service port (1-65535)"
    )
    protocol: str | None = Field(
        default=None,
        max_length=50,
        description="Service protocol (http, https, tcp, etc.)",
    )
    status: str | None = Field(
        default="stopped", description="Service status (running, stopped, error)"
    )
    health_check_url: str | None = Field(
        default=None, max_length=500, description="Health check endpoint URL"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate service status."""
        valid_statuses = ["running", "stopped", "error"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class ServiceCreate(ServiceBase):
    """Schema for creating a new service."""

    device_id: int = Field(..., description="ID of the device running this service")


class ServiceUpdate(BaseModel):
    """Schema for updating an existing service."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    protocol: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None)
    health_check_url: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate service status."""
        if v is None:
            return v
        valid_statuses = ["running", "stopped", "error"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class ServiceResponse(ServiceBase):
    """Schema for service response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int


class ServiceStatusUpdate(BaseModel):
    """Schema for updating only service status."""

    status: str = Field(..., description="Service status (running, stopped, error)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate service status."""
        valid_statuses = ["running", "stopped", "error"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()
