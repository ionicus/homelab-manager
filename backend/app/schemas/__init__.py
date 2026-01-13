"""Pydantic schemas for request and response validation."""

from app.schemas.automation import (
    AutomationJobCreate,
    AutomationJobResponse,
)
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
)
from app.schemas.metric import (
    MetricCreate,
    MetricResponse,
)
from app.schemas.network_interface import (
    NetworkInterfaceCreate,
    NetworkInterfaceResponse,
    NetworkInterfaceUpdate,
)
from app.schemas.service import (
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

__all__ = [
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "NetworkInterfaceCreate",
    "NetworkInterfaceUpdate",
    "NetworkInterfaceResponse",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "MetricCreate",
    "MetricResponse",
    "AutomationJobCreate",
    "AutomationJobResponse",
]
