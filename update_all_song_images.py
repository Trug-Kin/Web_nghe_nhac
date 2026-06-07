"""
Script để cập nhật ảnh cho tất cả bài hát dựa vào tên file có sẵn
"""
from app import create_app
from src.models.music import Song
from src.models import db
import os

app = create_app()
ctx = app.app_context()
ctx.push()

# Thư mục chứa ảnh
image_dir = "DoAnCoSo/images/songs"

# Danh sách file ảnh có sẵn
image_files = os.listdir(image_dir) if os.path.exists(image_dir) else []

print(f"Found {len(image_files)} images in {image_dir}")

# Mapping thủ công (vì tên file không giống tên bài hát)
manual_mapping = {
    1: "noi_nay_co_anh.jpg",
    2: "lac_troi.jpg", 
    3: "chung_ta_khong_thuoc_ve_nhau.jpg",
    4: "chac_ai_do_se_ve.jpg",
    6: "hay_trao_cho_anh.jpg",
    7: "chay_ngay_di.jpg",
    8: "vung_an_toan.jpg",
    9: "the_one.jpg",
    10: "viet_em_ban_tinh_ca.jpg",
}

updated_count = 0

for song_id, filename in manual_mapping.items():
    if filename in image_files:
        song = Song.query.get(song_id)
        if song:
            old_path = song.image_path
            song.image_path = f"images/songs/{filename}"
            print(f"✅ ID {song_id}: {song.title[:40]:40} | {old_path} -> {song.image_path}")
            updated_count += 1
        else:
            print(f"❌ Song ID {song_id} not found")
    else:
        print(f"⚠️ File {filename} không tồn tại")

# COMMIT vào database
db.session.commit()
print(f"\n🎉 Đã cập nhật {updated_count} bài hát!")

# Verify
print("\n=== Verify ===")
songs = Song.query.filter(Song.id.in_(list(manual_mapping.keys()))).all()
for s in songs:
    print(f"ID {s.id}: {s.title[:40]:40} | {s.image_path}")
