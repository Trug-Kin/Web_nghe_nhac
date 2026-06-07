# -*- coding: utf-8 -*-
from pathlib import Path
import codecs
from datetime import datetime
import shutil

history_path = Path(r'C:\Users\HP\AppData\Roaming\Code\User\History')
templates_path = Path(r'c:\Users\HP\web_nghe_nhac\src\templates')

print("Tìm file login.html từ hôm nay (5/12/2025)...")

today = datetime.now().replace(hour=0, minute=0, second=0)
login_files = []

for folder in history_path.iterdir():
    if not folder.is_dir():
        continue
    
    for f in folder.glob('*.html'):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            
            # Only files from today
            if mtime < today:
                continue
            
            size = f.stat().st_size
            if size < 1000 or size > 15000:
                continue
            
            content = codecs.open(f, 'r', 'utf-8', errors='ignore').read(2500)
            
            # Check if it's login page
            if 'Đăng nhập' in content and 'login' in content.lower()[:1000]:
                if 'password' in content.lower() and 'username' in content.lower():
                    login_files.append({
                        'path': f,
                        'size': size,
                        'mtime': mtime,
                        'preview': content[:300]
                    })
        except:
            pass

login_files.sort(key=lambda x: x['mtime'], reverse=True)

print(f"\nTìm thấy {len(login_files)} file login từ hôm nay:\n")
for i, info in enumerate(login_files[:10], 1):
    print(f"{i}. {info['mtime']:%H:%M:%S} - {info['size']:>6,} bytes - {info['path'].parent.name}/{info['path'].name}")
    print(f"   {info['preview'][:100]}...")
    print()

if login_files:
    best = login_files[0]
    print(f"\n{'='*80}")
    print(f"Khôi phục file mới nhất: {best['path'].parent.name}/{best['path'].name}")
    print(f"Thời gian: {best['mtime']:%H:%M:%S}")
    print(f"Kích thước: {best['size']:,} bytes")
    print('='*80)
    
    dest = templates_path / 'login.html'
    shutil.copy2(best['path'], dest)
    print(f"\n✓ Đã khôi phục login.html")
else:
    print("\n⚠ Không tìm thấy file login.html từ hôm nay")
