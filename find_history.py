# -*- coding: utf-8 -*-
from pathlib import Path
import codecs
from datetime import datetime
import shutil

history_path = Path(r'C:\Users\HP\AppData\Roaming\Code\User\History')
templates_path = Path(r'c:\Users\HP\web_nghe_nhac\src\templates')

print("Tìm file history.html đúng...")

history_files = []
for folder in history_path.iterdir():
    if not folder.is_dir():
        continue
    
    for f in folder.glob('*.html'):
        try:
            size = f.stat().st_size
            if size < 8000 or size > 20000:
                continue
            
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            content = codecs.open(f, 'r', 'utf-8', errors='ignore').read(3000)
            
            # Check if it's history page (not duplicate)
            if 'Lịch sử nghe' in content and 'extends' in content[:500]:
                # Make sure not duplicate
                if content.count('extends') == 1:
                    history_files.append({
                        'path': f,
                        'size': size,
                        'mtime': mtime,
                        'preview': content[:400]
                    })
        except:
            pass

history_files.sort(key=lambda x: x['mtime'], reverse=True)

print(f"\nTìm thấy {len(history_files)} file history:\n")
for i, info in enumerate(history_files[:10], 1):
    print(f"{i}. {info['mtime']:%Y-%m-%d %H:%M} - {info['size']:>6,} bytes - {info['path'].parent.name}/{info['path'].name}")
    print(f"   {info['preview'][:120]}...")
    print()

if history_files:
    best = history_files[0]
    print(f"\n{'='*80}")
    print(f"Khôi phục file: {best['path'].parent.name}/{best['path'].name}")
    print(f"Kích thước: {best['size']:,} bytes")
    print('='*80)
    
    dest = templates_path / 'history.html'
    shutil.copy2(best['path'], dest)
    print(f"\n✓ Đã khôi phục history.html")
else:
    print("\n⚠ Không tìm thấy file history.html phù hợp trong VS Code history")
