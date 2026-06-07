"""
Script Python để tạo bảng likes và comments cho MySQL
"""
import pymysql
import os

# Thông tin kết nối MySQL (lấy từ config)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kin0919136592',
    'database': 'Flask_Web',
    'charset': 'utf8mb4'
}

# SQL script cho MySQL
sql_script = """
-- Tạo bảng likes
CREATE TABLE IF NOT EXISTS likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    song_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_song_like (user_id, song_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tạo bảng comments  
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    song_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tạo index để tăng hiệu suất
CREATE INDEX idx_likes_song_id ON likes(song_id);
CREATE INDEX idx_likes_user_id ON likes(user_id);
CREATE INDEX idx_comments_song_id ON comments(song_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
"""

try:
    # Kết nối MySQL
    print("🔌 Đang kết nối MySQL...")
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # Tách và chạy từng câu lệnh SQL
    statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for statement in statements:
        if statement:
            print(f"⚙️  Executing: {statement[:50]}...")
            cursor.execute(statement)
    
    connection.commit()
    
    # Kiểm tra bảng đã tạo
    cursor.execute("SHOW TABLES LIKE 'likes'")
    likes_table = cursor.fetchone()
    
    cursor.execute("SHOW TABLES LIKE 'comments'")
    comments_table = cursor.fetchone()
    
    print("\n✅ Migration thành công!")
    if likes_table:
        print("   ✓ Bảng 'likes' đã được tạo")
    if comments_table:
        print("   ✓ Bảng 'comments' đã được tạo")
    
    # Kiểm tra cấu trúc bảng
    print("\n📋 Cấu trúc bảng likes:")
    cursor.execute("DESCRIBE likes")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]}")
    
    print("\n📋 Cấu trúc bảng comments:")
    cursor.execute("DESCRIBE comments")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]}")
    
    # Kiểm tra index
    print("\n🔍 Indexes:")
    cursor.execute("SHOW INDEX FROM likes WHERE Key_name != 'PRIMARY'")
    for row in cursor.fetchall():
        print(f"   - likes.{row[4]}")
    
    cursor.execute("SHOW INDEX FROM comments WHERE Key_name != 'PRIMARY'")
    for row in cursor.fetchall():
        print(f"   - comments.{row[4]}")
    
    cursor.close()
    connection.close()
    print("\n✅ Hoàn tất!")
    
except pymysql.Error as e:
    print(f"❌ Lỗi MySQL: {e}")
except Exception as e:
    print(f"❌ Lỗi: {e}")
