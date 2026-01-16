"""Add app_settings table for configurable application settings.

Revision ID: 20260116_add_app_settings
Revises: 20260116_add_cancelled
Create Date: 2026-01-16

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade():
    """Create app_settings table and insert default values."""
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_app_settings_id"), "app_settings", ["id"], unique=False)
    op.create_index(op.f("ix_app_settings_key"), "app_settings", ["key"], unique=True)

    # Insert default settings
    op.execute(
        """
        INSERT INTO app_settings (key, value, description) VALUES
        ('session_timeout_minutes', '60', 'Session timeout in minutes (default: 60)'),
        ('max_login_attempts', '5', 'Maximum failed login attempts before lockout'),
        ('lockout_duration_minutes', '15', 'Account lockout duration in minutes after max failed attempts')
    """
    )


def downgrade():
    """Drop app_settings table."""
    op.drop_index(op.f("ix_app_settings_key"), table_name="app_settings")
    op.drop_index(op.f("ix_app_settings_id"), table_name="app_settings")
    op.drop_table("app_settings")
