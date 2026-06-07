"""
Revision ID: 20251103_add_user_artist_followers
Revises: 
Create Date: 2025-11-03
"""

revision = '20251103_add_user_artist_followers'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Bảng đã tồn tại, không tạo lại
    pass

def downgrade():
    op.drop_table('user_artist_followers')
