"""Add CANCELLED value to jobstatus enum.

Revision ID: 20260116_add_cancelled
Revises: 20260115_automation_phase5_workflows
Create Date: 2026-01-16

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "g7h8i9j0k1l2"
down_revision = "f6g7h8i9j0k1"
branch_labels = None
depends_on = None


def upgrade():
    """Add CANCELLED to the jobstatus enum."""
    # PostgreSQL requires ALTER TYPE to add new enum values
    op.execute("ALTER TYPE jobstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade():
    """Cannot remove enum values in PostgreSQL without recreating the type."""
    # PostgreSQL doesn't support removing enum values directly
    # This would require recreating the entire type and migrating data
    pass
