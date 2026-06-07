"""Add added_at column to playlist_songs for insertion ordering

Revision ID: add_added_at_to_playlist_songs
Revises: merge_post_genre_heads
Create Date: 2025-11-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_added_at_to_playlist_songs'
down_revision = 'merge_post_genre_heads'
branch_labels = None
depends_on = None

def upgrade():
    # Add added_at with current timestamp default
    op.add_column('playlist_songs', sa.Column('added_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
    # Optional: backfill ordering by assigning incremental offsets (MySQL: keep same CURRENT_TIMESTAMP; deeper ordering unavailable without historical data)
    # Could later run an update procedure if we stored historical order elsewhere.


def downgrade():
    op.drop_column('playlist_songs', 'added_at')
