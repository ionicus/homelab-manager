"""Service routes with improved error handling and validation."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models import Device, Service, ServiceStatus
from app.schemas.service import ServiceCreate, ServiceStatusUpdate, ServiceUpdate
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    success_response,
)
from app.utils.pagination import (
    get_pagination_params,
    paginate_query,
    paginated_response,
)
from app.utils.validation import validate_request

services_bp = Blueprint("services", __name__)


@services_bp.route("", methods=["GET"])
@jwt_required()
def list_services():
    """List services with pagination.
    ---
    tags:
      - Services
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Items per page (max 100)
    responses:
      200:
        description: Paginated list of services
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/Service'
            pagination:
              type: object
    """
    page, per_page = get_pagination_params()

    with DatabaseSession() as db:
        query = db.query(Service).order_by(Service.name)
        services, total = paginate_query(query, page, per_page)
        return paginated_response(
            [service.to_dict() for service in services], total, page, per_page
        )


@services_bp.route("/<int:service_id>", methods=["GET"])
@jwt_required()
def get_service(service_id: int):
    """Get a specific service.
    ---
    tags:
      - Services
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: Service ID
    responses:
      200:
        description: Service details
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/Service'
      404:
        description: Service not found
    """
    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)
        return success_response(service.to_dict())


@services_bp.route("", methods=["POST"])
@jwt_required()
@validate_request(ServiceCreate)
def create_service():
    """Create a new service.
    ---
    tags:
      - Services
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - device_id
            - name
          properties:
            device_id:
              type: integer
              description: ID of the device running this service
              example: 1
            name:
              type: string
              description: Service name
              example: nginx
            port:
              type: integer
              description: Port number
              example: 80
            protocol:
              type: string
              description: Protocol
              example: http
            status:
              type: string
              enum: [running, stopped, error]
              default: stopped
            health_check_url:
              type: string
              description: Health check endpoint
              example: http://localhost:80/health
    responses:
      201:
        description: Service created successfully
      400:
        description: Validation error
      404:
        description: Device not found
    """
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
@jwt_required()
@validate_request(ServiceUpdate)
def update_service(service_id: int):
    """Update a service.
    ---
    tags:
      - Services
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: Service ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            port:
              type: integer
            protocol:
              type: string
            status:
              type: string
              enum: [running, stopped, error]
            health_check_url:
              type: string
    responses:
      200:
        description: Service updated successfully
      404:
        description: Service not found
      400:
        description: Validation error
    """
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
@jwt_required()
def delete_service(service_id: int):
    """Delete a service.
    ---
    tags:
      - Services
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: Service ID
    responses:
      200:
        description: Service deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Service deleted successfully
      404:
        description: Service not found
    """
    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)

        db.delete(service)
        db.commit()

        return success_response(message="Service deleted successfully")


@services_bp.route("/<int:service_id>/status", methods=["PUT"])
@jwt_required()
@validate_request(ServiceStatusUpdate)
def update_service_status(service_id: int):
    """Update service status.
    ---
    tags:
      - Services
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: Service ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [running, stopped, error]
              description: New service status
    responses:
      200:
        description: Status updated successfully
      404:
        description: Service not found
    """
    data = request.validated_data

    with DatabaseSession() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundError("Service", service_id)

        service.status = ServiceStatus(data.status)
        db.commit()
        db.refresh(service)

        return success_response(service.to_dict())
