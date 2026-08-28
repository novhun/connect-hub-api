"""add_events_support_settings_profile

Revision ID: 2f6a9c3d7b1e
Revises: 189fbac443f8
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f6a9c3d7b1e'
down_revision: Union[str, None] = '189fbac443f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- User profile fields ---
    op.add_column('users', sa.Column('job_title', sa.String(length=150), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=150), nullable=True))

    # --- Events ---
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('creator_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('cover_image', sa.Text(), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_creator_id'), 'events', ['creator_id'], unique=False)
    op.create_index(op.f('ix_events_start_at'), 'events', ['start_at'], unique=False)

    op.create_table(
        'event_attendees',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_event_user_attendee'),
    )
    op.create_index(op.f('ix_event_attendees_id'), 'event_attendees', ['id'], unique=False)
    op.create_index(op.f('ix_event_attendees_event_id'), 'event_attendees', ['event_id'], unique=False)
    op.create_index(op.f('ix_event_attendees_user_id'), 'event_attendees', ['user_id'], unique=False)

    # --- Support messages ---
    op.create_table(
        'support_messages',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_support_messages_id'), 'support_messages', ['id'], unique=False)
    op.create_index(op.f('ix_support_messages_user_id'), 'support_messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_support_messages_created_at'), 'support_messages', ['created_at'], unique=False)

    # --- User settings ---
    op.create_table(
        'user_settings',
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('push_notifications', sa.Boolean(), nullable=True),
        sa.Column('call_ringtone', sa.Boolean(), nullable=True),
        sa.Column('default_audience', sa.String(length=20), nullable=True),
        sa.Column('show_online_status', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )
    op.create_index(op.f('ix_user_settings_user_id'), 'user_settings', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_table('user_settings')

    op.drop_index(op.f('ix_support_messages_created_at'), table_name='support_messages')
    op.drop_index(op.f('ix_support_messages_user_id'), table_name='support_messages')
    op.drop_index(op.f('ix_support_messages_id'), table_name='support_messages')
    op.drop_table('support_messages')

    op.drop_index(op.f('ix_event_attendees_user_id'), table_name='event_attendees')
    op.drop_index(op.f('ix_event_attendees_event_id'), table_name='event_attendees')
    op.drop_index(op.f('ix_event_attendees_id'), table_name='event_attendees')
    op.drop_table('event_attendees')

    op.drop_index(op.f('ix_events_start_at'), table_name='events')
    op.drop_index(op.f('ix_events_creator_id'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')

    op.drop_column('users', 'location')
    op.drop_column('users', 'job_title')
