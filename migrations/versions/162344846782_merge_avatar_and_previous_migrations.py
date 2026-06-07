"""merge avatar and previous migrations

Revision ID: 162344846782
Revises: add_avatar_to_users, a360c5be2bc0
Create Date: 2025-10-22 21:59:42.530039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '162344846782'
down_revision = ('add_avatar_to_users', 'a360c5be2bc0')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
