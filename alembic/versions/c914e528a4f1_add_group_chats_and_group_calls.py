"""add_group_chats_and_group_calls

Revision ID: c914e528a4f1
Revises: b8873e33f8d5
Create Date: 2026-09-25 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c914e528a4f1'
down_revision: Union[str, None] = 'b8873e33f8d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. group_chats table
    if 'group_chats' not in existing_tables:
        op.create_table(
            'group_chats',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('avatar', sa.Text(), nullable=True),
            sa.Column('creator_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('invite_code', sa.String(length=32), unique=True, index=True, nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        )

    # 2. group_chat_members table
    if 'group_chat_members' not in existing_tables:
        op.create_table(
            'group_chat_members',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('group_chat_id', sa.String(length=64), sa.ForeignKey('group_chats.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(length=32), server_default='member', nullable=False),
            sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        )

    # 3. group_chat_messages table
    if 'group_chat_messages' not in existing_tables:
        op.create_table(
            'group_chat_messages',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('group_chat_id', sa.String(length=64), sa.ForeignKey('group_chats.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('sender_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('media_url', sa.Text(), nullable=True),
            sa.Column('message_type', sa.String(length=32), server_default='text', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        )

    # 4. update call_sessions columns
    if 'call_sessions' in existing_tables:
        call_columns = {col['name'] for col in inspector.get_columns('call_sessions')}
        if 'group_id' not in call_columns:
            op.add_column('call_sessions', sa.Column('group_id', sa.String(length=64), nullable=True, index=True))
        if 'is_group_call' not in call_columns:
            op.add_column('call_sessions', sa.Column('is_group_call', sa.Boolean(), server_default=sa.false(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'call_sessions' in existing_tables:
        call_columns = {col['name'] for col in inspector.get_columns('call_sessions')}
        if 'is_group_call' in call_columns:
            op.drop_column('call_sessions', 'is_group_call')
        if 'group_id' in call_columns:
            op.drop_column('call_sessions', 'group_id')

    if 'group_chat_messages' in existing_tables:
        op.drop_table('group_chat_messages')
    if 'group_chat_members' in existing_tables:
        op.drop_table('group_chat_members')
    if 'group_chats' in existing_tables:
        op.drop_table('group_chats')
