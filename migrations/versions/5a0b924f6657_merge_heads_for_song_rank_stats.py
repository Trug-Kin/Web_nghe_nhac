"""merge heads for song_rank_stats

Revision ID: 5a0b924f6657
Revises: 162344846782, song_rank_stats_init
Create Date: 2025-10-30 11:21:30.154311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a0b924f6657'
down_revision = ('162344846782', 'song_rank_stats_init')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
