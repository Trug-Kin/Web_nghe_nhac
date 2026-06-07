"""Kiểm tra playlist công khai trong database"""
from flask import Flask
from src.models.music import Playlist
from src.extensions import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Lấy tất cả playlists
    all_playlists = Playlist.query.all()
    print(f"📊 Tổng số playlists: {len(all_playlists)}")
    
    # Kiểm tra cột is_public có tồn tại không
    print("\n🔍 Kiểm tra cột is_public...")
    if all_playlists:
        sample = all_playlists[0]
        if hasattr(sample, 'is_public'):
            print("✅ Cột is_public đã tồn tại")
            
            # Đếm playlist công khai
            public_count = Playlist.query.filter_by(is_public=True).count()
            print(f"\n🌐 Số playlist công khai: {public_count}")
            
            # Hiển thị chi tiết
            print("\n📋 Chi tiết tất cả playlists:")
            for p in all_playlists:
                status = "🌐 Công khai" if p.is_public else "🔒 Riêng tư"
                print(f"  - ID {p.id}: {p.name} ({status}) - User ID: {p.user_id}")
        else:
            print("❌ Cột is_public CHƯA tồn tại trong database!")
            print("   Cần chạy migration để thêm cột này")
    else:
        print("⚠️ Không có playlist nào trong database")
