# -*- coding: utf-8 -*-
import codecs
from pathlib import Path
import shutil
from datetime import datetime

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

# Get ALL HTML files from history
all_candidates = {}

print("Scanning all history folders...")
for folder in history_path.iterdir():
    if not folder.is_dir():
        continue
    
    for html_file in folder.glob("*.html"):
        try:
            size = html_file.stat().st_size
            if size < 300:  # Skip very small files
                continue
            
            mtime = datetime.fromtimestamp(html_file.stat().st_mtime)
            
            with codecs.open(html_file, 'r', 'utf-8', errors='ignore') as f:
                content = f.read(6000)
            
            name = None
            confidence = 0
            
            # Login page
            if 'login' in content[:500].lower() and 'password' in content.lower():
                if 'Đăng nhập' in content or 'Login' in content[:800]:
                    if 'auth' in content or 'signin' in content.lower():
                        name = 'login.html'
                        confidence = 3
            
            # Register page  
            if not name and 'register' in content[:500].lower():
                if 'Đăng ký' in content or 'Register' in content[:800]:
                    if 'password' in content.lower() and 'email' in content.lower():
                        name = 'register.html'
                        confidence = 3
            
            # BXH page
            if not name and ('Bảng Xếp Hạng' in content or 'BXH' in content[:1000]):
                if 'rank' in content.lower() or 'top' in content[:1500]:
                    name = 'bxh.html'
                    confidence = 3
            
            # Liked songs
            if not name and 'liked-songs' in content:
                name = 'liked_songs.html'
                confidence = 3
            elif not name and 'Bài hát yêu thích' in content[:1000]:
                name = 'liked_songs.html'
                confidence = 2
            
            # History
            if not name and 'history' in content[:800].lower():
                if 'Lịch sử' in content[:1000] or 'History' in content[:1000]:
                    if 'song' in content.lower() or 'listen' in content.lower():
                        name = 'history.html'
                        confidence = 2
            
            # Album detail
            if not name and 'album-detail' in content:
                name = 'album_detail.html'
                confidence = 3
            elif not name and ('album-page' in content or 'album_page' in content):
                if 'album-info' in content or 'album-header' in content:
                    name = 'album_detail.html'
                    confidence = 2
            
            # Genre detail
            if not name and 'genre-detail' in content:
                name = 'genre_detail.html'
                confidence = 3
            elif not name and ('genre-page' in content or 'genre_page' in content):
                if 'genre' in content and 'songs' in content:
                    name = 'genre_detail.html'
                    confidence = 2
            
            # Edit song
            if not name and 'edit-song' in content:
                name = 'edit_song.html'
                confidence = 3
            elif not name and 'Sửa Bài Hát' in content[:1500]:
                name = 'edit_song.html'
                confidence = 2
            
            # Manage song data (modal)
            if not name and 'Modal Thêm/Sửa Bài hát' in content:
                name = 'manage_song_data.html'
                confidence = 3
            elif not name and 'song-modal' in content:
                if 'edit' in content.lower() and 'song' in content.lower():
                    name = 'manage_song_data.html'
                    confidence = 2
            
            # Manage users
            if not name and 'Quản Lý Người Dùng' in content:
                name = 'manage_users.html'
                confidence = 3
            elif not name and 'manage-users' in content:
                name = 'manage_users.html'
                confidence = 2
            
            # Manage music
            if not name and 'manage-music-page' in content:
                if 'Quản Lý Nhạc' in content[:2000]:
                    name = 'manage_music.html'
                    confidence = 3
            
            # Add artist
            if not name and 'Thêm Nghệ Sĩ' in content[:1000]:
                if 'artist' in content.lower() and 'form' in content.lower():
                    name = 'add_artist.html'
                    confidence = 3
            elif not name and 'add-artist' in content:
                name = 'add_artist.html'
                confidence = 2
            
            # Add song
            if not name and 'Thêm Bài Hát' in content[:1000]:
                if 'song' in content.lower() and 'form' in content.lower():
                    name = 'add_song.html'
                    confidence = 3
            elif not name and 'add-song-form' in content:
                name = 'add_song.html'
                confidence = 2
            
            # Add genre
            if not name and 'Thêm Thể Loại' in content[:1000]:
                name = 'add_genre.html'
                confidence = 3
            elif not name and 'add-genre' in content:
                name = 'add_genre.html'
                confidence = 2
            
            # Artists list
            if not name and 'Nghệ Sĩ' in content[:500]:
                if 'artist-grid' in content or 'artists-grid' in content:
                    if 'filter' in content.lower() or 'all' in content.lower():
                        name = 'artists.html'
                        confidence = 2
            
            # Admin playlist dashboard
            if not name and 'admin-playlist' in content:
                name = 'admin_playlist_dashboard.html'
                confidence = 3
            
            if name:
                key = name
                if key not in all_candidates:
                    all_candidates[key] = []
                all_candidates[key].append({
                    'path': html_file,
                    'size': size,
                    'mtime': mtime,
                    'confidence': confidence
                })
                
        except Exception as e:
            pass

print(f"\nFound candidates for {len(all_candidates)} template types\n")

# Select best candidate for each file
best_matches = {}
for name, candidates in all_candidates.items():
    # Sort by confidence (desc), then size (desc), then mtime (desc)
    candidates.sort(key=lambda x: (x['confidence'], x['size'], x['mtime']), reverse=True)
    best = candidates[0]
    best_matches[name] = best
    print(f"{name:30} - {best['size']:7,} bytes - {best['mtime'].strftime('%Y-%m-%d %H:%M')} - conf:{best['confidence']} - {best['path'].parent.name}/{best['path'].name}")

print(f"\n{'='*80}")
print("Restoring files...")
print('='*80)

restored = []
for name, info in best_matches.items():
    dest = templates_path / name
    if not dest.exists() or dest.stat().st_size == 0:
        shutil.copy2(info['path'], dest)
        print(f"✓ {name:30} ({info['size']:,} bytes)")
        restored.append(name)
    else:
        print(f"⊘ {name:30} (already exists, {dest.stat().st_size:,} bytes)")

print(f"\n{'='*80}")
print(f"Restored {len(restored)} files")
print('='*80)

# Final check
missing = []
all_expected = [
    'login.html', 'register.html', 'bxh.html', 'liked_songs.html', 
    'history.html', 'album_detail.html', 'genre_detail.html', 
    'edit_song.html', 'manage_song_data.html', 'manage_users.html',
    'manage_music.html', 'add_artist.html', 'add_song.html',
    'add_genre.html', 'artists.html', 'admin_playlist_dashboard.html',
    'history_old_backup.html'
]

for f in all_expected:
    dest = templates_path / f
    if not dest.exists() or dest.stat().st_size == 0:
        missing.append(f)

if missing:
    print(f"\n⚠ Still missing {len(missing)} files:")
    for f in missing:
        print(f"  - {f}")
else:
    print("\n✓✓✓ ALL TEMPLATE FILES RESTORED! ✓✓✓")
