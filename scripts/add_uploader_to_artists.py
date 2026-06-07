"""
Script để thêm cột uploader_id vào bảng artists
"""
import sys
import os

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from src.models import db
from app import create_app

def add_uploader_to_artists():
    """Thêm cột uploader_id vào bảng artists nếu chưa có"""
    app = create_app()
    with app.app_context():
        try:
            # Kiểm tra xem cột đã tồn tại chưa
            result = db.session.execute(text("SHOW COLUMNS FROM artists LIKE 'uploader_id'"))
            column_exists = result.fetchone() is not None
            
            if column_exists:
                print("✓ Cột uploader_id đã tồn tại trong bảng artists")
                return
            
            print("Đang thêm cột uploader_id vào bảng artists...")
            
            # Thêm cột uploader_id
            db.session.execute(text("""
                ALTER TABLE artists 
                ADD COLUMN uploader_id INT NULL
            """))
            
            # Thêm foreign key constraint
            db.session.execute(text("""
                ALTER TABLE artists 
                ADD CONSTRAINT fk_artists_uploader 
                FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL
            """))
            
            db.session.commit()
            print("✓ Đã thêm cột uploader_id vào bảng artists thành công!")
            
            # Kiểm tra kết quả
            result = db.session.execute(text("DESCRIBE artists"))
            print("\nCấu trúc bảng artists sau khi thêm cột:")
            for row in result:
                print(f"  {row[0]}: {row[1]} {row[2]}")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Lỗi khi thêm cột: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_uploader_to_artists()
