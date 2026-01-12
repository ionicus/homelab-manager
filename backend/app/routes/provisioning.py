"""Provisioning routes."""

from flask import Blueprint, request, jsonify
from datetime import datetime

from app.database import Session
from app.models import ProvisioningJob, JobStatus, Device

provisioning_bp = Blueprint("provisioning", __name__)


@provisioning_bp.route("", methods=["POST"])
def trigger_provisioning():
    """Trigger a provisioning job."""
    data = request.get_json()

    if not data or "device_id" not in data or "playbook_name" not in data:
        return jsonify({"error": "Missing required fields: device_id, playbook_name"}), 400

    db = Session()
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == data["device_id"]).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        job = ProvisioningJob(
            device_id=data["device_id"],
            playbook_name=data["playbook_name"],
            status=JobStatus.PENDING,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # TODO: Trigger actual Ansible playbook execution asynchronously

        return jsonify(job.to_dict()), 201
    finally:
        db.close()


@provisioning_bp.route("/<int:job_id>", methods=["GET"])
def get_job_status(job_id: int):
    """Get provisioning job status."""
    db = Session()
    try:
        job = db.query(ProvisioningJob).filter(ProvisioningJob.id == job_id).first()
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify(job.to_dict()), 200
    finally:
        db.close()


@provisioning_bp.route("/<int:job_id>/logs", methods=["GET"])
def get_job_logs(job_id: int):
    """Get provisioning job logs."""
    db = Session()
    try:
        job = db.query(ProvisioningJob).filter(ProvisioningJob.id == job_id).first()
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({"job_id": job.id, "log_output": job.log_output or ""}), 200
    finally:
        db.close()
