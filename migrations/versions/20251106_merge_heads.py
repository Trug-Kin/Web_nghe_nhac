"""
Merge all migration heads
Revision ID: 20251106_merge_heads
Revises: 5a0b924f6657, 20251106_add_ads_table
Create Date: 2025-11-06
"""
revision = '20251106_merge_heads'
down_revision = ('5a0b924f6657', '20251106_add_ads_table')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
