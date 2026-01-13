"""Provisioning routes with improved error handling and validation."""

from flask import Blueprint, request

from app.models import ProvisioningJob, JobStatus, Device
from app.schemas.provisioning import ProvisioningTaskCreate
from app.services.ansible_executor import executor
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.validation import validate_request

provisioning_bp = Blueprint("provisioning", __name__)


@provisioning_bp.route("", methods=["POST"])
@validate_request(ProvisioningTaskCreate)
def trigger_provisioning():
    """Trigger a provisioning job."""
    data = request.validated_data

    with DatabaseSession() as db:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            raise NotFoundError("Device", data.device_id)

        job = ProvisioningJob(
            device_id=data.device_id,
            playbook_name=data.playbook_name,
            status=JobStatus.PENDING,
        )

        # Validate device has IP address
        if not device.ip_address:
            raise ValidationError("Device must have an IP address for provisioning")

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


@provisioning_bp.route("/<int:job_id>", methods=["GET"])
def get_job_status(job_id: int):
    """Get provisioning job status."""
    with DatabaseSession() as db:
        job = db.query(ProvisioningJob).filter(ProvisioningJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response(job.to_dict())


@provisioning_bp.route("/<int:job_id>/logs", methods=["GET"])
def get_job_logs(job_id: int):
    """Get provisioning job logs."""
    with DatabaseSession() as db:
        job = db.query(ProvisioningJob).filter(ProvisioningJob.id == job_id).first()
        if not job:
            raise NotFoundError("Job", job_id)

        return success_response({"job_id": job.id, "log_output": job.log_output or ""})
