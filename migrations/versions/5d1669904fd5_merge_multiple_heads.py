"""merge_multiple_heads

Revision ID: 5d1669904fd5
Revises: 20251120_add_search_events_and_moving_avg, add_added_at_to_playlist_songs
Create Date: 2025-12-02 18:40:06.001783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d1669904fd5'
down_revision = ('20251120_add_search_events_and_moving_avg', 'add_added_at_to_playlist_songs')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
