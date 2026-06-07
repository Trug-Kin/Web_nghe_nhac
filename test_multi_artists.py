"""
Test script: Kiểm tra xem bài hát có xuất hiện ở trang của tất cả nghệ sĩ không
"""
from app import create_app
from src.models.music import Song, Artist
from src.models import db

app = create_app()
ctx = app.app_context()
ctx.push()

# Tìm một bài hát có nhiều nghệ sĩ
songs_with_multi_artists = Song.query.all()

print("="*70)
print("KIỂM TRA BÀI HÁT VÀ NGHỆ SĨ")
print("="*70)

for song in songs_with_multi_artists[:10]:
    artists = list(song.artists.all())
    if len(artists) > 0:
        print(f"\n🎵 Bài hát: {song.title}")
        print(f"   ID: {song.id}")
        print(f"   Nghệ sĩ ({len(artists)}): {', '.join([a.name for a in artists])}")
        
        # Kiểm tra ngược lại: bài hát này có trong danh sách của mỗi nghệ sĩ không?
        for artist in artists:
            artist_songs = list(artist.songs.all())
            song_ids = [s.id for s in artist_songs]
            if song.id in song_ids:
                print(f"   ✅ Bài hát xuất hiện trong danh sách của {artist.name}")
            else:
                print(f"   ❌ CHƯA xuất hiện trong danh sách của {artist.name}")

print("\n" + "="*70)
print("THỐNG KÊ")
print("="*70)

all_songs = Song.query.all()
multi_artist_songs = [s for s in all_songs if len(list(s.artists.all())) > 1]
single_artist_songs = [s for s in all_songs if len(list(s.artists.all())) == 1]
no_artist_songs = [s for s in all_songs if len(list(s.artists.all())) == 0]

print(f"Tổng số bài hát: {len(all_songs)}")
print(f"Bài hát có NHIỀU nghệ sĩ: {len(multi_artist_songs)}")
print(f"Bài hát có 1 nghệ sĩ: {len(single_artist_songs)}")
print(f"Bài hát KHÔNG có nghệ sĩ: {len(no_artist_songs)}")

if multi_artist_songs:
    print("\n📋 Danh sách bài hát có nhiều nghệ sĩ:")
    for s in multi_artist_songs:
        artists = list(s.artists.all())
        print(f"  - {s.title}: {', '.join([a.name for a in artists])}")
