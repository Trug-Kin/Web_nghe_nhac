"""
Alembic migration template to add uploader_id to songs and playlist fields.
Place this file in migrations/versions and run `flask db upgrade` after verifying env.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251020_add_playlist_uploader_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add uploader_id to songs
    with op.batch_alter_table('songs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uploader_id', sa.Integer(), nullable=True))
        try:
            batch_op.create_foreign_key('fk_songs_uploader_id_users', 'users', ['uploader_id'], ['id'])
        except Exception:
            # If foreign key creation fails (e.g., users table not present yet), skip and let manual migration handle it
            pass

    # Add fields to playlists
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        # add user_id if missing
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        try:
            batch_op.create_foreign_key('fk_playlists_user_id_users', 'users', ['user_id'], ['id'])
        except Exception:
            pass
        batch_op.add_column(sa.Column('description', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('cover_image_path', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.drop_column('cover_image_path')
        batch_op.drop_column('description')
        try:
            batch_op.drop_constraint('fk_playlists_user_id_users', type_='foreignkey')
        except Exception:
            pass
        batch_op.drop_column('user_id')

    with op.batch_alter_table('songs', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('fk_songs_uploader_id_users', type_='foreignkey')
        except Exception:
            pass
        batch_op.drop_column('uploader_id')
