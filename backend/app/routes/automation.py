"""Automation routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import AutomationJob, JobStatus, Device
from app.schemas.automation import AutomationJobCreate
from app.services.ansible_executor import executor
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
    """Trigger an automation job."""
    data = request.validated_data

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise NotFoundError("Device", data.device_id)

        job = AutomationJob(
            device_id=data.device_id,
            playbook_name=data.playbook_name,
            status=JobStatus.PENDING,
        )

        # Validate device has IP address
        if not device.ip_address:
            raise ValidationError("Device must have an IP address for automation")

        db.add(job)
        db.commit()
        db.refresh(job)

        # Trigger Ansible playbook execution in background thread
        executor.execute_playbook(
            job_id=job.id,
            device_ip=device.ip_address,
            device_name=device.name,
            playbook_name=data.playbook_name,
        )

        return success_response(job.to_dict(), status_code=201)


@automation_bp.route("/<int:job_id>", methods=["GET"])
def get_job_status(job_id: int):
    """Get automation job status."""
    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response(job.to_dict())


@automation_bp.route("/<int:job_id>/logs", methods=["GET"])
def get_job_logs(job_id: int):
    """Get automation job logs."""
    with DatabaseSession() as db:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response({"job_id": job.id, "log_output": job.log_output or ""})


@automation_bp.route("/playbooks", methods=["GET"])
def list_playbooks():
    """List available Ansible playbooks."""
    playbooks = executor.list_available_playbooks()
    return success_response({"playbooks": playbooks})


@automation_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """List automation jobs, optionally filtered by device_id."""
    device_id = request.args.get("device_id", type=int)

    with DatabaseSession() as db:
        query = db.query(AutomationJob)

        if device_id:
            # Verify device exists
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise NotFoundError("Device", device_id)
            query = query.filter(AutomationJob.device_id == device_id)

        # Order by id descending (newest first)
        jobs = query.order_by(AutomationJob.id.desc()).all()

        return success_response([job.to_dict() for job in jobs])
