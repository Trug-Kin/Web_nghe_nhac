# -*- coding: utf-8 -*-
import codecs
from pathlib import Path

history_folders = {
    '59e29e05': [],
    '-45f1f47f': [],
    '3eabbda1': [],
    '7142f': [],
    '15b0b1ec': [],
    '-323d3982': [],
    '-1f807e2b': [],
    '-680edf27': []
}

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")

for folder_name in history_folders.keys():
    folder = history_path / folder_name
    if folder.exists():
        for html_file in folder.glob("*.html"):
            try:
                with codecs.open(html_file, 'r', 'utf-8', errors='ignore') as f:
                    content = f.read(3000)
                
                # Identify file
                name = "unknown"
                
                # Check patterns
                if 'Genre Cards' in content or ('genre-grid' in content and 'artist-tab' in content):
                    name = 'main.html'
                elif 'Login' in content[:500] and 'glassmorphism' in content and 'auth-wrap' in content:
                    name = 'login.html'
                elif 'Register' in content[:500] and 'Đăng ký' in content and 'auth-wrap' in content:
                    name = 'register.html'
                elif 'Bảng Xếp Hạng' in content and 'Lượt Nghe' in content:
                    name = 'bxh.html'
                elif 'Bài hát yêu thích' in content[:800] and 'liked-songs' in content:
                    name = 'liked_songs.html'
                elif 'Lịch sử nghe' in content[:800] and 'history-table' in content:
                    name = 'history.html'
                elif 'artist-detail-page' in content:
                    name = 'artist_detail.html'
                elif 'album-detail-page' in content:
                    name = 'album_detail.html'
                elif 'song-detail-page' in content:
                    name = 'song_detail.html'
                elif 'genre-detail-page' in content:
                    name = 'genre_detail.html'
                elif 'Nghệ Sĩ Đã follow' in content:
                    name = 'artists.html'
                elif 'following-list' in content or 'Đang theo dõi' in content[:800]:
                    name = 'following.html'
                elif 'followers-list' in content or 'Người theo dõi' in content[:800]:
                    name = 'followers.html'
                elif 'Quản lý Dữ liệu Âm nhạc' in content:
                    name = 'manage_music_data.html'
                elif 'Modal Thêm/Sửa Bài hát' in content:
                    name = 'manage_song_data.html'
                elif 'Quản Lý Người Dùng' in content:
                    name = 'manage_users.html'
                elif 'Quản Lý Nhạc' in content[:1500] and 'manage-music-page' in content:
                    name = 'manage_music.html'
                elif 'Thêm Nghệ Sĩ Mới' in content[:800]:
                    name = 'add_artist.html'
                elif 'Thêm Bài Hát' in content[:800] and 'add-song-form' in content:
                    name = 'add_song.html'
                elif 'Thêm Thể Loại' in content[:800]:
                    name = 'add_genre.html'
                elif 'admin-playlist-dashboard' in content:
                    name = 'admin_playlist_dashboard.html'
                elif 'Sửa Thông Tin Bài Hát' in content or ('Sửa Bài Hát' in content[:800] and 'edit-song' in content):
                    name = 'edit_song.html'
                elif 'test_button' in str(html_file) or 'test_upload' in str(html_file):
                    name = 'test_file'
                
                history_folders[folder_name].append((html_file.name, name, html_file.stat().st_size, content[:200]))
                
            except Exception as e:
                print(f"Error reading {html_file}: {e}")

# Print results
for folder, files in history_folders.items():
    if files:
        print(f"\n{'='*80}")
        print(f"Folder: {folder}")
        print('='*80)
        for fname, identified, size, preview in files:
            print(f"\n{fname} -> {identified} ({size:,} bytes)")
            print(f"Preview: {preview[:150]}...")
