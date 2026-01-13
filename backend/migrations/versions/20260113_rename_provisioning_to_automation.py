"""Rename provisioning_jobs table to automation_jobs

Revision ID: a1b2c3d4e5f6
Revises: fd6676591086
Create Date: 2026-01-13

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "fd6676591086"
branch_labels = None
depends_on = None


def upgrade():
    """Rename provisioning_jobs table to automation_jobs."""
    # Rename the table
    op.rename_table("provisioning_jobs", "automation_jobs")

    # The index on device_id is created via ForeignKey,
    # so it will be renamed with the table


def downgrade():
    """Revert automation_jobs table back to provisioning_jobs."""
    op.rename_table("automation_jobs", "provisioning_jobs")
