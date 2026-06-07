# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from datetime import datetime
import codecs

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

# Mapping of history folders to template files based on analysis
file_mapping = {
    '421dcc89': 'playlists.html',  # 32KB
    '-22980fca': 'playlist.html',  # 33KB  
    '-5d46fde9': 'base.html',      # 23KB
    '-1ec318cd': 'user_profile.html', # 7KB
    '-ef27eff': 'profile.html',    # 21KB
}

# Find the most recent file in each history folder
restored = []
for folder_name, template_name in file_mapping.items():
    folder_path = history_path / folder_name
    if folder_path.exists():
        html_files = list(folder_path.glob("*.html"))
        if html_files:
            # Get most recent file
            latest = max(html_files, key=lambda x: x.stat().st_mtime)
            mtime = datetime.fromtimestamp(latest.stat().st_mtime)
            
            # Only restore if from today before noon
            if mtime.date() == datetime(2025, 12, 5).date() and mtime.hour < 12:
                dest = templates_path / template_name
                shutil.copy2(latest, dest)
                restored.append(f"{template_name} <- {latest.name} ({latest.stat().st_size:,} bytes, {mtime})")
                print(f"✓ Restored: {template_name}")

print(f"\nRestored {len(restored)} files:")
for r in restored:
    print(f"  {r}")

# Now let's scan all history and try to identify more files
print("\n" + "="*80)
print("Scanning for more files...")
print("="*80)

all_files = []
for folder in history_path.iterdir():
    if folder.is_dir():
        for html_file in folder.glob("*.html"):
            mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
            if mtime.date() == datetime(2025, 12, 5).date() and mtime.hour < 12:
                all_files.append(html_file)

# Try to identify each file
identified = {}
for file_path in all_files:
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            content = f.read(1000)
            
        # Identify file by content
        name = None
        if '{% extends "base.html" %}' not in content[:300]:
            if 'DOCTYPE' in content and 'music-player' in content:
                name = 'base.html'
        elif 'Playlist của tôi' in content:
            name = 'playlists.html'
        elif 'entity-page playlist-page' in content:
            name = 'playlist.html'
        elif 'profile.html' in str(file_path) or ('avatar' in content and 'inline-new-username' in content):
            name = 'profile.html'
        elif 'user-profile' in str(file_path) or ('profile_user.username' in content and 'Hồ sơ' in content):
            name = 'user_profile.html'
        elif 'Bảng Xếp Hạng' in content or 'bxh' in content.lower():
            name = 'bxh.html'
        elif 'main.html' in str(file_path) or ('Genre Cards Grid' in content or 'genre-grid' in content):
            name = 'main.html'
        elif 'Sửa Thông Tin Bài Hát' in content or 'edit-song' in content:
            name = 'edit_song.html'
        elif 'Bài hát yêu thích' in content and '{% block title %}' in content:
            name = 'liked_songs.html'
        elif 'auth-wrap' in content and 'Đăng nhập' in content:
            name = 'login.html'
        elif 'auth-wrap' in content and 'Đăng ký' in content:
            name = 'register.html'
        elif 'Lịch sử nghe' in content:
            name = 'history.html'
        elif 'artist-detail-page' in content or 'artist-header' in content:
            name = 'artist_detail.html'
        elif 'album-detail-page' in content or 'album-header' in content:
            name = 'album_detail.html'
        elif 'Nghệ Sĩ Đã follow' in content and 'artist-card' in content:
            name = 'artists.html'
        elif 'following-page' in content or 'Đang theo dõi' in content:
            name = 'following.html'
        elif 'followers-page' in content or 'Người theo dõi' in content:
            name = 'followers.html'
        elif 'song-detail-page' in content:
            name = 'song_detail.html'
        elif 'genre-detail-page' in content:
            name = 'genre_detail.html'
        elif 'manage-music-data' in content or 'Quản lý Dữ liệu Âm nhạc' in content:
            name = 'manage_music_data.html'
        elif 'manage-song-data' in content or 'Quản lý bài hát' in content:
            name = 'manage_song_data.html'
        elif 'manage-users' in content or 'Quản Lý Người Dùng' in content:
            name = 'manage_users.html'
        elif 'manage-music' in content and 'Quản Lý Nhạc' in content:
            name = 'manage_music.html'
        elif 'add-artist-form' in content or 'Thêm Nghệ Sĩ Mới' in content:
            name = 'add_artist.html'
        elif 'add-song-form' in content or 'Thêm Bài Hát Mới' in content:
            name = 'add_song.html'
        elif 'add-genre-form' in content or 'Thêm Thể Loại' in content:
            name = 'add_genre.html'
        elif 'admin-playlist-dashboard' in content:
            name = 'admin_playlist_dashboard.html'
        
        if name and name not in identified:
            identified[name] = file_path
            
    except:
        pass

# Restore identified files
print(f"\nFound {len(identified)} more files to restore:")
for name, path in identified.items():
    dest = templates_path / name
    if not dest.exists() or dest.stat().st_size == 0:
        shutil.copy2(path, dest)
        print(f"✓ Restored: {name} ({path.stat().st_size:,} bytes)")
    else:
        print(f"  Skipped: {name} (already exists)")

print("\n" + "="*80)
print("RESTORATION COMPLETE!")
print("="*80)
