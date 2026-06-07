"""add badge fields to artist_stats

Revision ID: 20251120_add_artist_stats_badge_fields
Revises: 20251120_add_artist_stats
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa

revision = '20251120_add_artist_stats_badge_fields'
down_revision = '20251120_add_artist_stats'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('artist_stats') as batch_op:
        batch_op.add_column(sa.Column('last_rank', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('appearances_count', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('first_seen_in_top_at', sa.TIMESTAMP(), nullable=True))


def downgrade():
    with op.batch_alter_table('artist_stats') as batch_op:
        batch_op.drop_column('first_seen_in_top_at')
        batch_op.drop_column('appearances_count')
        batch_op.drop_column('last_rank')
