"""merge heads

Revision ID: 5015d4954457
Revises: add_all_plays_to_song_rank_stats, 20251103_add_user_artist_followers
Create Date: 2025-11-03 08:48:41.797656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5015d4954457'
down_revision = ('add_all_plays_to_song_rank_stats', '20251103_add_user_artist_followers')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
