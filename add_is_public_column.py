from app import create_app
from src.extensions import db

app = create_app()

with app.app_context():
    # Add is_public column to playlists table
    sql = "ALTER TABLE playlists ADD COLUMN is_public TINYINT(1) NOT NULL DEFAULT 0"
    try:
        db.session.execute(db.text(sql))
        db.session.commit()
        print("✅ Successfully added is_public column to playlists table")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
