"""Pydantic schemas for request and response validation."""

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
)
from app.schemas.network_interface import (
    NetworkInterfaceCreate,
    NetworkInterfaceUpdate,
    NetworkInterfaceResponse,
)
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceStatusUpdate,
)
from app.schemas.metric import (
    MetricCreate,
    MetricResponse,
)
from app.schemas.automation import (
    AutomationJobCreate,
    AutomationJobResponse,
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
