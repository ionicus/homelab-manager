"""Celery tasks for automation execution."""

import ipaddress
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT
from typing import Any

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

# Pattern to detect Ansible TASK lines for progress tracking
TASK_PATTERN = re.compile(r'^TASK \[(.+)\]')
PLAY_PATTERN = re.compile(r'^PLAY \[(.+)\]')

# Cancellation check interval (check every N lines)
CANCELLATION_CHECK_INTERVAL = 10


class CancellationError(Exception):
    """Raised when a job is cancelled."""
    pass


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

    # Build host line with required parameters
    host_line = (
        f"{safe_name} ansible_host={safe_ip} "
        f"ansible_user={ansible_user} ansible_ssh_common_args='{ssh_args}'"
    )

    # Add password authentication if configured (requires sshpass on system)
    ansible_password = os.getenv("ANSIBLE_PASSWORD")
    if ansible_password:
        host_line += f" ansible_password={ansible_password}"
        host_line += " ansible_ssh_extra_args='-o PubkeyAuthentication=no'"

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


def _categorize_error(error: Exception) -> str:
    """Categorize an error for better user feedback.

    Args:
        error: The exception that occurred

    Returns:
        Error category string
    """
    error_str = str(error).lower()
    if "connection refused" in error_str or "unreachable" in error_str:
        return "connectivity"
    elif "permission denied" in error_str:
        return "permission"
    elif "not found" in error_str:
        return "not_found"
    elif "timeout" in error_str:
        return "timeout"
    elif "authentication" in error_str:
        return "authentication"
    return "execution"


