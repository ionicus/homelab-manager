"""Add automation phase 1 - variables and progress tracking

Revision ID: c3d4e5f6g7h8
Revises: 113473d262e7
Create Date: 2026-01-14 21:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = '113473d262e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to automation_jobs table (idempotent)
    columns_to_add = [
        ('extra_vars', sa.Column('extra_vars', sa.JSON(), nullable=True)),
        ('progress', sa.Column('progress', sa.Integer(), nullable=False, server_default='0')),
        ('task_count', sa.Column('task_count', sa.Integer(), nullable=False, server_default='0')),
        ('tasks_completed', sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0')),
        ('error_category', sa.Column('error_category', sa.String(length=50), nullable=True)),
        ('cancel_requested', sa.Column('cancel_requested', sa.Boolean(), nullable=False, server_default='false')),
        ('cancelled_at', sa.Column('cancelled_at', sa.DateTime(), nullable=True)),
        ('celery_task_id', sa.Column('celery_task_id', sa.String(length=255), nullable=True)),
    ]

    for col_name, col_obj in columns_to_add:
        if not column_exists('automation_jobs', col_name):
            op.add_column('automation_jobs', col_obj)

    # Create device_variables table (idempotent)
    if not table_exists('device_variables'):
        op.create_table(
            'device_variables',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('device_id', sa.Integer(), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False),
            sa.Column('playbook_name', sa.String(length=100), nullable=True),
            sa.Column('variables', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.UniqueConstraint('device_id', 'playbook_name', name='uq_device_playbook'),
        )
        op.create_index('ix_device_variables_device_id', 'device_variables', ['device_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop device_variables table
    if table_exists('device_variables'):
        op.drop_index('ix_device_variables_device_id', 'device_variables')
        op.drop_table('device_variables')

    # Remove columns from automation_jobs table
    columns_to_drop = [
        'celery_task_id', 'cancelled_at', 'cancel_requested', 'error_category',
        'tasks_completed', 'task_count', 'progress', 'extra_vars'
    ]
    for col_name in columns_to_drop:
        if column_exists('automation_jobs', col_name):
            op.drop_column('automation_jobs', col_name)
