# -*- coding: utf-8 -*-
import codecs
from pathlib import Path
import shutil

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

# Folders to check (from the list that have sizeable files)
folders_to_check = [
    '-22980fca', '421dcc89', '-2b1e4951', '23f3afc7', '1b981df8',
    '-10bb78a3', 'b151dce', '-1fdf0b20', '-569bc2e2', '-603389cb',
    '186cae0a', '29df0b7f', '-1386cdbf', '-59b63481', '5bdfafaf',
    '-62488a39', '7ce075d4', '-5d14e8de', '-3b3d1746', '1c1f069c'
]

mapping = {}

for folder_name in folders_to_check:
    folder = history_path / folder_name
    if not folder.exists():
        continue
    
    for html_file in folder.glob("*.html"):
        try:
            size = html_file.stat().st_size
            if size < 500:  # Skip very small files
                continue
                
            with codecs.open(html_file, 'r', 'utf-8', errors='ignore') as f:
                content = f.read(5000)
            
            name = None
            
            # Specific identification for missing files
            if 'Đăng nhập' in content[:1000] and 'auth-form' in content and 'email' in content.lower():
                if 'Quên mật khẩu' in content or 'Đăng ký' in content:
                    name = 'login.html'
            elif 'Đăng ký' in content[:1000] and 'auth-form' in content and 'password' in content.lower():
                if 'Đã có tài khoản' in content or 'Nhập lại mật khẩu' in content:
                    name = 'register.html'
            elif 'Bảng Xếp Hạng' in content[:1500] or 'Top 100' in content[:1500]:
                if 'rank-table' in content or 'bxh-table' in content:
                    name = 'bxh.html'
            elif 'Bài hát yêu thích' in content[:1000] or 'Liked Songs' in content[:1000]:
                if 'liked-songs' in content:
                    name = 'liked_songs.html'
            elif 'Lịch sử nghe' in content[:1000] or 'History' in content[:1000]:
                if 'history-container' in content or 'listen-history' in content:
                    name = 'history.html'
            elif 'album-detail' in content or 'album-page' in content:
                if 'album-header' in content or 'album-info' in content:
                    name = 'album_detail.html'
            elif 'song-detail' in content or 'song-page' in content:
                if 'song-header' in content or 'song-info' in content:
                    name = 'song_detail.html'
            elif 'genre-detail' in content or 'genre-page' in content:
                if 'genre-header' in content or 'genre-songs' in content:
                    name = 'genre_detail.html'
            elif 'Sửa Bài Hát' in content or 'Edit Song' in content:
                if 'edit-song-form' in content or 'song-edit' in content:
                    name = 'edit_song.html'
            elif 'Quản Lý Bài Hát' in content or 'manage-song' in content:
                if 'Modal Thêm/Sửa Bài hát' in content or 'song-modal' in content:
                    name = 'manage_song_data.html'
            elif 'Quản Lý Người Dùng' in content:
                if 'user-table' in content or 'manage-users' in content:
                    name = 'manage_users.html'
            elif 'Quản Lý Nhạc' in content[:2000]:
                if 'manage-music-page' in content or 'music-tabs' in content:
                    name = 'manage_music.html'
            elif 'Thêm Nghệ Sĩ' in content[:1000]:
                if 'artist-form' in content or 'add-artist' in content:
                    name = 'add_artist.html'
            elif 'Thêm Bài Hát' in content[:1000]:
                if 'song-form' in content or 'add-song' in content:
                    name = 'add_song.html'
            elif 'Thêm Thể Loại' in content[:1000]:
                if 'genre-form' in content or 'add-genre' in content:
                    name = 'add_genre.html'
            elif 'Nghệ Sĩ' in content[:500] and 'artist-grid' in content:
                if 'filter-btn' in content or 'sort-dropdown' in content:
                    name = 'artists.html'
            elif 'admin-playlist' in content:
                name = 'admin_playlist_dashboard.html'
            
            if name:
                if name not in mapping:
                    mapping[name] = (html_file, size)
                elif size > mapping[name][1]:  # Keep the larger file
                    mapping[name] = (html_file, size)
                    
        except Exception as e:
            pass

print(f"Found {len(mapping)} template files to restore:\n")
for name, (path, size) in sorted(mapping.items()):
    print(f"  {name:30} - {size:7,} bytes - {path.parent.name}/{path.name}")

# Restore files
restored = []
for name, (path, size) in mapping.items():
    dest = templates_path / name
    if not dest.exists() or dest.stat().st_size == 0:
        shutil.copy2(path, dest)
        restored.append(name)
        print(f"\n✓ Restored: {name}")

if restored:
    print(f"\n{'='*80}")
    print(f"Successfully restored {len(restored)} files!")
else:
    print("\nNo files needed restoration.")

# Check what's still missing
still_missing = []
for f in ['login.html', 'register.html', 'bxh.html', 'liked_songs.html', 
          'history.html', 'album_detail.html', 'song_detail.html', 
          'genre_detail.html', 'edit_song.html', 'manage_song_data.html',
          'manage_users.html', 'manage_music.html', 'add_artist.html',
          'add_song.html', 'add_genre.html', 'artists.html',
          'admin_playlist_dashboard.html', 'history_old_backup.html']:
    dest = templates_path / f
    if not dest.exists() or dest.stat().st_size == 0:
        still_missing.append(f)

if still_missing:
    print(f"\n{'='*80}")
    print(f"Still missing {len(still_missing)} files:")
    for f in still_missing:
        print(f"  - {f}")
