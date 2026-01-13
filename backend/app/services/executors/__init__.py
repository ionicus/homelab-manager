"""Automation executors package.

This package provides a plugin-based architecture for automation backends.
New executors can be added by implementing BaseExecutor and registering
with the global registry.

Example:
    from app.services.executors import registry, BaseExecutor

    class MyExecutor(BaseExecutor):
        @classmethod
        def get_executor_type(cls) -> str:
            return "my_executor"
        # ... implement other abstract methods

    registry.register(MyExecutor)
"""

from .ansible import AnsibleExecutor
from .base import ActionInfo, BaseExecutor, ExecutorInfo
from .registry import ExecutorRegistry, registry

# Register built-in executors
registry.register(AnsibleExecutor)

__all__ = [
    "ActionInfo",
    "BaseExecutor",
    "ExecutorInfo",
    "ExecutorRegistry",
    "registry",
    "AnsibleExecutor",
]
