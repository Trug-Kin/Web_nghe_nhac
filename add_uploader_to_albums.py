"""
Script to add uploader_id column to albums table
"""
from app import create_app
from src.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Kiểm tra xem cột đã tồn tại chưa
        result = db.session.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'Flask_Web' 
            AND TABLE_NAME = 'albums' 
            AND COLUMN_NAME = 'uploader_id'
        """))
        count = result.fetchone()[0]
        
        if count == 0:
            print("Adding uploader_id column to albums table...")
            db.session.execute(text("""
                ALTER TABLE albums 
                ADD COLUMN uploader_id INT NULL
            """))
            db.session.commit()
            print("✓ Column uploader_id added successfully!")
            
            # Thêm foreign key constraint
            print("Adding foreign key constraint...")
            db.session.execute(text("""
                ALTER TABLE albums 
                ADD CONSTRAINT fk_albums_uploader 
                FOREIGN KEY (uploader_id) REFERENCES users(id)
            """))
            db.session.commit()
            print("✓ Foreign key constraint added successfully!")
        else:
            print("✓ Column uploader_id already exists in albums table")
            
        # Kiểm tra và cập nhật artist_id thành nullable nếu cần
        result = db.session.execute(text("""
            SELECT IS_NULLABLE FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'Flask_Web' 
            AND TABLE_NAME = 'albums' 
            AND COLUMN_NAME = 'artist_id'
        """))
        is_nullable = result.fetchone()[0]
        
        if is_nullable == 'NO':
            print("Making artist_id nullable...")
            db.session.execute(text("""
                ALTER TABLE albums 
                MODIFY COLUMN artist_id INT NULL
            """))
            db.session.commit()
            print("✓ artist_id is now nullable!")
        else:
            print("✓ artist_id is already nullable")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        db.session.rollback()
