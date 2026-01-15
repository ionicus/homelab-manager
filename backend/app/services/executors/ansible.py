"""Ansible playbook executor implementation using Celery."""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from app.config import Config
from app.tasks.automation import run_ansible_playbook

from .base import ActionInfo, BaseExecutor

logger = logging.getLogger(__name__)

# Pattern for valid playbook names: alphanumeric, underscore, hyphen only
SAFE_ACTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class AnsibleExecutor(BaseExecutor):
    """Execute Ansible playbooks via Celery task queue."""

    def __init__(self, playbooks_dir: str | None = None):
        if playbooks_dir is None:
            playbooks_dir = Config.ANSIBLE_PLAYBOOK_DIR
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
        extra_vars: dict[str, Any] | None = None,
        devices: list[dict[str, str]] | None = None,
    ) -> str:
        """Queue an Ansible playbook for execution via Celery.

        Supports both single-device and multi-device execution.

        Args:
            job_id: Database ID of the automation job
            device_ip: Target device IP address (single device mode)
            device_name: Target device name (single device mode)
            action_name: Name of the playbook to execute (without .yml)
            config: Optional extra configuration (not used for Ansible)
            extra_vars: Optional variables to pass to the playbook
            devices: Optional list of device dicts for multi-device execution

        Returns:
            Celery task ID for tracking
        """
        task = run_ansible_playbook.delay(
            job_id=job_id,
            device_ip=device_ip,
            device_name=device_name,
            playbook_name=action_name,
            extra_vars=extra_vars,
            devices=devices,
        )
        device_count = len(devices) if devices else 1
        logger.info(
            f"Queued playbook execution for job {job_id}, "
            f"task_id={task.id}, devices={device_count}"
        )
        return task.id

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
            with open(playbook_path) as f:
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

    def get_action_schema(self, action_name: str) -> dict | None:
        """Get the variable schema for a playbook.

        Loads schema from schemas/<action_name>.schema.yml if it exists.

        Args:
            action_name: Name of the playbook (without .yml)

        Returns:
            JSON Schema dict or None if no schema exists
        """
        # Validate action name first
        if not SAFE_ACTION_NAME_PATTERN.match(action_name):
            return None

        schema_path = self.playbooks_dir / "schemas" / f"{action_name}.schema.yml"

        if not schema_path.exists():
            return None

        try:
            with open(schema_path) as f:
                schema = yaml.safe_load(f)
                return schema if isinstance(schema, dict) else None
        except Exception as e:
            logger.warning(f"Failed to load schema for {action_name}: {e}")
            return None

    def get_schema_defaults(self, action_name: str) -> dict:
        """Extract default values from a playbook's schema.

        Args:
            action_name: Name of the playbook

        Returns:
            Dict of variable names to default values
        """
        schema = self.get_action_schema(action_name)
        if not schema or "properties" not in schema:
            return {}

        defaults = {}
        for var_name, var_schema in schema.get("properties", {}).items():
            if "default" in var_schema:
                defaults[var_name] = var_schema["default"]

        return defaults
