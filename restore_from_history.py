# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path
from datetime import datetime

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

# Find all HTML files in history
html_files = []
for folder in history_path.iterdir():
    if folder.is_dir():
        for file in folder.glob("*.html"):
            html_files.append({
                'path': file,
                'size': file.stat().st_size,
                'mtime': datetime.fromtimestamp(file.stat().st_mtime),
                'name': file.name
            })

# Sort by modification time (newest first)
html_files.sort(key=lambda x: x['mtime'], reverse=True)

# Filter files from today (Dec 5, 2025) before the disaster (around 11:42)
today_files = [f for f in html_files if f['mtime'].date() == datetime(2025, 12, 5).date() and f['mtime'].hour < 12]

print(f"Found {len(today_files)} HTML files from today (before 12:00)")
print("\nMost recent files:")
for i, f in enumerate(today_files[:20]):
    print(f"{i+1}. {f['name']} - {f['size']:,} bytes - {f['mtime']}")
    print(f"   Path: {f['path']}")
    
# Read first few lines of largest files to identify them
print("\n" + "="*80)
print("Identifying files by content:")
print("="*80)

checked = {}
for f in today_files[:20]:
    try:
        with open(f['path'], 'r', encoding='utf-8') as file:
            content = file.read(500)
            # Try to identify the file
            if 'base.html' in str(f['path']) or 'extends "base.html"' not in content[:200]:
                file_type = "base.html (likely)"
            elif 'playlist' in content.lower() and 'của tôi' in content:
                file_type = "playlists.html"
            elif 'playlist' in content.lower() and 'entity-page' in content:
                file_type = "playlist.html"
            elif 'profile' in content.lower() and 'avatar' in content:
                file_type = "profile.html"
            elif 'bxh' in content.lower() or 'bảng xếp hạng' in content.lower():
                file_type = "bxh.html"
            elif 'main' in content.lower() and 'genre' in content.lower():
                file_type = "main.html"
            elif 'edit' in content.lower() and 'song' in content.lower():
                file_type = "edit_song.html"
            elif 'liked' in content.lower() or 'yêu thích' in content.lower():
                file_type = "liked_songs.html"
            elif 'login' in content.lower() and 'glass' in content.lower():
                file_type = "login.html"
            elif 'register' in content.lower() and 'đăng ký' in content.lower():
                file_type = "register.html"
            else:
                file_type = "unknown"
            
            if file_type not in checked:
                checked[file_type] = f
                print(f"\n{file_type}:")
                print(f"  Size: {f['size']:,} bytes")
                print(f"  Time: {f['mtime']}")
                print(f"  Path: {f['path']}")
                print(f"  Preview: {content[:150]}...")
    except Exception as e:
        print(f"Error reading {f['path']}: {e}")

print("\n" + "="*80)
print("Ready to restore? Check the identified files above.")
print("="*80)
