"""Add uploader_id to genres table

Revision ID: b123456789ab
Revises: 
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b123456789ab'
# Chain after latest existing migration that introduced albums uploader & merge heads
# Use the revision id from the last applied migration (a360c5be2bc0 depends on be1de514d759, so we continue after a360c5be2bc0)
down_revision = 'a360c5be2bc0'
branch_labels = None
depends_on = None

def _column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for col in insp.get_columns(table_name):
        if col['name'] == column_name:
            return True
    return False

def upgrade():
    # Add uploader_id column to genres if not exists
    if not _column_exists('genres', 'uploader_id'):
        op.add_column('genres', sa.Column('uploader_id', sa.Integer(), nullable=True))
        # Create FK constraint to users.id
        op.create_foreign_key('fk_genres_uploader_id_users', 'genres', 'users', ['uploader_id'], ['id'])


def downgrade():
    # Drop FK then column if exists
    bind = op.get_bind()
    insp = sa.inspect(bind)
    fk_names = [fk['name'] for fk in insp.get_foreign_keys('genres')]
    if 'fk_genres_uploader_id_users' in fk_names:
        op.drop_constraint('fk_genres_uploader_id_users', 'genres', type_='foreignkey')
    if _column_exists('genres', 'uploader_id'):
        op.drop_column('genres', 'uploader_id')
