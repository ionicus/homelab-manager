"""Database models."""

from app.models.device import Device, DeviceType, DeviceStatus
from app.models.hardware_spec import HardwareSpec
from app.models.service import Service, ServiceStatus
from app.models.metric import Metric
from app.models.automation_job import AutomationJob, JobStatus
from app.models.network_interface import NetworkInterface, InterfaceStatus

__all__ = [
    "Device",
    "DeviceType",
    "DeviceStatus",
    "HardwareSpec",
    "Service",
    "ServiceStatus",
    "Metric",
    "AutomationJob",
    "JobStatus",
    "NetworkInterface",
    "InterfaceStatus",
]
