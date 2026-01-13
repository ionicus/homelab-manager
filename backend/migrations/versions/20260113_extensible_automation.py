"""Add extensible automation fields to automation_jobs

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-13

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    """Add executor_type, rename playbook_name to action_name, add action_config."""
    # Add executor_type column with default value
    op.add_column(
        "automation_jobs",
        sa.Column(
            "executor_type",
            sa.String(50),
            nullable=False,
            server_default="ansible",
        ),
    )

    # Rename playbook_name to action_name
    op.alter_column(
        "automation_jobs",
        "playbook_name",
        new_column_name="action_name",
    )

    # Add action_config column for executor-specific configuration
    op.add_column(
        "automation_jobs",
        sa.Column("action_config", sa.JSON, nullable=True),
    )


def downgrade():
    """Remove extensible automation fields."""
    # Drop action_config column
    op.drop_column("automation_jobs", "action_config")

    # Rename action_name back to playbook_name
    op.alter_column(
        "automation_jobs",
        "action_name",
        new_column_name="playbook_name",
    )

    # Drop executor_type column
    op.drop_column("automation_jobs", "executor_type")
