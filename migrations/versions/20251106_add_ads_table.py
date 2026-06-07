"""
Add ads table for Ad model (with mp3_path)
Revision ID: 20251106_add_ads_table
Revises: 5a0b924f6657
Create Date: 2025-11-06
"""
revision = '20251106_add_ads_table'
down_revision = '5a0b924f6657'
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Create ads table if it does not already exist.

    This migration previously failed with OperationalError (table exists) when the
    table had been created manually or by an earlier merged head. We guard creation
    to make the migration idempotent across environments.
    """
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'ads' in inspector.get_table_names():
        # Table already present; skip creation to avoid 1050 error
        return
    op.create_table(
        'ads',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('image_url', sa.String(255)),
        sa.Column('link', sa.String(255)),
        sa.Column('mp3_path', sa.String(255)),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade():
    # Only drop if exists to mirror guarded upgrade
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'ads' in inspector.get_table_names():
        op.drop_table('ads')
