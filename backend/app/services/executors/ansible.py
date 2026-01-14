"""Ansible playbook executor implementation."""

import ipaddress
import logging
import os
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.database import Session
from app.models import AutomationJob, JobStatus

from .base import ActionInfo, BaseExecutor

logger = logging.getLogger(__name__)

# Pattern for valid playbook names: alphanumeric, underscore, hyphen only
SAFE_ACTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class AnsibleExecutor(BaseExecutor):
    """Execute Ansible playbooks in background threads."""

    def __init__(self, playbooks_dir: str = "automation/ansible/playbooks"):
        self.playbooks_dir = Path(playbooks_dir).resolve()
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_executor_type(cls) -> str:
        """Return executor type identifier."""
        return "ansible"

    @classmethod
    def get_display_name(cls) -> str:
        """Return human-readable name."""
        return "Ansible"

    @classmethod
    def get_description(cls) -> str:
        """Return executor description."""
        return "Execute Ansible playbooks for configuration management"

    def execute(
        self,
        job_id: int,
        device_ip: str,
        device_name: str,
        action_name: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Execute an Ansible playbook in a background thread.

        Args:
            job_id: Database ID of the automation job
            device_ip: Target device IP address
            device_name: Target device name
            action_name: Name of the playbook to execute (without .yml)
            config: Optional extra configuration (not used for Ansible)
        """
        thread = threading.Thread(
            target=self._run_playbook,
            args=(job_id, device_ip, device_name, action_name),
            daemon=True,
        )
        thread.start()
        logger.info(f"Started playbook execution thread for job {job_id}")

    def list_available_actions(self) -> list[ActionInfo]:
        """List available Ansible playbooks as actions.

        Returns:
            List of ActionInfo objects for each playbook
        """
        actions = []
        if self.playbooks_dir.exists():
            for file in self.playbooks_dir.glob("*.yml"):
                actions.append(
                    ActionInfo(
                        name=file.stem,
                        display_name=file.stem.replace("_", " ").title(),
                        description=self._get_playbook_description(file),
                        config_schema={},  # Ansible playbooks don't need extra config
                    )
                )
        return sorted(actions, key=lambda a: a.name)

    def validate_config(self, action_name: str, config: dict | None) -> bool:
        """Validate that the playbook exists and action name is safe.

        Args:
            action_name: Name of the playbook
            config: Configuration (not used for Ansible)

        Returns:
            True if action name is safe and playbook file exists
        """
        # Validate action name contains only safe characters (prevent path traversal)
        if not SAFE_ACTION_NAME_PATTERN.match(action_name):
            logger.warning(f"Invalid action name rejected: {action_name}")
            return False

        # Build path and resolve to absolute
        playbook_path = (self.playbooks_dir / f"{action_name}.yml").resolve()

        # Ensure the resolved path is within the playbooks directory (prevent symlink attacks)
        if not str(playbook_path).startswith(str(self.playbooks_dir.resolve())):
            logger.warning(f"Path traversal attempt blocked: {action_name}")
            return False

        return playbook_path.exists()

    def _get_playbook_description(self, playbook_path: Path) -> str:
        """Extract description from playbook file.

        Looks for a comment at the start of the file or the play name.

        Args:
            playbook_path: Path to the playbook file

        Returns:
            Description string or default message
        """
        try:
            with open(playbook_path, "r") as f:
                content = f.read(500)  # Read first 500 chars
                # Look for "# Description:" comment
                for line in content.split("\n"):
                    if line.strip().startswith("# Description:"):
                        return line.split(":", 1)[1].strip()
                    # Or use the play name
                    if "- name:" in line:
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return f"Execute {playbook_path.stem} playbook"

    def _run_playbook(
        self,
        job_id: int,
        device_ip: str,
        device_name: str,
        playbook_name: str,
    ) -> None:
        """Internal method to run the playbook (runs in separate thread).

        Args:
            job_id: Database ID of the automation job
            device_ip: Target device IP address
            device_name: Target device name
            playbook_name: Name of the playbook to execute
        """
        db = Session()
        job = None

        try:
            # Get job from database
            job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in database")
                return

            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            logger.info(f"Job {job_id} status updated to RUNNING")

            # Generate inventory
            inventory_content = self._generate_inventory(device_ip, device_name)
            inventory_file = f"/tmp/ansible_inventory_{job_id}.ini"

            with open(inventory_file, "w") as f:
                f.write(inventory_content)

            # Build playbook path
            playbook_path = self.playbooks_dir / f"{playbook_name}.yml"
            if not playbook_path.exists():
                raise FileNotFoundError(f"Playbook not found: {playbook_path}")

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
                timeout=600,  # 10 minute timeout
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
                logger.error(
                    f"Job {job_id} failed with return code {result.returncode}"
                )

            db.commit()

            # Cleanup inventory file
            try:
                Path(inventory_file).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete inventory file: {e}")

        except subprocess.TimeoutExpired:
            logger.error(f"Job {job_id} timed out")
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.log_output = (
                    job.log_output or ""
                ) + "\n\nERROR: Execution timed out after 10 minutes"
                db.commit()

        except Exception as e:
            logger.exception(f"Error executing job {job_id}")
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.log_output = (job.log_output or "") + f"\n\nERROR: {str(e)}"
                db.commit()

        finally:
            db.close()

    def _sanitize_inventory_value(self, value: str) -> str:
        """Sanitize a value for use in Ansible inventory.

        Removes characters that could be used for injection attacks.

        Args:
            value: Raw input value

        Returns:
            Sanitized value safe for inventory files
        """
        # Remove newlines, quotes, backslashes, and other dangerous characters
        sanitized = re.sub(r"[\n\r'\"\\\[\]{}]", "", value)
        return sanitized.strip()

    def _validate_ip_address(self, ip_str: str) -> str:
        """Validate and return IP address.

        Args:
            ip_str: IP address string

        Returns:
            Validated IP address string

        Raises:
            ValueError: If IP address is invalid
        """
        try:
            # This validates both IPv4 and IPv6
            ip = ipaddress.ip_address(ip_str)
            return str(ip)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {ip_str}") from e

    def _generate_inventory(self, device_ip: str, device_name: str) -> str:
        """Generate Ansible inventory for a single device.

        Args:
            device_ip: Target device IP address
            device_name: Target device name

        Returns:
            Inventory file content in INI format

        Raises:
            ValueError: If device_ip is not a valid IP address
        """
        # Validate and sanitize inputs
        safe_ip = self._validate_ip_address(device_ip)
        safe_name = self._sanitize_inventory_value(device_name)

        # Use a safe inventory hostname (alphanumeric only)
        if not re.match(r"^[a-zA-Z0-9_-]+$", safe_name):
            safe_name = f"device_{hash(safe_name) % 10000}"

        # Get configurable Ansible user from environment (default: ansible, not root)
        ansible_user = os.getenv("ANSIBLE_USER", "ansible")
        ansible_user = self._sanitize_inventory_value(ansible_user)

        # Use accept-new to accept new host keys but reject changed ones
        ssh_host_key_checking = os.getenv("ANSIBLE_HOST_KEY_CHECKING", "accept-new")

        # Build SSH args securely
        ssh_args = f"-o StrictHostKeyChecking={ssh_host_key_checking}"

        # Optionally add SSH key path
        ssh_key_path = os.getenv("ANSIBLE_SSH_KEY")
        if ssh_key_path:
            ssh_args += f" -o IdentityFile={ssh_key_path}"

        host_line = (
            f"{safe_name} ansible_host={safe_ip} "
            f"ansible_user={ansible_user} ansible_ssh_common_args='{ssh_args}'"
        )
        return f"""[homelab]
{host_line}

[all:vars]
ansible_python_interpreter=/usr/bin/python3
"""
