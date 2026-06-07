# -*- coding: utf-8 -*-
from pathlib import Path
import codecs
from datetime import datetime
import shutil

history = Path(r'C:\Users\HP\AppData\Roaming\Code\User\History')
templates_path = Path(r'c:\Users\HP\web_nghe_nhac\src\templates')

print("Tìm tất cả file BXH (kích thước >5KB)...")

bxh_files = []
for folder in history.iterdir():
    if not folder.is_dir():
        continue
    
    for f in folder.glob('*.html'):
        try:
            size = f.stat().st_size
            if size < 5000:
                continue
            
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            content = codecs.open(f, 'r', 'utf-8', errors='ignore').read(3000)
            
            # Check if it's BXH page
            if 'Bảng Xếp Hạng' in content or 'BXH' in content[:1500]:
                if 'rank' in content.lower() or 'top' in content.lower():
                    bxh_files.append({
                        'path': f,
                        'size': size,
                        'mtime': mtime,
                        'preview': content[:400]
                    })
        except:
            pass

bxh_files.sort(key=lambda x: x['mtime'], reverse=True)

print(f"\nTìm thấy {len(bxh_files)} file BXH:\n")
for i, info in enumerate(bxh_files[:10], 1):
    print(f"{i}. {info['mtime']:%Y-%m-%d %H:%M} - {info['size']:>7,} bytes - {info['path'].parent.name}/{info['path'].name}")
    print(f"   Preview: {info['preview'][:150]}...")
    print()

if bxh_files:
    # Show the most recent large BXH file
    best = bxh_files[0]
    print(f"\n{'='*80}")
    print(f"File BXH tốt nhất: {best['path'].parent.name}/{best['path'].name}")
    print(f"Kích thước: {best['size']:,} bytes")
    print(f"Ngày: {best['mtime']:%Y-%m-%d %H:%M}")
    print('='*80)
    
    choice = input("\nKhôi phục file này? (y/n): ").strip().lower()
    if choice == 'y':
        dest = templates_path / 'bxh.html'
        shutil.copy2(best['path'], dest)
        print(f"\n✓ Đã khôi phục bxh.html từ {best['path'].name}")
        print(f"  Kích thước: {best['size']:,} bytes")
