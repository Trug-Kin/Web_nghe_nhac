"""Backfill uploader_id for existing genres

Revision ID: b123456789ac
Revises: b123456789ab
Create Date: 2025-11-11

Purpose:
    After adding uploader_id column to genres, existing rows have NULL.
    This migration assigns uploader_id = 1 (assumed admin) for any genre
    without an uploader. Adjust ADMIN_ID below if needed.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b123456789ac'
down_revision = 'b123456789ab'
branch_labels = None
depends_on = None

def upgrade():
    """Attempt to backfill genres.uploader_id to an existing admin user.

    More robust than hard-coding id=1: we search for an admin; if none exist,
    we fallback to any user; if still none, we skip backfill (leave NULLs).
    This prevents FOREIGN KEY errors on environments where user id 1 is absent.
    """
    bind = op.get_bind()
    admin_id = None
    # Try find admin
    try:
        res = bind.execute(sa.text("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1"))
        row = res.fetchone()
        if row:
            admin_id = row[0]
    except Exception:
        pass
    # Fallback to any user
    if admin_id is None:
        try:
            res2 = bind.execute(sa.text("SELECT id FROM users ORDER BY id LIMIT 1"))
            row2 = res2.fetchone()
            if row2:
                admin_id = row2[0]
        except Exception:
            pass
    if admin_id is None:
        print("[migration b123456789ac] No users found; skipping genre uploader_id backfill.")
        return
    # Perform update safely with parameter to avoid SQL injection
    bind.execute(sa.text("UPDATE genres SET uploader_id = :aid WHERE uploader_id IS NULL").bindparams(aid=admin_id))
    print(f"[migration b123456789ac] Backfilled genres.uploader_id to user {admin_id}")


def downgrade():
    # Downgrade: can't know which user we used; leave as-is (or set NULL for all rows that match a chosen user if needed)
    # Intentionally no-op to avoid wiping legitimate ownership.
    pass
