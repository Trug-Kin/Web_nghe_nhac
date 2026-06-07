"""add is_public to playlists

Revision ID: 20251202_add_is_public
Revises: 5d1669904fd5
Create Date: 2025-12-02 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251202_add_is_public'
down_revision = '5d1669904fd5'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_public column to playlists table
    op.add_column('playlists', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove is_public column
    op.drop_column('playlists', 'is_public')
