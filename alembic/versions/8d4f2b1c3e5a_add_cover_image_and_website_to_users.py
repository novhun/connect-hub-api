"""add_cover_image_and_website_to_users

Revision ID: 8d4f2b1c3e5a
Revises: 7c3e1a9f4d2b
Create Date: 2026-08-28 22:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d4f2b1c3e5a'
down_revision: Union[str, None] = '7c3e1a9f4d2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cover_image and website to users table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'cover_image' not in user_columns:
        op.add_column('users', sa.Column('cover_image', sa.Text(), nullable=True))
    if 'website' not in user_columns:
        op.add_column('users', sa.Column('website', sa.String(length=255), nullable=True))
    if 'job_title' not in user_columns:
        op.add_column('users', sa.Column('job_title', sa.String(length=150), nullable=True))
    if 'location' not in user_columns:
        op.add_column('users', sa.Column('location', sa.String(length=150), nullable=True))
    if 'is_verified' not in user_columns:
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'location')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'website')
    op.drop_column('users', 'cover_image')
