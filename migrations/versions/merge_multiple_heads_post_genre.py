"""Merge heads after adding genre uploader id

Revision ID: merge_post_genre_heads
Revises: 20251106_merge_heads, 5015d4954457, b123456789ac
Create Date: 2025-11-11

Purpose:
    Unify three divergent heads so future upgrades (including genre uploader column) proceed.
    This merge revision has no schema changes.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_post_genre_heads'
down_revision = ('20251106_merge_heads', '5015d4954457', 'b123456789ac')
branch_labels = None
depends_on = None


def upgrade():
    # No operations; purely merges heads.
    pass


def downgrade():
    # Downgrade would re-create the split (not recommended). Leave empty.
    pass
