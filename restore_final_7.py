# -*- coding: utf-8 -*-
import codecs
from pathlib import Path
import shutil

history_path = Path(r"C:\Users\HP\AppData\Roaming\Code\User\History")
templates_path = Path(r"c:\Users\HP\web_nghe_nhac\src\templates")

print("Deep scanning for remaining 7 files...")

remaining = {}

for folder in history_path.iterdir():
    if not folder.is_dir():
        continue
    
    for html_file in folder.glob("*.html"):
        try:
            size = html_file.stat().st_size
            if size < 400:
                continue
            
            with codecs.open(html_file, 'r', 'utf-8', errors='ignore') as f:
                content = f.read(8000)
            
            name = None
            
            # Album detail - more patterns
            if 'album' in content[:1000].lower():
                if any(x in content for x in ['album-detail', 'album_detail', 'album-page', 'album-info', 'album-header']):
                    name = 'album_detail.html'
                elif '{% block title %}' in content and 'album' in content[:500].lower():
                    if 'song' in content and ('track' in content or 'bài hát' in content.lower()):
                        name = 'album_detail.html'
            
            # Genre detail
            if not name and 'genre' in content[:800].lower():
                if any(x in content for x in ['genre-detail', 'genre_detail', 'genre-page', 'genre-songs']):
                    name = 'genre_detail.html'
                elif 'Thể loại' in content[:1000] and 'songs' in content:
                    name = 'genre_detail.html'
            
            # Manage music
            if not name and 'quản' in content.lower() and 'nhạc' in content.lower():
                if 'manage' in content.lower() and ('music' in content.lower() or 'song' in content.lower()):
                    if size > 5000:  # Should be a complex page
                        name = 'manage_music.html'
            
            # Add song
            if not name and 'thêm' in content[:1500].lower() and 'bài' in content[:1500].lower():
                if 'song' in content.lower() or 'hát' in content.lower():
                    if 'form' in content.lower() or 'input' in content.lower():
                        name = 'add_song.html'
            
            # Artists (all artists list)
            if not name and 'artist' in content.lower():
                if 'grid' in content and ('all' in content[:1000].lower() or 'tất cả' in content.lower()):
                    if size > 1000 and size < 5000:
                        name = 'artists.html'
            
            # Admin playlist dashboard
            if not name and 'playlist' in content.lower():
                if 'admin' in content.lower() and 'dashboard' in content.lower():
                    name = 'admin_playlist_dashboard.html'
            
            # History old backup
            if not name and 'history' in content.lower():
                if 'backup' in str(html_file).lower() or 'old' in content[:1000].lower():
                    name = 'history_old_backup.html'
            
            if name:
                if name not in remaining:
                    remaining[name] = []
                remaining[name].append({
                    'path': html_file,
                    'size': size,
                    'preview': content[:300]
                })
        except:
            pass

print(f"\nFound candidates:")
for name, candidates in remaining.items():
    candidates.sort(key=lambda x: x['size'], reverse=True)
    best = candidates[0]
    print(f"\n{name} - {len(candidates)} candidates")
    print(f"  Best: {best['size']:,} bytes - {best['path'].parent.name}/{best['path'].name}")
    print(f"  Preview: {best['preview'][:150]}...")
    
    # Restore
    dest = templates_path / name
    if not dest.exists() or dest.stat().st_size == 0:
        shutil.copy2(best['path'], dest)
        print(f"  ✓ RESTORED")

# Check again
print(f"\n{'='*80}")
missing = []
for f in ['album_detail.html', 'genre_detail.html', 'manage_music.html', 
          'add_song.html', 'artists.html', 'admin_playlist_dashboard.html', 
          'history_old_backup.html']:
    dest = templates_path / f
    if not dest.exists() or dest.stat().st_size == 0:
        missing.append(f)

if missing:
    print(f"Still missing {len(missing)} files: {', '.join(missing)}")
else:
    print("✓✓✓ ALL FILES RESTORED! ✓✓✓")
