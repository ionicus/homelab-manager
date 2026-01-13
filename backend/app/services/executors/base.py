"""Base executor interface for automation backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ActionInfo:
    """Information about an available automation action."""

    name: str
    display_name: str
    description: str
    config_schema: dict  # JSON Schema for action config


@dataclass
class ExecutorInfo:
    """Information about an executor type."""

    type: str
    display_name: str
    description: str


class BaseExecutor(ABC):
    """Abstract base class for automation executors.

    All automation backends (Ansible, SSH, Terraform, etc.) must implement
    this interface to be registered with the executor registry.
    """

    @abstractmethod
    def execute(
        self,
        job_id: int,
        device_ip: str,
        device_name: str,
        action_name: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Execute an automation action in a background thread.

        Args:
            job_id: Database ID of the automation job
            device_ip: Target device IP address
            device_name: Target device name
            action_name: Name of the action to execute
            config: Optional action-specific configuration
        """
        pass

    @abstractmethod
    def list_available_actions(self) -> list[ActionInfo]:
        """List all available actions for this executor.

        Returns:
            List of ActionInfo objects describing available actions
        """
        pass

    @abstractmethod
    def validate_config(self, action_name: str, config: dict | None) -> bool:
        """Validate configuration for an action.

        Args:
            action_name: Name of the action
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def get_executor_type(cls) -> str:
        """Return unique identifier for this executor type.

        Returns:
            String identifier (e.g., 'ansible', 'ssh', 'terraform')
        """
        pass

    @classmethod
    @abstractmethod
    def get_display_name(cls) -> str:
        """Return human-readable name for this executor.

        Returns:
            Display name (e.g., 'Ansible', 'SSH Commands')
        """
        pass

    @classmethod
    def get_description(cls) -> str:
        """Return description of this executor.

        Returns:
            Description string
        """
        return ""

    @classmethod
    def get_info(cls) -> ExecutorInfo:
        """Return executor info object.

        Returns:
            ExecutorInfo with type, display_name, and description
        """
        return ExecutorInfo(
            type=cls.get_executor_type(),
            display_name=cls.get_display_name(),
            description=cls.get_description(),
        )
