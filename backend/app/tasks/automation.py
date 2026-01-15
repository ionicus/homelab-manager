"""Celery tasks for automation execution."""

import ipaddress
import logging
import os
import re
import subprocess
import tempfile
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

# Maximum log output size (characters) to store
MAX_LOG_OUTPUT_SIZE = 100_000  # 100KB

# Patterns to redact from log output (case-insensitive)
SENSITIVE_PATTERNS = [
    # Passwords in various formats
    (re.compile(r'(password|passwd|pwd)\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE), r'\1=***REDACTED***'),
    (re.compile(r'(ansible_password|ansible_become_pass|ansible_ssh_pass)\s*[:=]\s*[^\s]+', re.IGNORECASE), r'\1=***REDACTED***'),
    # API keys and tokens
    (re.compile(r'(api[_-]?key|api[_-]?secret|token|bearer)\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE), r'\1=***REDACTED***'),
    # AWS credentials
    (re.compile(r'(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*[^\s]+', re.IGNORECASE), r'\1=***REDACTED***'),
    # Generic secrets
    (re.compile(r'(secret|private[_-]?key)\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE), r'\1=***REDACTED***'),
    # SSH private key content
    (re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----', re.DOTALL), '***PRIVATE KEY REDACTED***'),
]


def _redact_sensitive_data(text: str) -> str:
    """Redact sensitive information from text before logging/storing.

    Removes or masks:
    - Passwords and credentials
    - API keys and tokens
    - Private keys

    Args:
        text: Raw text that may contain sensitive data

    Returns:
        Text with sensitive data redacted
    """
    if not text:
        return text

    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)

    # Truncate if too long
    if len(result) > MAX_LOG_OUTPUT_SIZE:
        result = result[:MAX_LOG_OUTPUT_SIZE] + "\n\n... [OUTPUT TRUNCATED - exceeded 100KB limit]"

    return result


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

    Uses secure tempfile with restricted permissions to prevent
    information disclosure and race condition attacks.

    Args:
        device_ip: Target device IP address
        device_name: Target device name
        job_id: Job ID for unique naming (used in prefix for debugging)

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

    # Use secure tempfile with:
    # - Unpredictable filename (random suffix)
    # - Restrictive permissions (0o600 - owner read/write only)
    # - delete=False so we can pass path to ansible, cleanup manually later
    fd = tempfile.NamedTemporaryFile(
        mode="w",
        prefix=f"ansible_inv_{job_id}_",
        suffix=".ini",
        delete=False,
    )
    try:
        fd.write(inventory_content)
        inventory_path = fd.name
    finally:
        fd.close()

    # Ensure restrictive permissions (NamedTemporaryFile already creates with 0o600)
    os.chmod(inventory_path, 0o600)

    return inventory_path


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

        # Capture and redact output before storing
        log_output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        job.log_output = _redact_sensitive_data(log_output)

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
            # Redact any existing output and append error
            existing = _redact_sensitive_data(job.log_output or "")
            job.log_output = existing + "\n\nERROR: Task exceeded time limit"
            db.commit()
        raise  # Let Celery handle retry

    except subprocess.TimeoutExpired:
        logger.error(f"Job {job_id} subprocess timed out")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            # Redact any existing output and append error
            existing = _redact_sensitive_data(job.log_output or "")
            job.log_output = existing + "\n\nERROR: Execution timed out"
            db.commit()
        return {"status": "failed", "job_id": job_id, "error": "timeout"}

    except Exception as e:
        logger.exception(f"Error executing job {job_id}")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            # Redact any existing output and error message
            existing = _redact_sensitive_data(job.log_output or "")
            error_msg = _redact_sensitive_data(str(e))
            job.log_output = existing + f"\n\nERROR: {error_msg}"
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
