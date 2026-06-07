"""
Script tự động map ảnh cho TẤT CẢ bài hát dựa vào tên file
"""
from app import create_app
from src.models.music import Song
from src.models import db
import os
import unicodedata
import re

app = create_app()
ctx = app.app_context()
ctx.push()

def normalize_text(text):
    """Chuẩn hóa text để so sánh (bỏ dấu, lowercase, bỏ ký tự đặc biệt)"""
    # Bỏ dấu tiếng Việt
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    # Lowercase và bỏ ký tự đặc biệt
    text = re.sub(r'[^a-z0-9]+', '_', text.lower())
    text = text.strip('_')
    return text

# Lấy danh sách file ảnh
image_dir = "DoAnCoSo/images/songs"
image_files = os.listdir(image_dir) if os.path.exists(image_dir) else []

print(f"📁 Found {len(image_files)} images")
print(f"🎵 Checking all songs in database...\n")

# Tạo mapping từ tên file
file_mapping = {}
for filename in image_files:
    name_without_ext = os.path.splitext(filename)[0]
    normalized = normalize_text(name_without_ext)
    file_mapping[normalized] = filename

# Lấy tất cả bài hát
all_songs = Song.query.all()
updated_count = 0
already_has_image = 0
not_found = []

for song in all_songs:
    if song.image_path:
        already_has_image += 1
        continue
    
    # Chuẩn hóa tên bài hát để tìm
    normalized_title = normalize_text(song.title)
    
    # Tìm ảnh matching
    matched_file = None
    
    # 1. Thử tìm exact match
    if normalized_title in file_mapping:
        matched_file = file_mapping[normalized_title]
    else:
        # 2. Thử tìm partial match (tên file chứa tên bài hát hoặc ngược lại)
        for norm_name, filename in file_mapping.items():
            if normalized_title in norm_name or norm_name in normalized_title:
                matched_file = filename
                break
    
    if matched_file:
        song.image_path = f"images/songs/{matched_file}"
        print(f"✅ ID {song.id:2d}: {song.title[:45]:45} -> {matched_file}")
        updated_count += 1
    else:
        not_found.append((song.id, song.title))
        print(f"⚠️  ID {song.id:2d}: {song.title[:45]:45} -> NOT FOUND")

# COMMIT vào database
if updated_count > 0:
    db.session.commit()
    print(f"\n🎉 Đã cập nhật {updated_count} bài hát mới!")
else:
    print(f"\n⚠️  Không có bài hát nào được cập nhật")

print(f"✅ {already_has_image} bài đã có ảnh từ trước")

if not_found:
    print(f"\n❌ {len(not_found)} bài hát không tìm thấy ảnh:")
    for song_id, title in not_found:
        print(f"   ID {song_id}: {title}")
        # Suggest possible files
        norm_title = normalize_text(title)
        suggestions = [f for n, f in file_mapping.items() if any(word in n for word in norm_title.split('_')[:3])]
        if suggestions:
            print(f"      Có thể: {', '.join(suggestions[:3])}")

print("\n" + "="*70)
print("TỔNG KẾT:")
print(f"  - Tổng số bài hát: {len(all_songs)}")
print(f"  - Đã có ảnh trước đó: {already_has_image}")
print(f"  - Vừa cập nhật: {updated_count}")
print(f"  - Không tìm thấy: {len(not_found)}")
print("="*70)
