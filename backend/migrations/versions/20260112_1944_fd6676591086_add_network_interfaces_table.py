"""add_network_interfaces_table

Revision ID: fd6676591086
Revises: 5fea6ecb8e6a
Create Date: 2026-01-12 19:44:51.486202+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd6676591086'
down_revision: Union[str, Sequence[str], None] = '5fea6ecb8e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create network_interfaces table
    op.create_table('network_interfaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('interface_name', sa.String(length=50), nullable=False),
        sa.Column('mac_address', sa.String(length=17), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('subnet_mask', sa.String(length=45), nullable=True),
        sa.Column('gateway', sa.String(length=45), nullable=True),
        sa.Column('vlan_id', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('status', sa.Enum('UP', 'DOWN', 'DISABLED', name='interfacestatus'), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_network_interfaces_id'), 'network_interfaces', ['id'], unique=False)
    op.create_index(op.f('ix_network_interfaces_mac_address'), 'network_interfaces', ['mac_address'], unique=False)
    op.create_index(op.f('ix_network_interfaces_is_primary'), 'network_interfaces', ['is_primary'], unique=False)

    # Migrate existing ip_address and mac_address data from devices table
    # Only migrate if MAC address exists (required field for interfaces)
    connection = op.get_bind()

    # Get all devices with mac_address
    devices = connection.execute(
        sa.text("SELECT id, ip_address, mac_address FROM devices WHERE mac_address IS NOT NULL")
    ).fetchall()

    # Insert network interfaces for each device with MAC address
    for device_id, ip_address, mac_address in devices:
        connection.execute(
            sa.text(
                "INSERT INTO network_interfaces (device_id, interface_name, mac_address, ip_address, is_primary, status) "
                "VALUES (:device_id, :interface_name, :mac_address, :ip_address, :is_primary, :status)"
            ),
            {
                "device_id": device_id,
                "interface_name": "eth0",  # Default name for migrated interfaces
                "mac_address": mac_address,
                "ip_address": ip_address,
                "is_primary": True,  # Migrated interface is primary
                "status": "UP"
            }
        )

    # Keep the old columns for backward compatibility
    # They will be deprecated in a future migration after ensuring all clients updated


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_network_interfaces_is_primary'), table_name='network_interfaces')
    op.drop_index(op.f('ix_network_interfaces_mac_address'), table_name='network_interfaces')
    op.drop_index(op.f('ix_network_interfaces_id'), table_name='network_interfaces')
    op.drop_table('network_interfaces')
