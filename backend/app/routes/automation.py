"""Automation routes with extensible executor support."""

from flask import Blueprint, request

from app.models import AutomationJob, Device, JobStatus
from app.schemas.automation import AutomationJobCreate
from app.services.executors import registry
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.validation import validate_request

automation_bp = Blueprint("automation", __name__)


@automation_bp.route("", methods=["POST"])
@validate_request(AutomationJobCreate)
def trigger_automation():
    """Trigger an automation job.
    ---
    tags:
      - Automation
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - device_id
            - action_name
          properties:
            device_id:
              type: integer
              description: ID of the target device
              example: 1
            executor_type:
              type: string
              description: Executor backend type
              default: ansible
              example: ansible
            action_name:
              type: string
              description: Action/playbook to execute
              example: ping
            action_config:
              type: object
              description: Action-specific configuration
    responses:
      201:
        description: Automation job created and started
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/AutomationJob'
      400:
        description: Validation error (invalid executor, action, or device has no IP)
      404:
        description: Device not found
    """
    data = request.validated_data

    # Get executor from registry
    executor = registry.get_executor(data.executor_type)
    if not executor:
        valid_types = [e.type for e in registry.list_executor_types()]
        raise ValidationError(
            f"Unknown executor type: {data.executor_type}. Valid types: {valid_types}"
        )

    # Validate action exists for this executor
    if not executor.validate_config(data.action_name, data.action_config):
        raise ValidationError(
            f"Invalid action '{data.action_name}' for executor '{data.executor_type}'"
        )

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise NotFoundError("Device", data.device_id)

        # Validate device has IP address
        if not device.ip_address:
            raise ValidationError("Device must have an IP address for automation")

        job = AutomationJob(
            device_id=data.device_id,
            executor_type=data.executor_type,
            action_name=data.action_name,
            action_config=data.action_config,
            status=JobStatus.PENDING,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # Execute automation in background thread
        executor.execute(
            job_id=job.id,
            device_ip=device.ip_address,
            device_name=device.name,
            action_name=data.action_name,
            config=data.action_config,
        )

        return success_response(job.to_dict(), status_code=201)


@automation_bp.route("/<int:job_id>", methods=["GET"])
def get_job_status(job_id: int):
    """Get automation job status.
    ---
    tags:
      - Automation
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: Job ID
    responses:
      200:
        description: Job details
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/AutomationJob'
      404:
        description: Job not found
    """
    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response(job.to_dict())


@automation_bp.route("/<int:job_id>/logs", methods=["GET"])
def get_job_logs(job_id: int):
    """Get automation job logs.
    ---
    tags:
      - Automation
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: Job ID
    responses:
      200:
        description: Job logs
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                job_id:
                  type: integer
                log_output:
                  type: string
      404:
        description: Job not found
    """
    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response({"job_id": job.id, "log_output": job.log_output or ""})


@automation_bp.route("/executors", methods=["GET"])
def list_executors():
    """List available executor types.
    ---
    tags:
      - Automation
    responses:
      200:
        description: List of available executors
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  type:
                    type: string
                    example: ansible
                  display_name:
                    type: string
                    example: Ansible
                  description:
                    type: string
                    example: Execute Ansible playbooks for configuration management
    """
    executors = registry.list_executor_types()
    return success_response(
        [
            {
                "type": e.type,
                "display_name": e.display_name,
                "description": e.description,
            }
            for e in executors
        ]
    )


@automation_bp.route("/executors/<executor_type>/actions", methods=["GET"])
def list_executor_actions(executor_type: str):
    """List available actions for an executor type.
    ---
    tags:
      - Automation
    parameters:
      - name: executor_type
        in: path
        type: string
        required: true
        description: Executor type identifier
    responses:
      200:
        description: List of available actions
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    example: ping
                  display_name:
                    type: string
                    example: Ping
                  description:
                    type: string
                    example: Test connectivity to device
                  config_schema:
                    type: object
      404:
        description: Executor type not found
    """
    executor = registry.get_executor(executor_type)
    if not executor:
        raise NotFoundError("Executor", executor_type)

    actions = executor.list_available_actions()
    return success_response(
        [
            {
                "name": a.name,
                "display_name": a.display_name,
                "description": a.description,
                "config_schema": a.config_schema,
            }
            for a in actions
        ]
    )


@automation_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """List automation jobs with optional filtering.
    ---
    tags:
      - Automation
    parameters:
      - name: device_id
        in: query
        type: integer
        description: Filter by device ID
      - name: executor_type
        in: query
        type: string
        description: Filter by executor type
    responses:
      200:
        description: List of automation jobs
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/AutomationJob'
      404:
        description: Device not found (if device_id filter specified)
    """
    device_id = request.args.get("device_id", type=int)
    executor_type = request.args.get("executor_type", type=str)

    with DatabaseSession() as db:
        query = db.query(AutomationJob)

        if device_id:
            # Verify device exists
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise NotFoundError("Device", device_id)
            query = query.filter(AutomationJob.device_id == device_id)

        if executor_type:
            query = query.filter(AutomationJob.executor_type == executor_type)

        # Order by id descending (newest first)
        jobs = query.order_by(AutomationJob.id.desc()).all()

        return success_response([job.to_dict() for job in jobs])
