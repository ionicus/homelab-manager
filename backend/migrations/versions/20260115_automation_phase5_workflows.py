"""Add automation phase 5 - workflow templates and instances

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-01-15 14:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k1"
down_revision: str | Sequence[str] | None = "e5f6g7h8i9j0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Upgrade schema."""
    # Create workflow_templates table
    if not table_exists("workflow_templates"):
        op.create_table(
            "workflow_templates",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "name", sa.String(length=100), nullable=False, unique=True, index=True
            ),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("steps", sa.JSON(), nullable=False, default=list),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    # Create workflow_instances table
    if not table_exists("workflow_instances"):
        op.create_table(
            "workflow_instances",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "template_id",
                sa.Integer(),
                sa.ForeignKey("workflow_templates.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("template_snapshot", sa.JSON(), nullable=True),
            sa.Column(
                "status",
                sa.Enum(
                    "pending",
                    "running",
                    "completed",
                    "failed",
                    "cancelled",
                    "rolling_back",
                    "rolled_back",
                    name="workflowstatus",
                ),
                default="pending",
            ),
            sa.Column("device_ids", sa.JSON(), nullable=False),
            sa.Column("rollback_on_failure", sa.Boolean(), default=False),
            sa.Column("extra_vars", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    # Add workflow fields to automation_jobs table
    if not column_exists("automation_jobs", "workflow_instance_id"):
        op.add_column(
            "automation_jobs",
            sa.Column(
                "workflow_instance_id",
                sa.Integer(),
                sa.ForeignKey("workflow_instances.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not column_exists("automation_jobs", "step_order"):
        op.add_column(
            "automation_jobs",
            sa.Column("step_order", sa.Integer(), nullable=True),
        )

    if not column_exists("automation_jobs", "depends_on_job_ids"):
        op.add_column(
            "automation_jobs",
            sa.Column("depends_on_job_ids", sa.JSON(), nullable=True),
        )

    if not column_exists("automation_jobs", "is_rollback"):
        op.add_column(
            "automation_jobs",
            sa.Column("is_rollback", sa.Boolean(), default=False),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove workflow fields from automation_jobs
    if column_exists("automation_jobs", "is_rollback"):
        op.drop_column("automation_jobs", "is_rollback")

    if column_exists("automation_jobs", "depends_on_job_ids"):
        op.drop_column("automation_jobs", "depends_on_job_ids")

    if column_exists("automation_jobs", "step_order"):
        op.drop_column("automation_jobs", "step_order")

    if column_exists("automation_jobs", "workflow_instance_id"):
        op.drop_column("automation_jobs", "workflow_instance_id")

    # Drop workflow_instances table
    if table_exists("workflow_instances"):
        op.drop_table("workflow_instances")

    # Drop workflow_templates table
    if table_exists("workflow_templates"):
        op.drop_table("workflow_templates")

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS workflowstatus")
