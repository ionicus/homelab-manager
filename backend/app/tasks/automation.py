"""Celery tasks for automation execution."""

import ipaddress
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from app.config import Config
from app.database import Session
from app.models import AutomationJob, JobStatus

logger = logging.getLogger(__name__)

# Pattern for valid playbook names: alphanumeric, underscore, hyphen only
SAFE_ACTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _sanitize_inventory_value(value: str) -> str:
    """Sanitize a value for use in Ansible inventory.

    Removes characters that could be used for injection attacks.

    Args:
        value: Raw input value

    Returns:
        Sanitized value safe for inventory files
    """
    sanitized = re.sub(r"[\n\r'\"\\[\]{}]", "", value)
    return sanitized.strip()


def _validate_ip_address(ip_str: str) -> str:
    """Validate and return IP address.

    Args:
        ip_str: IP address string

    Returns:
        Validated IP address string

    Raises:
        ValueError: If IP address is invalid
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return str(ip)
    except ValueError as e:
        raise ValueError(f"Invalid IP address: {ip_str}") from e


def _generate_inventory(device_ip: str, device_name: str, job_id: int) -> str:
    """Generate Ansible inventory for a single device.

    Args:
        device_ip: Target device IP address
        device_name: Target device name
        job_id: Job ID for unique naming

    Returns:
        Path to the inventory file

    Raises:
        ValueError: If device_ip is not a valid IP address
    """
    safe_ip = _validate_ip_address(device_ip)
    safe_name = _sanitize_inventory_value(device_name)

    if not re.match(r"^[a-zA-Z0-9_-]+$", safe_name):
        safe_name = f"device_{hash(safe_name) % 10000}"

    ansible_user = os.getenv("ANSIBLE_USER", "ansible")
    ansible_user = _sanitize_inventory_value(ansible_user)

    ssh_host_key_checking = os.getenv("ANSIBLE_HOST_KEY_CHECKING", "accept-new")
    ssh_args = f"-o StrictHostKeyChecking={ssh_host_key_checking}"

    ssh_key_path = os.getenv("ANSIBLE_SSH_KEY")
    if ssh_key_path:
        ssh_args += f" -o IdentityFile={ssh_key_path}"

    host_line = (
        f"{safe_name} ansible_host={safe_ip} "
        f"ansible_user={ansible_user} ansible_ssh_common_args='{ssh_args}'"
    )

    inventory_content = f"""[homelab]
{host_line}

[all:vars]
ansible_python_interpreter=/usr/bin/python3
"""

    inventory_file = f"/tmp/ansible_inventory_{job_id}.ini"
    with open(inventory_file, "w") as f:
        f.write(inventory_content)

    return inventory_file


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=540,  # Soft limit at 9 minutes
    time_limit=600,  # Hard limit at 10 minutes
)
def run_ansible_playbook(
    self,
    job_id: int,
    device_ip: str,
    device_name: str,
    playbook_name: str,
) -> dict:
    """Execute an Ansible playbook as a Celery task.

    This task runs in a Celery worker process, separate from the web server.
    It supports automatic retries, timeout handling, and result persistence.

    Args:
        job_id: Database ID of the automation job
        device_ip: Target device IP address
        device_name: Target device name
        playbook_name: Name of the playbook to execute (without .yml)

    Returns:
        Dict with job status and details
    """
    db = Session()
    job = None
    inventory_file = None

    try:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return {"status": "error", "message": "Job not found"}

        # Update job status to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} status updated to RUNNING (Celery task: {self.request.id})")

        # Validate playbook name
        if not SAFE_ACTION_NAME_PATTERN.match(playbook_name):
            raise ValueError(f"Invalid playbook name: {playbook_name}")

        # Build playbook path
        playbooks_dir = Path(Config.ANSIBLE_PLAYBOOK_DIR).resolve()
        playbook_path = (playbooks_dir / f"{playbook_name}.yml").resolve()

        # Security check: ensure path is within playbooks directory
        if not str(playbook_path).startswith(str(playbooks_dir)):
            raise ValueError(f"Path traversal attempt blocked: {playbook_name}")

        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook not found: {playbook_path}")

        # Generate inventory
        inventory_file = _generate_inventory(device_ip, device_name, job_id)

        # Execute ansible-playbook command
        cmd = [
            "ansible-playbook",
            str(playbook_path),
            "-i",
            inventory_file,
            "--timeout",
            "300",
        ]

        logger.info(f"Executing command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=500,  # 8+ minute timeout for subprocess
        )

        # Capture output
        log_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        job.log_output = log_output

        # Update job status based on result
        job.completed_at = datetime.utcnow()
        if result.returncode == 0:
            job.status = JobStatus.COMPLETED
            logger.info(f"Job {job_id} completed successfully")
        else:
            job.status = JobStatus.FAILED
            logger.error(f"Job {job_id} failed with return code {result.returncode}")

        db.commit()

        return {
            "status": job.status.value,
            "job_id": job_id,
            "return_code": result.returncode,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} hit soft time limit")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.log_output = (job.log_output or "") + "\n\nERROR: Task exceeded time limit"
            db.commit()
        raise  # Let Celery handle retry

    except subprocess.TimeoutExpired:
        logger.error(f"Job {job_id} subprocess timed out")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.log_output = (job.log_output or "") + "\n\nERROR: Execution timed out"
            db.commit()
        return {"status": "failed", "job_id": job_id, "error": "timeout"}

    except Exception as e:
        logger.exception(f"Error executing job {job_id}")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.log_output = (job.log_output or "") + f"\n\nERROR: {str(e)}"
            db.commit()

        # Don't retry on validation errors
        if isinstance(e, (ValueError, FileNotFoundError)):
            return {"status": "failed", "job_id": job_id, "error": str(e)}

        raise  # Let Celery handle retry for other errors

    finally:
        db.close()
        # Cleanup inventory file
        if inventory_file:
            try:
                Path(inventory_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete inventory file: {e}")
