"""
Revision ID: song_rank_stats_init
Revises: None
Create Date: 2025-10-30
"""

# Alembic identifiers
revision = 'song_rank_stats_init'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'song_rank_stats',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('song_id', sa.Integer(), sa.ForeignKey('songs.id'), nullable=False, index=True),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('week_plays', sa.Integer(), nullable=False, default=0),
        sa.Column('month_plays', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('song_rank_stats')
