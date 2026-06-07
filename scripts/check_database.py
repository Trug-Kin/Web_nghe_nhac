"""
Script kiểm tra dữ liệu trong MySQL database Flask_Web
"""
import pymysql

# Kết nối database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Kin0919136592',
    database='Flask_Web',
    charset='utf8mb4'
)

try:
    cursor = conn.cursor()
    
    print("=" * 60)
    print("KIỂM TRA DATABASE FLASK_WEB")
    print("=" * 60)
    
    # 1. Kiểm tra tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n📋 Có {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 2. Kiểm tra table LIKES
    print("\n" + "=" * 60)
    print("❤️  TABLE: likes")
    print("=" * 60)
    cursor.execute("DESCRIBE likes")
    print("Cấu trúc:")
    for col in cursor.fetchall():
        print(f"  {col[0]:15s} {col[1]:20s} {col[2]:5s} {col[3]}")
    
    cursor.execute("SELECT COUNT(*) FROM likes")
    like_count = cursor.fetchone()[0]
    print(f"\n✅ Tổng số likes: {like_count}")
    
    if like_count > 0:
        cursor.execute("""
            SELECT l.id, l.user_id, u.username, l.song_id, s.title, l.created_at
            FROM likes l
            JOIN users u ON l.user_id = u.id
            JOIN songs s ON l.song_id = s.id
            ORDER BY l.created_at DESC
            LIMIT 5
        """)
        print("\n5 likes gần nhất:")
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, User: {row[2]} (ID={row[1]}), Song: {row[4]} (ID={row[3]}), Time: {row[5]}")
    
    # 3. Kiểm tra table COMMENTS
    print("\n" + "=" * 60)
    print("💬 TABLE: comments")
    print("=" * 60)
    cursor.execute("DESCRIBE comments")
    print("Cấu trúc:")
    for col in cursor.fetchall():
        print(f"  {col[0]:15s} {col[1]:20s} {col[2]:5s} {col[3]}")
    
    cursor.execute("SELECT COUNT(*) FROM comments")
    comment_count = cursor.fetchone()[0]
    print(f"\n✅ Tổng số comments: {comment_count}")
    
    if comment_count > 0:
        cursor.execute("""
            SELECT c.id, c.user_id, u.username, c.song_id, s.title, 
                   LEFT(c.content, 50) as preview, c.created_at
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN songs s ON c.song_id = s.id
            ORDER BY c.created_at DESC
            LIMIT 5
        """)
        print("\n5 comments gần nhất:")
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, User: {row[2]}, Song: {row[4]}")
            print(f"    Content: {row[5]}...")
            print(f"    Time: {row[6]}")
    
    # 4. Kiểm tra table LISTENING_HISTORY
    print("\n" + "=" * 60)
    print("🎧 TABLE: listening_history")
    print("=" * 60)
    cursor.execute("DESCRIBE listening_history")
    print("Cấu trúc:")
    for col in cursor.fetchall():
        print(f"  {col[0]:15s} {col[1]:20s} {col[2]:5s} {col[3]}")
    
    cursor.execute("SELECT COUNT(*) FROM listening_history")
    history_count = cursor.fetchone()[0]
    print(f"\n✅ Tổng số lượt nghe: {history_count}")
    
    if history_count > 0:
        # Top 5 bài hát được nghe nhiều nhất
        cursor.execute("""
            SELECT s.id, s.title, a.name as artist, COUNT(lh.id) as play_count
            FROM listening_history lh
            JOIN songs s ON lh.song_id = s.id
            JOIN artists a ON s.artist_id = a.id
            GROUP BY s.id, s.title, a.name
            ORDER BY play_count DESC
            LIMIT 5
        """)
        print("\n🔥 Top 5 bài hát được nghe nhiều nhất:")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row[1]} - {row[2]} ({row[3]} lượt)")
    
    # 5. Kiểm tra USERS
    print("\n" + "=" * 60)
    print("👤 TABLE: users")
    print("=" * 60)
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✅ Tổng số users: {user_count}")
    
    cursor.execute("""
        SELECT id, username, email, role 
        FROM users 
        ORDER BY id 
        LIMIT 10
    """)
    print("\nDanh sách users:")
    for row in cursor.fetchall():
        print(f"  ID={row[0]}, Username: {row[1]}, Email: {row[2]}, Role: {row[3]}")
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH KIỂM TRA!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
finally:
    conn.close()
