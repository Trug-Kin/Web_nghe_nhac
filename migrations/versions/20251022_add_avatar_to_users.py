"""add avatar to users

Revision ID: add_avatar_to_users
Revises: 
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_avatar_to_users'
down_revision = None
depends_on = None


def upgrade():
    # Add avatar column to users table
    op.add_column('users', sa.Column('avatar', sa.String(length=255), nullable=True, server_default='images/default.jpg'))


def downgrade():
    # Remove avatar column from users table
    op.drop_column('users', 'avatar')
