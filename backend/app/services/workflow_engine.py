"""Workflow orchestrator for managing multi-step automation workflows."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    AutomationJob,
    Device,
    JobStatus,
    VaultSecret,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowTemplate,
)
from app.services.executors import registry
from app.services.vault import VaultService

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflow execution.

    Manages the lifecycle of workflow instances, creating jobs for steps,
    handling dependencies, and triggering rollbacks on failure.
    """

    def __init__(self, db: Session):
        """Initialize the orchestrator.

        Args:
            db: Database session
        """
        self.db = db

    def start_workflow(
        self,
        template_id: int,
        device_ids: list[int],
        rollback_on_failure: bool = False,
        extra_vars: dict | None = None,
        vault_secret_id: int | None = None,
    ) -> WorkflowInstance:
        """Start a new workflow instance.

        Creates a workflow instance and jobs for all steps that have
        no dependencies (step_order 0 or empty depends_on).

        Args:
            template_id: ID of the workflow template to execute
            device_ids: List of device IDs to run the workflow on
            rollback_on_failure: Whether to run rollback actions on failure
            extra_vars: Additional variables to pass to all steps
            vault_secret_id: Optional vault secret for encrypted content

        Returns:
            Created WorkflowInstance

        Raises:
            ValueError: If template not found or invalid
        """
        # Fetch template
        template = (
            self.db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == template_id)
            .first()
        )
        if not template:
            raise ValueError(f"Workflow template {template_id} not found")

        if not template.steps:
            raise ValueError("Workflow template has no steps")

        # Validate devices
        devices = self.db.query(Device).filter(Device.id.in_(device_ids)).all()
        if len(devices) != len(device_ids):
            found_ids = {d.id for d in devices}
            missing = set(device_ids) - found_ids
            raise ValueError(f"Devices not found: {missing}")

        for device in devices:
            if not device.ip_address:
                raise ValueError(
                    f"Device '{device.name}' (ID: {device.id}) has no IP address"
                )

        # Get vault password if vault secret specified
        vault_password = None
        if vault_secret_id:
            vault_secret = (
                self.db.query(VaultSecret)
                .filter(VaultSecret.id == vault_secret_id)
                .first()
            )
            if not vault_secret:
                raise ValueError(f"Vault secret {vault_secret_id} not found")
            vault_password = VaultService.decrypt(vault_secret.encrypted_content)

        # Create workflow instance with template snapshot
        instance = WorkflowInstance(
            template_id=template_id,
            template_snapshot={
                "name": template.name,
                "steps": template.steps,
            },
            status=WorkflowStatus.PENDING,
            device_ids=device_ids,
            rollback_on_failure=rollback_on_failure,
            extra_vars=extra_vars,
        )
        self.db.add(instance)
        self.db.flush()  # Get instance ID

        # Create jobs for all steps
        step_jobs = {}  # step_order -> job_id mapping
        for step in sorted(template.steps, key=lambda s: s.get("order", 0)):
            step_order = step.get("order", 0)
            action_name = step.get("action_name")
            executor_type = step.get("executor_type", "ansible")
            depends_on = step.get("depends_on", [])
            step_extra_vars = step.get("extra_vars", {})

            # Merge extra vars: workflow > step
            merged_vars = {**(extra_vars or {}), **step_extra_vars}

            # Map depends_on step orders to job IDs
            depends_on_job_ids = [step_jobs[o] for o in depends_on if o in step_jobs]

            # Use first device as primary (for FK constraint)
            primary_device = devices[0]

            # Create the job
            job = AutomationJob(
                device_id=primary_device.id,
                device_ids=device_ids if len(device_ids) > 1 else None,
                executor_type=executor_type,
                action_name=action_name,
                extra_vars=merged_vars if merged_vars else None,
                vault_secret_id=vault_secret_id,
                status=JobStatus.PENDING,
                workflow_instance_id=instance.id,
                step_order=step_order,
                depends_on_job_ids=depends_on_job_ids if depends_on_job_ids else None,
                is_rollback=False,
            )
            self.db.add(job)
            self.db.flush()
            step_jobs[step_order] = job.id

        self.db.commit()

        # Start jobs with no dependencies
        instance.status = WorkflowStatus.RUNNING
        instance.started_at = datetime.utcnow()
        self.db.commit()

        self._start_ready_jobs(instance, devices, vault_password)

        return instance

    def _start_ready_jobs(
        self,
        instance: WorkflowInstance,
        devices: list[Device],
        vault_password: str | None = None,
    ):
        """Start jobs that are ready to run (all dependencies satisfied).

        Args:
            instance: Workflow instance
            devices: List of target devices
            vault_password: Optional decrypted vault password
        """
        # Get all pending jobs for this workflow
        pending_jobs = (
            self.db.query(AutomationJob)
            .filter(
                AutomationJob.workflow_instance_id == instance.id,
                AutomationJob.status == JobStatus.PENDING,
                AutomationJob.is_rollback == False,  # noqa: E712
            )
            .all()
        )

        # Get completed job IDs
        completed_job_ids = {
            j.id
            for j in instance.jobs
            if j.status == JobStatus.COMPLETED and not j.is_rollback
        }

        for job in pending_jobs:
            # Check if all dependencies are satisfied
            depends_on = job.depends_on_job_ids or []
            if all(dep_id in completed_job_ids for dep_id in depends_on):
                self._execute_job(job, devices, vault_password)

    def _execute_job(
        self,
        job: AutomationJob,
        devices: list[Device],
        vault_password: str | None = None,
    ):
        """Execute a single job via the appropriate executor.

        Args:
            job: Job to execute
            devices: Target devices
            vault_password: Optional decrypted vault password
        """
        executor = registry.get_executor(job.executor_type)
        if not executor:
            logger.error(f"Executor {job.executor_type} not found for job {job.id}")
            job.status = JobStatus.FAILED
            job.error_category = "configuration"
            self.db.commit()
            return

        primary_device = devices[0]
        devices_list = [{"ip": d.ip_address, "name": d.name} for d in devices]

        try:
            celery_task_id = executor.execute(
                job_id=job.id,
                device_ip=primary_device.ip_address,
                device_name=primary_device.name,
                action_name=job.action_name,
                config=job.action_config,
                extra_vars=job.extra_vars,
                devices=devices_list if len(devices_list) > 1 else None,
                vault_password=vault_password,
            )
            if celery_task_id:
                job.celery_task_id = celery_task_id
                self.db.commit()
            logger.info(f"Started workflow job {job.id} (step {job.step_order})")
        except Exception as e:
            logger.exception(f"Failed to start job {job.id}: {e}")
            job.status = JobStatus.FAILED
            job.error_category = "execution"
            self.db.commit()

    def on_job_complete(self, job_id: int):
        """Handle job completion - trigger dependent jobs or rollback.

        This should be called when a workflow job completes (success or failure).

        Args:
            job_id: ID of the completed job
        """
        job = self.db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job or not job.workflow_instance_id:
            return

        instance = job.workflow_instance
        if not instance or instance.status not in (
            WorkflowStatus.RUNNING,
            WorkflowStatus.ROLLING_BACK,
        ):
            return

        # Get devices
        devices = self.db.query(Device).filter(Device.id.in_(instance.device_ids)).all()

        # Get vault password if needed
        vault_password = None
        if job.vault_secret_id:
            vault_secret = (
                self.db.query(VaultSecret)
                .filter(VaultSecret.id == job.vault_secret_id)
                .first()
            )
            if vault_secret:
                vault_password = VaultService.decrypt(vault_secret.encrypted_content)

        if instance.status == WorkflowStatus.ROLLING_BACK:
            # Handle rollback job completion
            self._handle_rollback_completion(instance)
            return

        if job.status == JobStatus.COMPLETED:
            # Check if all non-rollback jobs are complete
            all_jobs = [j for j in instance.jobs if not j.is_rollback]
            if all(j.status == JobStatus.COMPLETED for j in all_jobs):
                instance.status = WorkflowStatus.COMPLETED
                instance.completed_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"Workflow instance {instance.id} completed successfully")
            else:
                # Start next ready jobs
                self._start_ready_jobs(instance, devices, vault_password)

        elif job.status == JobStatus.FAILED:
            if instance.rollback_on_failure:
                self._trigger_rollback(instance, devices, vault_password)
            else:
                instance.status = WorkflowStatus.FAILED
                instance.completed_at = datetime.utcnow()
                instance.error_message = (
                    f"Step {job.step_order} ({job.action_name}) failed"
                )
                self.db.commit()
                logger.info(
                    f"Workflow instance {instance.id} failed at step {job.step_order}"
                )

    def _trigger_rollback(
        self,
        instance: WorkflowInstance,
        devices: list[Device],
        vault_password: str | None = None,
    ):
        """Trigger rollback actions for completed steps in reverse order.

        Args:
            instance: Workflow instance
            devices: Target devices
            vault_password: Optional decrypted vault password
        """
        instance.status = WorkflowStatus.ROLLING_BACK
        self.db.commit()
        logger.info(f"Starting rollback for workflow instance {instance.id}")

        # Get template steps
        steps = (
            instance.template_snapshot.get("steps", [])
            if instance.template_snapshot
            else []
        )

        # Find completed steps that have rollback actions
        completed_jobs = [
            j
            for j in instance.jobs
            if j.status == JobStatus.COMPLETED and not j.is_rollback
        ]
        completed_step_orders = {j.step_order for j in completed_jobs}

        # Create rollback jobs in reverse order
        rollback_jobs = []
        for step in sorted(steps, key=lambda s: s.get("order", 0), reverse=True):
            step_order = step.get("order", 0)
            rollback_action = step.get("rollback_action")

            if step_order in completed_step_orders and rollback_action:
                primary_device = devices[0]
                rollback_job = AutomationJob(
                    device_id=primary_device.id,
                    device_ids=instance.device_ids
                    if len(instance.device_ids) > 1
                    else None,
                    executor_type=step.get("executor_type", "ansible"),
                    action_name=rollback_action,
                    extra_vars=instance.extra_vars,
                    vault_secret_id=completed_jobs[0].vault_secret_id
                    if completed_jobs
                    else None,
                    status=JobStatus.PENDING,
                    workflow_instance_id=instance.id,
                    step_order=-step_order,  # Negative to indicate rollback
                    is_rollback=True,
                )
                self.db.add(rollback_job)
                rollback_jobs.append(rollback_job)

        self.db.commit()

        if not rollback_jobs:
            # No rollback actions to run
            instance.status = WorkflowStatus.FAILED
            instance.completed_at = datetime.utcnow()
            instance.error_message = "Workflow failed, no rollback actions defined"
            self.db.commit()
            return

        # Start first rollback job
        self._execute_job(rollback_jobs[0], devices, vault_password)

    def _handle_rollback_completion(self, instance: WorkflowInstance):
        """Handle rollback job completion.

        Args:
            instance: Workflow instance
        """
        rollback_jobs = [j for j in instance.jobs if j.is_rollback]
        pending_rollbacks = [j for j in rollback_jobs if j.status == JobStatus.PENDING]
        failed_rollbacks = [j for j in rollback_jobs if j.status == JobStatus.FAILED]

        if pending_rollbacks:
            # Get devices and start next rollback
            devices = (
                self.db.query(Device).filter(Device.id.in_(instance.device_ids)).all()
            )

            # Get vault password if needed
            vault_password = None
            first_job = rollback_jobs[0] if rollback_jobs else None
            if first_job and first_job.vault_secret_id:
                vault_secret = (
                    self.db.query(VaultSecret)
                    .filter(VaultSecret.id == first_job.vault_secret_id)
                    .first()
                )
                if vault_secret:
                    vault_password = VaultService.decrypt(
                        vault_secret.encrypted_content
                    )

            self._execute_job(pending_rollbacks[0], devices, vault_password)
        elif failed_rollbacks:
            instance.status = WorkflowStatus.FAILED
            instance.completed_at = datetime.utcnow()
            instance.error_message = "Rollback failed"
            self.db.commit()
        else:
            instance.status = WorkflowStatus.ROLLED_BACK
            instance.completed_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Workflow instance {instance.id} rolled back successfully")

    def cancel_workflow(self, instance_id: int) -> WorkflowInstance:
        """Cancel a running workflow.

        Args:
            instance_id: ID of the workflow instance to cancel

        Returns:
            Updated WorkflowInstance

        Raises:
            ValueError: If instance not found or not cancellable
        """
        instance = (
            self.db.query(WorkflowInstance)
            .filter(WorkflowInstance.id == instance_id)
            .first()
        )
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")

        if instance.status not in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING):
            raise ValueError(f"Cannot cancel workflow in {instance.status.value} state")

        # Mark pending jobs as cancelled
        for job in instance.jobs:
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.cancelled_at = datetime.utcnow()
            elif job.status == JobStatus.RUNNING:
                job.cancel_requested = True

        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Workflow instance {instance.id} cancelled")
        return instance
