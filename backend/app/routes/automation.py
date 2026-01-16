"""Automation routes with extensible executor support."""

import re

from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required
from kombu.exceptions import OperationalError as KombuOperationalError

from app import limiter
from app.config import Config
from app.models import AutomationJob, Device, JobStatus, VaultSecret
from app.schemas.automation import AutomationJobCreate
from app.services.executors import registry
from app.services.vault import VaultService
from app.utils.errors import (
    APIError,
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.pagination import (
    get_pagination_params,
    paginate_query,
    paginated_response,
)
from app.utils.validation import validate_request

automation_bp = Blueprint("automation", __name__)


@automation_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
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
        # Build list of target devices
        devices_list = []
        all_device_ids = []

        if data.device_ids and len(data.device_ids) > 0:
            # Multi-device mode: fetch all specified devices
            all_device_ids = data.device_ids
            devices = db.query(Device).filter(Device.id.in_(all_device_ids)).all()

            # Verify all devices were found
            found_ids = {d.id for d in devices}
            missing_ids = set(all_device_ids) - found_ids
            if missing_ids:
                raise NotFoundError("Device", list(missing_ids)[0])

            # Validate all devices have IP addresses
            for device in devices:
                if not device.ip_address:
                    raise ValidationError(
                        f"Device '{device.name}' (ID: {device.id}) must have an IP address"
                    )
                devices_list.append({"ip": device.ip_address, "name": device.name})

            # Use first device as the primary for the relationship
            primary_device = devices[0]
        else:
            # Single device mode
            device_id = data.device_id
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise NotFoundError("Device", device_id)

            if not device.ip_address:
                raise ValidationError("Device must have an IP address for automation")

            primary_device = device
            all_device_ids = [device_id]

        # Validate vault secret if provided
        vault_password = None
        if data.vault_secret_id:
            vault_secret = (
                db.query(VaultSecret)
                .filter(VaultSecret.id == data.vault_secret_id)
                .first()
            )
            if not vault_secret:
                raise NotFoundError("VaultSecret", data.vault_secret_id)
            # Decrypt the vault password for passing to executor
            vault_password = VaultService.decrypt(vault_secret.encrypted_content)

        # Create the job
        job = AutomationJob(
            device_id=primary_device.id,
            device_ids=all_device_ids if len(all_device_ids) > 1 else None,
            executor_type=data.executor_type,
            action_name=data.action_name,
            action_config=data.action_config,
            extra_vars=data.extra_vars,
            vault_secret_id=data.vault_secret_id,
            status=JobStatus.PENDING,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # Queue automation for background execution via Celery
        try:
            celery_task_id = executor.execute(
                job_id=job.id,
                device_ip=primary_device.ip_address,
                device_name=primary_device.name,
                action_name=data.action_name,
                config=data.action_config,
                extra_vars=data.extra_vars,
                devices=devices_list if len(devices_list) > 1 else None,
                vault_password=vault_password,
            )
        except KombuOperationalError:
            # Celery/RabbitMQ not available - update job status and return error
            job.status = JobStatus.FAILED
            job.log_output = "Task queue (Celery/RabbitMQ) is not available."
            db.commit()
            raise APIError(
                "Task queue unavailable. Please ensure Celery and RabbitMQ are running.",
                status_code=503,
            ) from None

        # Store the Celery task ID for tracking
        if celery_task_id:
            job.celery_task_id = celery_task_id
            db.commit()
            db.refresh(job)

        return success_response(job.to_dict(), status_code=201)


@automation_bp.route("/<int:job_id>", methods=["GET"])
@jwt_required()
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
@jwt_required()
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


@automation_bp.route("/<int:job_id>/logs/stream", methods=["GET"])
def stream_job_logs(job_id: int):
    """Stream automation job logs in real-time via SSE.
    ---
    tags:
      - Automation
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: Job ID
      - name: include_existing
        in: query
        type: boolean
        default: true
        description: Include existing logs before streaming
    responses:
      200:
        description: SSE stream of log lines
        content:
          text/event-stream:
            schema:
              type: string
      404:
        description: Job not found
    """
    import redis

    # Verify job exists first
    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        initial_status = job.status.value
        initial_logs = job.log_output or ""
        initial_progress = job.progress

    include_existing = request.args.get("include_existing", "true").lower() == "true"

    def event_stream():
        # Send initial job info
        import json

        yield f"event: status\ndata: {json.dumps({'status': initial_status, 'progress': initial_progress})}\n\n"

        # Send existing logs if requested
        if include_existing and initial_logs:
            for line in initial_logs.split("\n"):
                yield f"data: {line}\n\n"

        # If job already completed, send completion event and close
        if initial_status in ("completed", "failed", "cancelled"):
            yield "event: complete\ndata: {}\n\n"
            return

        # Connect to Redis for real-time streaming
        try:
            redis_client = redis.from_url(Config.CELERY_BROKER_URL)
            pubsub = redis_client.pubsub()
            pubsub.subscribe(f"job:{job_id}:logs")

            # Listen for messages with timeout
            for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    # Check for stream completion marker
                    if data == "[[STREAM_COMPLETE]]":
                        yield "event: complete\ndata: {}\n\n"
                        break

                    yield f"data: {data}\n\n"

        except redis.ConnectionError:
            # Redis not available, fall back to polling
            yield 'event: error\ndata: {"message": "Real-time streaming unavailable"}\n\n'
        finally:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@automation_bp.route("/<int:job_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_job(job_id: int):
    """Request cancellation of a running job.
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
        description: Cancellation requested
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                job_id:
                  type: integer
                message:
                  type: string
      400:
        description: Job cannot be cancelled (not running)
      404:
        description: Job not found
    """
    from datetime import datetime

    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        # Can only cancel running or pending jobs
        if job.status not in (JobStatus.RUNNING, JobStatus.PENDING):
            raise ValidationError(
                f"Cannot cancel job with status '{job.status.value}'. "
                "Only running or pending jobs can be cancelled."
            )

        # Mark cancellation requested
        job.cancel_requested = True

        # If pending, cancel immediately
        if job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.cancelled_at = datetime.utcnow()
            job.log_output = (
                job.log_output or ""
            ) + "\n\nJob cancelled before execution."
            db.commit()
            return success_response(
                {
                    "job_id": job.id,
                    "message": "Job cancelled immediately (was pending)",
                    "status": "cancelled",
                }
            )

        db.commit()

        return success_response(
            {
                "job_id": job.id,
                "message": "Cancellation requested. Job will stop at next checkpoint.",
                "status": "cancellation_requested",
            }
        )


@automation_bp.route("/<int:job_id>/rerun", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
def rerun_job(job_id: int):
    """Re-run an existing job by resetting its status and re-queuing.
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
        description: Job re-queued successfully
        schema:
          type: object
          properties:
            data:
              $ref: '#/definitions/AutomationJob'
      400:
        description: Job cannot be re-run (still running or pending)
      404:
        description: Job not found
    """
    from kombu.exceptions import OperationalError as KombuOperationalError

    from app.services.vault import VaultService

    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        # Cannot re-run jobs that are still in progress
        if job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            raise ValidationError(
                f"Cannot re-run job with status '{job.status.value}'. "
                "Wait for it to complete or cancel it first."
            )

        # Get the device
        device = db.query(Device).filter(Device.id == job.device_id).first()
        if not device:
            raise NotFoundError("Device", job.device_id)

        if not device.ip_address:
            raise ValidationError("Device must have an IP address for automation")

        # Get executor
        executor = registry.get_executor(job.executor_type)
        if not executor:
            raise ValidationError(f"Unknown executor type: {job.executor_type}")

        # Build device list for multi-device jobs
        devices_list = []
        if job.device_ids and len(job.device_ids) > 1:
            devices = db.query(Device).filter(Device.id.in_(job.device_ids)).all()
            for d in devices:
                if d.ip_address:
                    devices_list.append({"ip": d.ip_address, "name": d.name})

        # Get vault password if needed
        vault_password = None
        if job.vault_secret_id:
            vault_secret = (
                db.query(VaultSecret)
                .filter(VaultSecret.id == job.vault_secret_id)
                .first()
            )
            if vault_secret:
                vault_password = VaultService.decrypt(vault_secret.encrypted_content)

        # Reset job state
        job.status = JobStatus.PENDING
        job.started_at = None
        job.completed_at = None
        job.cancelled_at = None
        job.log_output = None
        job.progress = 0
        job.tasks_completed = 0
        job.task_count = 0
        job.error_category = None
        job.cancel_requested = False
        job.celery_task_id = None

        db.commit()

        # Re-queue the job
        try:
            celery_task_id = executor.execute(
                job_id=job.id,
                device_ip=device.ip_address,
                device_name=device.name,
                action_name=job.action_name,
                config=job.action_config,
                extra_vars=job.extra_vars,
                devices=devices_list if len(devices_list) > 1 else None,
                vault_password=vault_password,
            )
        except KombuOperationalError:
            job.status = JobStatus.FAILED
            job.log_output = "Task queue (Celery) is not available."
            db.commit()
            raise APIError(
                "Task queue unavailable. Please ensure Celery is running.",
                status_code=503,
            ) from None

        # Store Celery task ID
        if celery_task_id:
            job.celery_task_id = celery_task_id
            db.commit()
            db.refresh(job)

        return success_response(job.to_dict())


@automation_bp.route("/executors", methods=["GET"])
@jwt_required()
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
@jwt_required()
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


@automation_bp.route(
    "/executors/<executor_type>/actions/<action_name>/schema", methods=["GET"]
)
@jwt_required()
def get_action_schema(executor_type: str, action_name: str):
    """Get variable schema for a specific action.
    ---
    tags:
      - Automation
    parameters:
      - name: executor_type
        in: path
        type: string
        required: true
        description: Executor type identifier
      - name: action_name
        in: path
        type: string
        required: true
        description: Action/playbook name
    responses:
      200:
        description: Action variable schema (JSON Schema format)
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                action_name:
                  type: string
                schema:
                  type: object
                  description: JSON Schema for action variables
      404:
        description: Executor or action not found
    """
    executor = registry.get_executor(executor_type)
    if not executor:
        raise NotFoundError("Executor", executor_type)

    # Check if action exists
    if not executor.validate_config(action_name, None):
        raise NotFoundError("Action", action_name)

    # Get schema if executor supports it
    schema = {}
    if hasattr(executor, "get_action_schema"):
        schema = executor.get_action_schema(action_name) or {}

    return success_response(
        {
            "action_name": action_name,
            "schema": schema,
        }
    )


@automation_bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    """List automation jobs with optional filtering and pagination.
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
        description: Paginated list of automation jobs
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/definitions/AutomationJob'
            pagination:
              type: object
      404:
        description: Device not found (if device_id filter specified)
    """
    device_id = request.args.get("device_id", type=int)
    executor_type = request.args.get("executor_type", type=str)
    page, per_page = get_pagination_params()

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
        query = query.order_by(AutomationJob.id.desc())
        jobs, total = paginate_query(query, page, per_page)

        return paginated_response(
            [job.to_dict() for job in jobs], total, page, per_page
        )


# =============================================================================
# Vault Secrets Routes
# =============================================================================


@automation_bp.route("/vault/secrets", methods=["GET"])
@jwt_required()
def list_vault_secrets():
    """List all vault secrets (without content).
    ---
    tags:
      - Vault
    responses:
      200:
        description: List of vault secrets
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  description:
                    type: string
                  created_at:
                    type: string
                  updated_at:
                    type: string
    """
    with DatabaseSession() as db:
        secrets = db.query(VaultSecret).order_by(VaultSecret.name).all()
        return success_response([s.to_dict() for s in secrets])


@automation_bp.route("/vault/secrets", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
def create_vault_secret():
    """Create a new vault secret.
    ---
    tags:
      - Vault
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - content
          properties:
            name:
              type: string
              description: Unique name for the secret
              example: ssh_key_prod
            description:
              type: string
              description: Optional description
              example: SSH private key for production servers
            content:
              type: string
              description: The secret content to encrypt
    responses:
      201:
        description: Vault secret created
      400:
        description: Validation error
      409:
        description: Secret with this name already exists
    """
    data = request.get_json()

    if not data or not data.get("name") or not data.get("content"):
        raise ValidationError("Name and content are required")

    name = data["name"].strip()
    content = data["content"]
    description = data.get("description", "").strip() or None

    # Validate name format (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise ValidationError(
            "Name must start with a letter and contain only letters, numbers, underscores, and hyphens"
        )

    if len(name) > 100:
        raise ValidationError("Name must be 100 characters or less")

    with DatabaseSession() as db:
        # Check for existing secret with same name
        existing = db.query(VaultSecret).filter(VaultSecret.name == name).first()
        if existing:
            raise ValidationError(f"Secret with name '{name}' already exists")

        # Encrypt the content
        encrypted_content = VaultService.encrypt(content)

        secret = VaultSecret(
            name=name,
            description=description,
            encrypted_content=encrypted_content,
        )
        db.add(secret)
        db.commit()
        db.refresh(secret)

        return success_response(secret.to_dict(), status_code=201)


@automation_bp.route("/vault/secrets/<int:secret_id>", methods=["GET"])
@jwt_required()
def get_vault_secret(secret_id: int):
    """Get a vault secret by ID (without content).
    ---
    tags:
      - Vault
    parameters:
      - name: secret_id
        in: path
        type: integer
        required: true
        description: Secret ID
    responses:
      200:
        description: Vault secret details
      404:
        description: Secret not found
    """
    with DatabaseSession() as db:
        secret = db.query(VaultSecret).filter(VaultSecret.id == secret_id).first()
        if not secret:
            raise NotFoundError("VaultSecret", secret_id)

        return success_response(secret.to_dict())


@automation_bp.route("/vault/secrets/<int:secret_id>", methods=["PUT"])
@jwt_required()
@limiter.limit("10 per minute")
def update_vault_secret(secret_id: int):
    """Update a vault secret.
    ---
    tags:
      - Vault
    parameters:
      - name: secret_id
        in: path
        type: integer
        required: true
        description: Secret ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            description:
              type: string
              description: Updated description
            content:
              type: string
              description: New secret content (if changing)
    responses:
      200:
        description: Vault secret updated
      400:
        description: Validation error
      404:
        description: Secret not found
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    with DatabaseSession() as db:
        secret = db.query(VaultSecret).filter(VaultSecret.id == secret_id).first()
        if not secret:
            raise NotFoundError("VaultSecret", secret_id)

        # Update description if provided
        if "description" in data:
            secret.description = data["description"].strip() or None

        # Update content if provided
        if "content" in data and data["content"]:
            secret.encrypted_content = VaultService.encrypt(data["content"])

        db.commit()
        db.refresh(secret)

        return success_response(secret.to_dict())


@automation_bp.route("/vault/secrets/<int:secret_id>", methods=["DELETE"])
@jwt_required()
def delete_vault_secret(secret_id: int):
    """Delete a vault secret.
    ---
    tags:
      - Vault
    parameters:
      - name: secret_id
        in: path
        type: integer
        required: true
        description: Secret ID
    responses:
      200:
        description: Vault secret deleted
      404:
        description: Secret not found
    """
    with DatabaseSession() as db:
        secret = db.query(VaultSecret).filter(VaultSecret.id == secret_id).first()
        if not secret:
            raise NotFoundError("VaultSecret", secret_id)

        db.delete(secret)
        db.commit()

        return success_response({"message": f"Secret '{secret.name}' deleted"})
