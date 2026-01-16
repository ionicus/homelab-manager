"""Workflow routes for multi-step automation orchestration."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from pydantic import BaseModel, Field

from app import limiter
from app.models import WorkflowInstance, WorkflowStatus, WorkflowTemplate
from app.services.workflow_engine import WorkflowOrchestrator
from app.utils.errors import (
    DatabaseSession,
    NotFoundError,
    ValidationError,
    success_response,
)
from app.utils.pagination import (
    get_pagination_params,
    paginate_query,
    paginated_response,
)
from app.utils.validation import validate_request

workflows_bp = Blueprint("workflows", __name__)


# =============================================================================
# Pydantic Schemas
# =============================================================================


class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step."""

    order: int = Field(..., ge=0, description="Step execution order")
    action_name: str = Field(..., min_length=1, description="Action/playbook name")
    executor_type: str = Field(default="ansible", description="Executor type")
    depends_on: list[int] = Field(
        default_factory=list, description="List of step orders this step depends on"
    )
    rollback_action: str | None = Field(
        default=None, description="Action to run on rollback"
    )
    extra_vars: dict | None = Field(default=None, description="Step-specific variables")


class WorkflowTemplateCreate(BaseModel):
    """Schema for creating a workflow template."""

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: str | None = Field(default=None, description="Template description")
    steps: list[WorkflowStepSchema] = Field(
        ..., min_length=1, description="Workflow steps"
    )


