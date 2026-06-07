"""Merge migration heads

Revision ID: be1de514d759
Revises: 20251020_add_playlist_uploader_fields, 25024ef1562b
Create Date: 2025-10-21 11:32:19.277826

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be1de514d759'
down_revision = ('20251020_add_playlist_uploader_fields', '25024ef1562b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
