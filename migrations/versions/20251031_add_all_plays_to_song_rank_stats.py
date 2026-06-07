"""add all_plays to song_rank_stats

Revision ID: add_all_plays_to_song_rank_stats
Revises: 5a0b924f6657
Create Date: 2025-10-31
"""

revision = 'add_all_plays_to_song_rank_stats'
down_revision = '5a0b924f6657'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('song_rank_stats', sa.Column('all_plays', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('song_rank_stats', 'all_plays', server_default=None)

def downgrade():
    op.drop_column('song_rank_stats', 'all_plays')