class WorkflowTemplateUpdate(BaseModel):
    """Schema for updating a workflow template."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None)
    steps: list[WorkflowStepSchema] | None = Field(default=None, min_length=1)


class WorkflowStart(BaseModel):
    """Schema for starting a workflow."""

    template_id: int = Field(..., description="ID of the workflow template")
    device_ids: list[int] = Field(..., min_length=1, description="Target device IDs")
    rollback_on_failure: bool = Field(
        default=False, description="Run rollback actions on failure"
    )
    extra_vars: dict | None = Field(
        default=None, description="Additional variables for all steps"
    )
    vault_secret_id: int | None = Field(
        default=None, description="Vault secret for encrypted content"
    )


# =============================================================================
# Workflow Template Routes
# =============================================================================


@workflows_bp.route("/templates", methods=["GET"])
@jwt_required()
def list_templates():
    """List all workflow templates.
    ---
    tags:
      - Workflows
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Items per page (max 100)
    responses:
      200:
        description: Paginated list of workflow templates
    """
    page, per_page = get_pagination_params()

    with DatabaseSession() as db:
        query = db.query(WorkflowTemplate).order_by(WorkflowTemplate.name)
        templates, total = paginate_query(query, page, per_page)

        return paginated_response(
            [t.to_dict() for t in templates], total, page, per_page
        )


@workflows_bp.route("/templates", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
@validate_request(WorkflowTemplateCreate)
def create_template():
    """Create a new workflow template.
    ---
    tags:
      - Workflows
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - steps
          properties:
            name:
              type: string
              description: Unique template name
              example: Full Server Setup
            description:
              type: string
              description: Template description
            steps:
              type: array
              items:
                type: object
                properties:
                  order:
                    type: integer
                  action_name:
                    type: string
                  executor_type:
                    type: string
                  depends_on:
                    type: array
                    items:
                      type: integer
                  rollback_action:
                    type: string
                  extra_vars:
                    type: object
    responses:
      201:
        description: Workflow template created
      400:
        description: Validation error
      409:
        description: Template with this name already exists
    """
    data: WorkflowTemplateCreate = request.validated_data

    # Validate step orders are unique
    orders = [s.order for s in data.steps]
    if len(orders) != len(set(orders)):
        raise ValidationError("Step orders must be unique")

    # Validate dependencies reference valid step orders
    order_set = set(orders)
    for step in data.steps:
        for dep in step.depends_on:
            if dep not in order_set:
                raise ValidationError(
                    f"Step {step.order} depends on non-existent step {dep}"
                )
            if dep >= step.order:
                raise ValidationError(
                    f"Step {step.order} cannot depend on step {dep} "
                    "(dependencies must have lower order)"
                )

    with DatabaseSession() as db:
        # Check for existing template with same name
        existing = (
            db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.name == data.name)
            .first()
        )
        if existing:
            raise ValidationError(f"Template with name '{data.name}' already exists")

        template = WorkflowTemplate(
            name=data.name,
            description=data.description,
            steps=[s.model_dump() for s in data.steps],
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        return success_response(template.to_dict(), status_code=201)


@workflows_bp.route("/templates/<int:template_id>", methods=["GET"])
@jwt_required()
def get_template(template_id: int):
    """Get a workflow template by ID.
    ---
    tags:
      - Workflows
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
        description: Template ID
    responses:
      200:
        description: Workflow template details
      404:
        description: Template not found
    """
    with DatabaseSession() as db:
        template = (
            db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == template_id)
            .first()
        )
        if not template:
            raise NotFoundError("WorkflowTemplate", template_id)

        return success_response(template.to_dict())


@workflows_bp.route("/templates/<int:template_id>", methods=["PUT"])
@jwt_required()
@limiter.limit("10 per minute")
@validate_request(WorkflowTemplateUpdate)
def update_template(template_id: int):
    """Update a workflow template.
    ---
    tags:
      - Workflows
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
        description: Template ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            steps:
              type: array
    responses:
      200:
        description: Workflow template updated
      400:
        description: Validation error
      404:
        description: Template not found
    """
    data: WorkflowTemplateUpdate = request.validated_data

    with DatabaseSession() as db:
        template = (
            db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == template_id)
            .first()
        )
        if not template:
            raise NotFoundError("WorkflowTemplate", template_id)

        if data.name is not None:
            # Check for name conflict
            existing = (
                db.query(WorkflowTemplate)
                .filter(
                    WorkflowTemplate.name == data.name,
                    WorkflowTemplate.id != template_id,
                )
                .first()
            )
            if existing:
                raise ValidationError(
                    f"Template with name '{data.name}' already exists"
                )
            template.name = data.name

        if data.description is not None:
            template.description = data.description

        if data.steps is not None:
            # Validate steps
            orders = [s.order for s in data.steps]
            if len(orders) != len(set(orders)):
                raise ValidationError("Step orders must be unique")

            order_set = set(orders)
            for step in data.steps:
                for dep in step.depends_on:
                    if dep not in order_set:
                        raise ValidationError(
                            f"Step {step.order} depends on non-existent step {dep}"
                        )
                    if dep >= step.order:
                        raise ValidationError(
                            f"Step {step.order} cannot depend on step {dep}"
                        )

            template.steps = [s.model_dump() for s in data.steps]

        db.commit()
        db.refresh(template)

        return success_response(template.to_dict())


@workflows_bp.route("/templates/<int:template_id>", methods=["DELETE"])
@jwt_required()
def delete_template(template_id: int):
    """Delete a workflow template.
    ---
    tags:
      - Workflows
    parameters:
      - name: template_id
        in: path
        type: integer
        required: true
        description: Template ID
    responses:
      200:
        description: Template deleted
      400:
        description: Cannot delete template with running instances
      404:
        description: Template not found
    """
    with DatabaseSession() as db:
        template = (
            db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == template_id)
            .first()
        )
        if not template:
            raise NotFoundError("WorkflowTemplate", template_id)

        # Check for running instances
        running_instances = (
            db.query(WorkflowInstance)
            .filter(
                WorkflowInstance.template_id == template_id,
                WorkflowInstance.status.in_(
                    [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]
                ),
            )
            .count()
        )
        if running_instances > 0:
            raise ValidationError(
                f"Cannot delete template with {running_instances} running instance(s)"
            )

        db.delete(template)
        db.commit()

        return success_response({"message": f"Template '{template.name}' deleted"})


# =============================================================================
# Workflow Instance Routes
# =============================================================================


@workflows_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
@validate_request(WorkflowStart)
def start_workflow():
    """Start a new workflow instance.
    ---
    tags:
      - Workflows
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - template_id
            - device_ids
          properties:
            template_id:
              type: integer
              description: ID of the workflow template
            device_ids:
              type: array
              items:
                type: integer
              description: Target device IDs
            rollback_on_failure:
              type: boolean
              default: false
              description: Run rollback actions on failure
            extra_vars:
              type: object
              description: Additional variables for all steps
            vault_secret_id:
              type: integer
              description: Vault secret for encrypted content
    responses:
      201:
        description: Workflow instance started
      400:
        description: Validation error
      404:
        description: Template or device not found
    """
    data: WorkflowStart = request.validated_data

    with DatabaseSession() as db:
        orchestrator = WorkflowOrchestrator(db)
        try:
            instance = orchestrator.start_workflow(
                template_id=data.template_id,
                device_ids=data.device_ids,
                rollback_on_failure=data.rollback_on_failure,
                extra_vars=data.extra_vars,
                vault_secret_id=data.vault_secret_id,
            )
            return success_response(
                instance.to_dict(include_jobs=True), status_code=201
            )
        except ValueError as e:
            raise ValidationError(str(e)) from None


@workflows_bp.route("", methods=["GET"])
@jwt_required()
def list_instances():
    """List workflow instances with optional filtering.
    ---
    tags:
      - Workflows
    parameters:
      - name: template_id
        in: query
        type: integer
        description: Filter by template ID
      - name: status
        in: query
        type: string
        description: Filter by status
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Paginated list of workflow instances
    """
    template_id = request.args.get("template_id", type=int)
    status = request.args.get("status", type=str)
    page, per_page = get_pagination_params()

    with DatabaseSession() as db:
        query = db.query(WorkflowInstance).order_by(WorkflowInstance.id.desc())

        if template_id:
            query = query.filter(WorkflowInstance.template_id == template_id)

        if status:
            try:
                status_enum = WorkflowStatus(status)
                query = query.filter(WorkflowInstance.status == status_enum)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}") from None

        instances, total = paginate_query(query, page, per_page)

        return paginated_response(
            [i.to_dict() for i in instances], total, page, per_page
        )


@workflows_bp.route("/<int:instance_id>", methods=["GET"])
@jwt_required()
def get_instance(instance_id: int):
    """Get a workflow instance by ID.
    ---
    tags:
      - Workflows
    parameters:
      - name: instance_id
        in: path
        type: integer
        required: true
        description: Instance ID
      - name: include_jobs
        in: query
        type: boolean
        default: false
        description: Include job details
    responses:
      200:
        description: Workflow instance details
      404:
        description: Instance not found
    """
    include_jobs = request.args.get("include_jobs", "false").lower() == "true"

    with DatabaseSession() as db:
        instance = (
            db.query(WorkflowInstance)
            .filter(WorkflowInstance.id == instance_id)
            .first()
        )
        if not instance:
            raise NotFoundError("WorkflowInstance", instance_id)

        return success_response(instance.to_dict(include_jobs=include_jobs))


@workflows_bp.route("/<int:instance_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_instance(instance_id: int):
    """Cancel a running workflow instance.
    ---
    tags:
      - Workflows
    parameters:
      - name: instance_id
        in: path
        type: integer
        required: true
        description: Instance ID
    responses:
      200:
        description: Workflow cancelled
      400:
        description: Cannot cancel (not running)
      404:
        description: Instance not found
    """
    with DatabaseSession() as db:
        orchestrator = WorkflowOrchestrator(db)
        try:
            instance = orchestrator.cancel_workflow(instance_id)
            return success_response(instance.to_dict(include_jobs=True))
        except ValueError as e:
            if "not found" in str(e).lower():
                raise NotFoundError("WorkflowInstance", instance_id) from None
            raise ValidationError(str(e)) from None
