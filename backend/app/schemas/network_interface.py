"""Pydantic schemas for NetworkInterface model."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re
import ipaddress


class NetworkInterfaceBase(BaseModel):
    """Base schema for NetworkInterface with common fields."""

    interface_name: str = Field(..., min_length=1, max_length=50, description="Interface name (e.g., eth0)")
    mac_address: str = Field(..., pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", description="MAC address")
    ip_address: Optional[str] = Field(default=None, description="IP address (IPv4 or IPv6)")
    subnet_mask: Optional[str] = Field(default=None, description="Subnet mask")
    gateway: Optional[str] = Field(default=None, description="Gateway IP address")
    vlan_id: Optional[int] = Field(default=None, ge=1, le=4094, description="VLAN ID (1-4094)")
    status: Optional[str] = Field(default="up", description="Interface status (up, down, disabled)")
    is_primary: Optional[bool] = Field(default=False, description="Whether this is the primary interface")

    @field_validator("mac_address")
    @classmethod
    def validate_mac_format(cls, v: str) -> str:
        """Validate MAC address format."""
        pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
        return v.upper()

    @field_validator("ip_address", "gateway", "subnet_mask")
    @classmethod
    def validate_ip_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format."""
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate interface status."""
        valid_statuses = ["up", "down", "disabled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class NetworkInterfaceCreate(NetworkInterfaceBase):
    """Schema for creating a new network interface."""
    pass


class NetworkInterfaceUpdate(BaseModel):
    """Schema for updating an existing network interface."""

    interface_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    mac_address: Optional[str] = Field(default=None, pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
    ip_address: Optional[str] = Field(default=None)
    subnet_mask: Optional[str] = Field(default=None)
    gateway: Optional[str] = Field(default=None)
    vlan_id: Optional[int] = Field(default=None, ge=1, le=4094)
    status: Optional[str] = Field(default=None)
    is_primary: Optional[bool] = Field(default=None)

    @field_validator("mac_address")
    @classmethod
    def validate_mac_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate MAC address format."""
        if v is None:
            return v
        pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
        return v.upper()

    @field_validator("ip_address", "gateway", "subnet_mask")
    @classmethod
    def validate_ip_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format."""
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate interface status."""
        if v is None:
            return v
        valid_statuses = ["up", "down", "disabled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class NetworkInterfaceResponse(NetworkInterfaceBase):
    """Schema for network interface response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
