"""add_device_tokens_table

Revision ID: 3b88770fd923
Revises: 2a77669ec812
Create Date: 2026-08-31 20:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b88770fd923'
down_revision: Union[str, None] = '2a77669ec812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('fcm_token', sa.String(length=512), nullable=False),
        sa.Column('platform', sa.String(length=32), nullable=False, server_default='ANDROID'),
        sa.Column('device_name', sa.String(length=128), nullable=True),
        sa.Column('app_version', sa.String(length=32), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('topic_subscriptions', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deactivation_reason', sa.String(length=255), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_device_tokens_fcm_token', 'device_tokens', ['fcm_token'], unique=True)
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])
    op.create_index('ix_device_tokens_platform', 'device_tokens', ['platform'])
    op.create_index('ix_device_tokens_is_active', 'device_tokens', ['is_active'])
    op.create_index('idx_device_active_platform', 'device_tokens', ['is_active', 'platform'])
    op.create_index('idx_device_user_active', 'device_tokens', ['user_id', 'is_active'])


def downgrade() -> None:
    op.drop_index('idx_device_user_active', table_name='device_tokens')
    op.drop_index('idx_device_active_platform', table_name='device_tokens')
    op.drop_index('ix_device_tokens_is_active', table_name='device_tokens')
    op.drop_index('ix_device_tokens_platform', table_name='device_tokens')
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    op.drop_index('ix_device_tokens_fcm_token', table_name='device_tokens')
    op.drop_table('device_tokens')
