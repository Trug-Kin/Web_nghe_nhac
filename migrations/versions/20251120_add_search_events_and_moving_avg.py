"""add search_events table and moving_avg_score column

Revision ID: 20251120_add_search_events_and_moving_avg
Revises: 20251120_add_artist_stats_badge_fields
Create Date: 2025-11-20
"""
from alembic import op
import sqlalchemy as sa

revision = '20251120_add_search_events_and_moving_avg'
down_revision = '20251120_add_artist_stats_badge_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add moving_avg_score column
    with op.batch_alter_table('artist_stats') as batch_op:
        batch_op.add_column(sa.Column('moving_avg_score', sa.Float(), server_default='0'))
    # Create search_events table
    op.create_table('search_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('artist_id', sa.Integer(), sa.ForeignKey('artists.id'), nullable=True),
        sa.Column('query', sa.String(length=200), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp())
    )
    op.create_index('ix_search_events_artist_id', 'search_events', ['artist_id'])
    op.create_index('ix_search_events_created_at', 'search_events', ['created_at'])


def downgrade():
    op.drop_index('ix_search_events_created_at', table_name='search_events')
    op.drop_index('ix_search_events_artist_id', table_name='search_events')
    op.drop_table('search_events')
    with op.batch_alter_table('artist_stats') as batch_op:
        batch_op.drop_column('moving_avg_score')
