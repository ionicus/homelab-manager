"""Add automation phase 4 - vault secrets table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-15 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j0"
down_revision: str | Sequence[str] | None = "d4e5f6g7h8i9"
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
    # Create vault_secrets table (idempotent)
    if not table_exists("vault_secrets"):
        op.create_table(
            "vault_secrets",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "name", sa.String(length=100), nullable=False, unique=True, index=True
            ),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("encrypted_content", sa.LargeBinary(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    # Add vault_secret_id column to automation_jobs table
    if not column_exists("automation_jobs", "vault_secret_id"):
        op.add_column(
            "automation_jobs",
            sa.Column(
                "vault_secret_id",
                sa.Integer(),
                sa.ForeignKey("vault_secrets.id"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove vault_secret_id from automation_jobs
    if column_exists("automation_jobs", "vault_secret_id"):
        op.drop_column("automation_jobs", "vault_secret_id")

    # Drop vault_secrets table
    if table_exists("vault_secrets"):
        op.drop_table("vault_secrets")
