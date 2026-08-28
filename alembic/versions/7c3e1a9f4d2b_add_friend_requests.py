"""add_friend_requests

Revision ID: 7c3e1a9f4d2b
Revises: 2f6a9c3d7b1e
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c3e1a9f4d2b'
down_revision: Union[str, None] = '2f6a9c3d7b1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'friend_requests',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('sender_id', sa.String(length=64), nullable=False),
        sa.Column('receiver_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sender_id', 'receiver_id', name='uq_friend_request_pair'),
    )
    op.create_index(op.f('ix_friend_requests_id'), 'friend_requests', ['id'], unique=False)
    op.create_index(op.f('ix_friend_requests_sender_id'), 'friend_requests', ['sender_id'], unique=False)
    op.create_index(op.f('ix_friend_requests_receiver_id'), 'friend_requests', ['receiver_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_friend_requests_receiver_id'), table_name='friend_requests')
    op.drop_index(op.f('ix_friend_requests_sender_id'), table_name='friend_requests')
    op.drop_index(op.f('ix_friend_requests_id'), table_name='friend_requests')
    op.drop_table('friend_requests')