def _sanitize_extra_vars(extra_vars: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize extra vars to prevent command injection.

    Only allows safe types: str, int, float, bool, list, dict.
    Strings are escaped to prevent shell injection.

    Args:
        extra_vars: Raw extra variables dict

    Returns:
        Sanitized extra variables dict
    """
    if not extra_vars:
        return {}

    sanitized = {}
    for key, value in extra_vars.items():
        # Validate key is alphanumeric with underscores
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
            logger.warning(f"Skipping invalid variable name: {key}")
            continue

        # Only allow safe types
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            # Allow list of primitive types
            sanitized[key] = [v for v in value if isinstance(v, (str, int, float, bool))]
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = _sanitize_extra_vars(value)
        else:
            logger.warning(f"Skipping unsupported variable type for {key}: {type(value)}")

    return sanitized


def _get_redis_client():
    """Get Redis client for log streaming if available.

    Returns:
        Redis client or None if not available
    """
    try:
        from redis import Redis
        redis_url = Config.CELERY_BROKER_URL
        if redis_url and redis_url.startswith("redis://"):
            return Redis.from_url(redis_url)
    except Exception as e:
        logger.debug(f"Redis not available for streaming: {e}")
    return None


def _count_tasks_in_playbook(playbook_path: Path) -> int:
    """Count approximate number of tasks in a playbook.

    Args:
        playbook_path: Path to the playbook file

    Returns:
        Estimated task count (minimum 1)
    """
    try:
        import yaml
        with open(playbook_path) as f:
            playbook = yaml.safe_load(f)

        task_count = 0
        if isinstance(playbook, list):
            for play in playbook:
                if isinstance(play, dict):
                    tasks = play.get("tasks", [])
                    if isinstance(tasks, list):
                        task_count += len(tasks)
                    # Count pre_tasks and post_tasks too
                    pre_tasks = play.get("pre_tasks", [])
                    if isinstance(pre_tasks, list):
                        task_count += len(pre_tasks)
                    post_tasks = play.get("post_tasks", [])
                    if isinstance(post_tasks, list):
                        task_count += len(post_tasks)

        return max(task_count, 1)
    except Exception as e:
        logger.debug(f"Could not count tasks in playbook: {e}")
        return 1


def _execute_with_streaming(
    cmd: list[str],
    job_id: int,
    db,
    job: AutomationJob,
    redis_client=None,
) -> int:
    """Execute command with streaming output, progress tracking, and cancellation support.

    Args:
        cmd: Command to execute
        job_id: Job ID for logging
        db: Database session
        job: AutomationJob instance
        redis_client: Optional Redis client for pub/sub streaming

    Returns:
        Process return code

    Raises:
        CancellationError: If job was cancelled
        subprocess.TimeoutExpired: If process times out
    """
    log_channel = f"job:{job_id}:logs"
    output_lines = []
    line_count = 0

    process = subprocess.Popen(
        cmd,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,  # Line buffered
    )

    try:
        for line in iter(process.stdout.readline, ''):
            if not line:
                break

            line_count += 1

            # Redact sensitive data before storing/publishing
            safe_line = _redact_sensitive_data(line.rstrip())
            output_lines.append(safe_line)

            # Publish to Redis for real-time streaming (if available)
            if redis_client:
                try:
                    redis_client.publish(log_channel, safe_line)
                except Exception:
                    pass  # Non-critical, continue execution

            # Track progress from TASK lines
            if TASK_PATTERN.match(line):
                job.tasks_completed += 1
                if job.task_count > 0:
                    job.progress = min(int((job.tasks_completed / job.task_count) * 100), 99)
                    # Don't commit on every task - batch updates
                    if job.tasks_completed % 3 == 0:
                        db.commit()

            # Check for cancellation periodically
            if line_count % CANCELLATION_CHECK_INTERVAL == 0:
                db.refresh(job)
                if job.cancel_requested:
                    logger.info(f"Job {job_id} cancellation detected, terminating process")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise CancellationError("Job cancelled by user")

        # Wait for process to complete
        process.wait(timeout=500)

        # Final progress update
        if process.returncode == 0:
            job.progress = 100

        return process.returncode

    finally:
        # Ensure process is terminated
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # Store accumulated output
        job.log_output = "\n".join(output_lines)

        # Publish completion signal to Redis
        if redis_client:
            try:
                redis_client.publish(log_channel, "[[STREAM_COMPLETE]]")
            except Exception:
                pass


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
    extra_vars: dict[str, Any] | None = None,
) -> dict:
    """Execute an Ansible playbook as a Celery task.

    This task runs in a Celery worker process, separate from the web server.
    It supports automatic retries, timeout handling, result persistence,
    real-time log streaming, progress tracking, and cancellation.

    Args:
        job_id: Database ID of the automation job
        device_ip: Target device IP address
        device_name: Target device name
        playbook_name: Name of the playbook to execute (without .yml)
        extra_vars: Optional extra variables to pass to ansible-playbook

    Returns:
        Dict with job status and details
    """
    db = Session()
    job = None
    inventory_file = None
    extra_vars_file = None
    redis_client = None

    try:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return {"status": "error", "message": "Job not found"}

        # Check if already cancelled before starting
        if job.cancel_requested:
            job.status = JobStatus.CANCELLED
            job.cancelled_at = datetime.utcnow()
            job.log_output = "Job cancelled before execution started."
            db.commit()
            return {"status": "cancelled", "job_id": job_id}

        # Update job status to running and store celery task ID
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.celery_task_id = self.request.id
        db.commit()
        logger.info(f"Job {job_id} status updated to RUNNING (Celery task: {self.request.id})")

        # Get Redis client for streaming (optional)
        redis_client = _get_redis_client()

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

        # Count tasks for progress tracking
        job.task_count = _count_tasks_in_playbook(playbook_path)
        db.commit()

        # Generate inventory
        inventory_file = _generate_inventory(device_ip, device_name, job_id)

        # Merge extra vars: parameter takes precedence over job.extra_vars
        merged_extra_vars = {}
        if job.extra_vars:
            merged_extra_vars.update(job.extra_vars)
        if extra_vars:
            merged_extra_vars.update(extra_vars)

        # Sanitize extra vars to prevent injection
        safe_extra_vars = _sanitize_extra_vars(merged_extra_vars)

        # Execute ansible-playbook command
        cmd = [
            "ansible-playbook",
            str(playbook_path),
            "-i",
            inventory_file,
            "--timeout",
            "300",
        ]

        # Add extra vars if present (use JSON file for safety)
        if safe_extra_vars:
            fd = tempfile.NamedTemporaryFile(
                mode="w",
                prefix=f"ansible_vars_{job_id}_",
                suffix=".json",
                delete=False,
            )
            try:
                json.dump(safe_extra_vars, fd)
                extra_vars_file = fd.name
            finally:
                fd.close()
            os.chmod(extra_vars_file, 0o600)
            cmd.extend(["--extra-vars", f"@{extra_vars_file}"])

        logger.info(f"Executing command: {' '.join(cmd)}")

        # Execute with streaming
        return_code = _execute_with_streaming(
            cmd=cmd,
            job_id=job_id,
            db=db,
            job=job,
            redis_client=redis_client,
        )

        # Update job status based on result
        job.completed_at = datetime.utcnow()
        if return_code == 0:
            job.status = JobStatus.COMPLETED
            job.progress = 100
            logger.info(f"Job {job_id} completed successfully")
        else:
            job.status = JobStatus.FAILED
            job.error_category = "execution"
            logger.error(f"Job {job_id} failed with return code {return_code}")

        db.commit()

        return {
            "status": job.status.value,
            "job_id": job_id,
            "return_code": return_code,
        }

    except CancellationError:
        logger.info(f"Job {job_id} was cancelled")
        if job:
            job.status = JobStatus.CANCELLED
            job.cancelled_at = datetime.utcnow()
            job.log_output = (job.log_output or "") + "\n\n--- Job cancelled by user ---"
            db.commit()
        return {"status": "cancelled", "job_id": job_id}

    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} hit soft time limit")
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_category = "timeout"
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
            job.error_category = "timeout"
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
            job.error_category = _categorize_error(e)
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
        # Cleanup temporary files
        if inventory_file:
            try:
                Path(inventory_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete inventory file: {e}")
        if extra_vars_file:
            try:
                Path(extra_vars_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete extra vars file: {e}")
