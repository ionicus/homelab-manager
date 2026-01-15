"""Automation routes with extensible executor support."""

from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required

from app import limiter
from app.config import Config
from app.models import AutomationJob, Device, JobStatus
from app.schemas.automation import AutomationJobCreate
from app.services.executors import registry
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.pagination import get_pagination_params, paginate_query, paginated_response
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
        # Determine device ID (device_id takes precedence, otherwise use first from device_ids)
        device_id = data.device_id
        if device_id is None and data.device_ids:
            device_id = data.device_ids[0]

        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise NotFoundError("Device", device_id)

        # Validate device has IP address
        if not device.ip_address:
            raise ValidationError("Device must have an IP address for automation")

        job = AutomationJob(
            device_id=device_id,
            executor_type=data.executor_type,
            action_name=data.action_name,
            action_config=data.action_config,
            extra_vars=data.extra_vars,
            status=JobStatus.PENDING,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # Queue automation for background execution via Celery
        celery_task_id = executor.execute(
            job_id=job.id,
            device_ip=device.ip_address,
            device_name=device.name,
            action_name=data.action_name,
            config=data.action_config,
            extra_vars=data.extra_vars,
        )

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
            yield "event: error\ndata: {\"message\": \"Real-time streaming unavailable\"}\n\n"
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
            job.log_output = (job.log_output or "") + "\n\nJob cancelled before execution."
            db.commit()
            return success_response({
                "job_id": job.id,
                "message": "Job cancelled immediately (was pending)",
                "status": "cancelled",
            })

        db.commit()

        return success_response({
            "job_id": job.id,
            "message": "Cancellation requested. Job will stop at next checkpoint.",
            "status": "cancellation_requested",
        })


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


@automation_bp.route("/executors/<executor_type>/actions/<action_name>/schema", methods=["GET"])
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

    return success_response({
        "action_name": action_name,
        "schema": schema,
    })


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
            [job.to_dict() for job in jobs],
            total, page, per_page
        )
