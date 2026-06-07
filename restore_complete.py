# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from datetime import datetime
import codecs

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

# Get all HTML files from history (expand time range)
all_files = []
for folder in history_path.iterdir():
    if folder.is_dir():
        for html_file in folder.glob("*.html"):
            mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
            # Include files from last few days
            if mtime >= datetime(2025, 12, 1):
                all_files.append((html_file, mtime))

all_files.sort(key=lambda x: x[1], reverse=True)

# Try to identify each file
identified = {}
for file_path, mtime in all_files:
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            content = f.read(2000)
        
        name = None
        
        # More specific identification patterns
        if '{% extends "base.html" %}' not in content[:300]:
            if 'DOCTYPE' in content and '<html' in content:
                if 'music-player' in content or 'id="main-sidebar"' in content:
                    name = 'base.html'
        elif 'Login' in content and 'glassmorphism' in content and 'auth-wrap' in content:
            name = 'login.html'
        elif 'Register' in content and 'Đăng ký' in content and 'auth-wrap' in content:
            name = 'register.html'
        elif 'Bảng Xếp Hạng' in content and 'Lượt Nghe' in content:
            name = 'bxh.html'
        elif 'Genre Cards' in content or ('genre-grid' in content and 'artist-tab' in content):
            name = 'main.html'
        elif 'Bài hát yêu thích' in content[:500] and 'liked-songs' in content:
            name = 'liked_songs.html'
        elif 'Lịch sử nghe' in content[:500] and 'history-table' in content:
            name = 'history.html'
        elif 'Lịch sử nghe' in content[:500] and 'history_old_backup' in str(file_path):
            name = 'history_old_backup.html'
        elif 'artist-detail-page' in content:
            name = 'artist_detail.html'
        elif 'album-detail-page' in content:
            name = 'album_detail.html'
        elif 'song-detail-page' in content:
            name = 'song_detail.html'
        elif 'genre-detail-page' in content:
            name = 'genre_detail.html'
        elif 'Nghệ Sĩ Đã follow' in content and 'artists-grid' in content:
            name = 'artists.html'
        elif 'following-list' in content or 'Đang theo dõi' in content[:500]:
            name = 'following.html'
        elif 'followers-list' in content or 'Người theo dõi' in content[:500]:
            name = 'followers.html'
        elif 'Quản lý Dữ liệu Âm nhạc' in content:
            name = 'manage_music_data.html'
        elif 'Modal Thêm/Sửa Bài hát' in content and 'song-modal' in content:
            name = 'manage_song_data.html'
        elif 'Quản Lý Người Dùng' in content and 'manage-users' in content:
            name = 'manage_users.html'
        elif 'Quản Lý Nhạc' in content[:1000] and 'manage-music-page' in content:
            name = 'manage_music.html'
        elif 'Thêm Nghệ Sĩ Mới' in content:
            name = 'add_artist.html'
        elif 'Thêm Bài Hát' in content[:500] and 'add-song-form' in content:
            name = 'add_song.html'
        elif 'Thêm Thể Loại' in content:
            name = 'add_genre.html'
        elif 'admin-playlist-dashboard' in content:
            name = 'admin_playlist_dashboard.html'
        elif 'Sửa Thông Tin Bài Hát' in content or 'Sửa Bài Hát' in content[:500]:
            name = 'edit_song.html'
        
        if name and name not in identified:
            identified[name] = (file_path, mtime)
            
    except Exception as e:
        pass

print(f"Found {len(identified)} template files:")
for name, (path, mtime) in sorted(identified.items()):
    print(f"  {name:30} - {path.stat().st_size:6,} bytes - {mtime}")

# Restore all identified files
restored_count = 0
for name, (path, mtime) in identified.items():
    dest = templates_path / name
    if not dest.exists() or dest.stat().st_size == 0:
        shutil.copy2(path, dest)
        print(f"✓ Restored: {name}")
        restored_count += 1

print(f"\n{'='*80}")
print(f"Restored {restored_count} files successfully!")
print(f"{'='*80}")

# Check what's still missing
all_expected = [
    'base.html', 'main.html', 'login.html', 'register.html',
    'profile.html', 'user_profile.html', 'playlist.html', 'playlists.html',
    'liked_songs.html', 'history.html', 'history_old_backup.html',
    'bxh.html', 'artists.html', 'artist_detail.html', 'album_detail.html',
    'song_detail.html', 'genre_detail.html', 'edit_song.html',
    'following.html', 'followers.html',
    'manage_music_data.html', 'manage_song_data.html', 'manage_users.html', 'manage_music.html',
    'add_artist.html', 'add_song.html', 'add_genre.html', 'admin_playlist_dashboard.html'
]

missing = [f for f in all_expected if not (templates_path / f).exists() or (templates_path / f).stat().st_size == 0]
if missing:
    print(f"\nStill missing {len(missing)} files:")
    for f in missing:
        print(f"  - {f}")
else:
    print("\n✓ All template files have been restored!")
