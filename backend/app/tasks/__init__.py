"""Celery tasks package."""

from app.tasks.automation import run_ansible_playbook

__all__ = ["run_ansible_playbook"]
