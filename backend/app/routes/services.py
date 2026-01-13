"""Service routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import Device, Service, ServiceStatus
from app.schemas.service import ServiceCreate, ServiceStatusUpdate, ServiceUpdate
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    success_response,
)
from app.utils.validation import validate_request

services_bp = Blueprint("services", __name__)


@services_bp.route("", methods=["GET"])
def list_services():
    """List all services."""
    with DatabaseSession() as db:
        services = db.query(Service).all()
        return success_response([service.to_dict() for service in services])


@services_bp.route("/<int:service_id>", methods=["GET"])
def get_service(service_id: int):
    """Get a specific service."""
    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)
        return success_response(service.to_dict())


@services_bp.route("", methods=["POST"])
@validate_request(ServiceCreate)
def create_service():
    """Create a new service."""
    data = request.validated_data

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise NotFoundError("Device", data.device_id)

        service = Service(
            device_id=data.device_id,
            name=data.name,
            port=data.port,
            protocol=data.protocol,
            status=ServiceStatus(data.status) if data.status else ServiceStatus.STOPPED,
            health_check_url=data.health_check_url,
        )

        db.add(service)
        db.commit()
        db.refresh(service)

        return success_response(service.to_dict(), status_code=201)


@services_bp.route("/<int:service_id>", methods=["PUT"])
@validate_request(ServiceUpdate)
def update_service(service_id: int):
    """Update a service."""
    data = request.validated_data

    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)

        # Update fields (only if provided in request)
        if data.name is not None:
            service.name = data.name
        if data.port is not None:
            service.port = data.port
        if data.protocol is not None:
            service.protocol = data.protocol
        if data.status is not None:
            service.status = ServiceStatus(data.status)
        if data.health_check_url is not None:
            service.health_check_url = data.health_check_url

        db.commit()
        db.refresh(service)

        return success_response(service.to_dict())


@services_bp.route("/<int:service_id>", methods=["DELETE"])
def delete_service(service_id: int):
    """Delete a service."""
    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)

        db.delete(service)
        db.commit()

        return success_response(message="Service deleted successfully")


@services_bp.route("/<int:service_id>/status", methods=["PUT"])
@validate_request(ServiceStatusUpdate)
def update_service_status(service_id: int):
    """Update service status."""
    data = request.validated_data

    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)

        service.status = ServiceStatus(data.status)
        db.commit()
        db.refresh(service)

        return success_response(service.to_dict())
