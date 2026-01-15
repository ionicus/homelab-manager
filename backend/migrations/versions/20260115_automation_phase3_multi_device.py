"""Add automation phase 3 - multi-device support

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-15 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: str | Sequence[str] | None = "c3d4e5f6g7h8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Upgrade schema."""
    # Add device_ids column to automation_jobs table for multi-device support
    if not column_exists("automation_jobs", "device_ids"):
        op.add_column(
            "automation_jobs",
            sa.Column("device_ids", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove device_ids column from automation_jobs table
    if column_exists("automation_jobs", "device_ids"):
        op.drop_column("automation_jobs", "device_ids")
