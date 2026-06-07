# -*- coding: utf-8 -*-
from pathlib import Path
import codecs
import shutil
from datetime import datetime

history = Path(r'C:\Users\HP\AppData\Roaming\Code\User\History')
templates_path = Path(r'c:\Users\HP\web_nghe_nhac\src\templates')

print("Tìm file genre_detail.html đúng...")

genre_files = []
for folder in history.iterdir():
    if not folder.is_dir():
        continue
    
    for f in folder.glob('*.html'):
        try:
            size = f.stat().st_size
            if size < 1000 or size > 20000:
                continue
            
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            content = codecs.open(f, 'r', 'utf-8', errors='ignore').read(3000)
            
            # Check if it's genre detail page (not modal)
            if 'extends' in content[:500] and 'block title' in content[:800]:
                if 'genre' in content.lower() and 'Thể loại' in content:
                    if 'genre-detail' in content or 'genre-page' in content or 'genre_detail' in content:
                        genre_files.append({
                            'path': f,
                            'size': size,
                            'mtime': mtime,
                            'preview': content[:500]
                        })
        except:
            pass

genre_files.sort(key=lambda x: x['mtime'], reverse=True)

print(f"\nTìm thấy {len(genre_files)} file genre_detail:\n")
for i, info in enumerate(genre_files[:10], 1):
    print(f"{i}. {info['mtime']:%Y-%m-%d %H:%M} - {info['size']:>6,} bytes - {info['path'].parent.name}/{info['path'].name}")
    print(f"   {info['preview'][:120]}...")
    print()

if genre_files:
    best = genre_files[0]
    print(f"\n{'='*80}")
    print(f"Khôi phục file: {best['path'].parent.name}/{best['path'].name}")
    print(f"Kích thước: {best['size']:,} bytes")
    print('='*80)
    
    dest = templates_path / 'genre_detail.html'
    shutil.copy2(best['path'], dest)
    print(f"\n✓ Đã khôi phục genre_detail.html")
