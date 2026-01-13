"""Ansible playbook executor using threading."""

import logging
import subprocess
import threading
from pathlib import Path

from app.database import Session
from app.models import AutomationJob, JobStatus

logger = logging.getLogger(__name__)


class AnsibleExecutor:
    """Execute Ansible playbooks in background threads."""

    def __init__(self, playbooks_dir: str = "../ansible/playbooks"):
        self.playbooks_dir = Path(playbooks_dir).resolve()
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)

    def execute_playbook(
        self,
        job_id: int,
        device_ip: str,
        device_name: str,
        playbook_name: str,
    ) -> None:
        """
        Execute an Ansible playbook in a background thread.

        Args:
            job_id: Database ID of the automation job
            device_ip: Target device IP address
            device_name: Target device name
            playbook_name: Name of the playbook to execute
        """
        thread = threading.Thread(
            target=self._run_playbook,
            args=(job_id, device_ip, device_name, playbook_name),
            daemon=True,
        )
        thread.start()
        logger.info(f"Started playbook execution thread for job {job_id}")

    def _run_playbook(
        self,
        job_id: int,
        device_ip: str,
        device_name: str,
        playbook_name: str,
    ) -> None:
        """
        Internal method to run the playbook (runs in separate thread).

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
            if result.returncode == 0:
                job.status = JobStatus.COMPLETED
                logger.info(f"Job {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                logger.error(f"Job {job_id} failed with return code {result.returncode}")

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
                job.log_output = (
                    job.log_output or ""
                ) + "\n\nERROR: Execution timed out after 10 minutes"
                db.commit()

        except Exception as e:
            logger.exception(f"Error executing job {job_id}")
            if job:
                job.status = JobStatus.FAILED
                job.log_output = (job.log_output or "") + f"\n\nERROR: {str(e)}"
                db.commit()

        finally:
            db.close()

    def _generate_inventory(self, device_ip: str, device_name: str) -> str:
        """
        Generate Ansible inventory for a single device.

        Args:
            device_ip: Target device IP address
            device_name: Target device name

        Returns:
            Inventory file content in INI format
        """
        ssh_args = "-o StrictHostKeyChecking=no"
        return f"""[homelab]
{device_name} ansible_host={device_ip} ansible_user=root ansible_ssh_common_args='{ssh_args}'

[all:vars]
ansible_python_interpreter=/usr/bin/python3
"""

    def list_available_playbooks(self) -> list[str]:
        """
        List all available playbooks in the playbooks directory.

        Returns:
            List of playbook names (without .yml extension)
        """
        playbooks = []
        if self.playbooks_dir.exists():
            for file in self.playbooks_dir.glob("*.yml"):
                playbooks.append(file.stem)
        return sorted(playbooks)


# Global executor instance
executor = AnsibleExecutor()
