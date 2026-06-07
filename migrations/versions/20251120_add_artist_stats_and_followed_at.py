"""add artist_stats table and followed_at column

Revision ID: 20251120_add_artist_stats
Revises: 20251106_add_ads_table  # adjust to latest head if different
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251120_add_artist_stats'
down_revision = '20251106_add_ads_table'  # update to actual latest head if needed
branch_labels = None
depends_on = None

def upgrade():
    # Add followed_at to user_artist_followers if not exists
    with op.batch_alter_table('user_artist_followers') as batch_op:
        batch_op.add_column(sa.Column('followed_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp()))
    # Create artist_stats table
    op.create_table('artist_stats',
        sa.Column('artist_id', sa.Integer(), sa.ForeignKey('artists.id'), primary_key=True),
        sa.Column('streams_current', sa.Integer(), server_default='0'),
        sa.Column('streams_previous', sa.Integer(), server_default='0'),
        sa.Column('followers_new', sa.Integer(), server_default='0'),
        sa.Column('playlist_adds', sa.Integer(), server_default='0'),
        sa.Column('search_hits', sa.Integer(), server_default='0'),
        sa.Column('social_mentions', sa.Integer(), server_default='0'),
        sa.Column('growth_rate', sa.Float(), server_default='0'),
        sa.Column('rising_score', sa.Float(), server_default='0'),
        sa.Column('window_start', sa.TIMESTAMP(), nullable=True),
        sa.Column('window_end', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp())
    )
    op.create_index('ix_artist_stats_rising_score', 'artist_stats', ['rising_score'])


def downgrade():
    op.drop_index('ix_artist_stats_rising_score', table_name='artist_stats')
    op.drop_table('artist_stats')
    with op.batch_alter_table('user_artist_followers') as batch_op:
        batch_op.drop_column('followed_at')
