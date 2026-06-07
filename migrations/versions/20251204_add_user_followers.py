"""Add user followers table

Revision ID: add_user_followers
Revises: 
Create Date: 2025-12-04

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_user_followers'
down_revision = '20251202_add_is_public'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create user_followers table
    op.create_table(
        'user_followers',
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('followed_id', sa.Integer(), nullable=False),
        sa.Column('followed_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['followed_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('follower_id', 'followed_id')
    )


def downgrade():
    op.drop_table('user_followers')
