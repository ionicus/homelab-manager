"""Executor registry for managing automation backends."""

import logging
from typing import Type

from .base import BaseExecutor, ExecutorInfo

logger = logging.getLogger(__name__)


class ExecutorRegistry:
    """Registry for automation executor types.

    Singleton pattern ensures a single global registry instance.
    Executors register themselves on import and can be retrieved by type.
    """

    _instance = None
    _executors: dict[str, BaseExecutor]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._executors = {}
        return cls._instance

    def register(self, executor_class: Type[BaseExecutor]) -> None:
        """Register an executor class.

        Args:
            executor_class: Class implementing BaseExecutor
        """
        executor_type = executor_class.get_executor_type()
        self._executors[executor_type] = executor_class()
        logger.info(f"Registered executor: {executor_type}")

    def get_executor(self, executor_type: str) -> BaseExecutor | None:
        """Get an executor instance by type.

        Args:
            executor_type: Executor type identifier

        Returns:
            Executor instance or None if not found
        """
        return self._executors.get(executor_type)

    def list_executor_types(self) -> list[ExecutorInfo]:
        """List all registered executor types.

        Returns:
            List of ExecutorInfo objects
        """
        return [executor.get_info() for executor in self._executors.values()]

    def get_default_type(self) -> str:
        """Return default executor type.

        Returns:
            'ansible' for backwards compatibility
        """
        return "ansible"

    def is_registered(self, executor_type: str) -> bool:
        """Check if an executor type is registered.

        Args:
            executor_type: Executor type identifier

        Returns:
            True if registered, False otherwise
        """
        return executor_type in self._executors


# Global registry instance
registry = ExecutorRegistry()
