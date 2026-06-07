# -*- coding: utf-8 -*-
import os

files_to_fix = [
    'c:/Users/HP/web_nghe_nhac/src/templates/base.html',
    'c:/Users/HP/web_nghe_nhac/src/templates/main.html',
]

# Danh sách replacement đầy đủ
replacements = [
    ('chá»§', 'chủ'),
    ('Báº£ng', 'Bảng'),
    ('xáº¿p', 'xếp'),
    ('yÃªu thÃ­ch', 'yêu thích'),
    ('Lá»‹ch sá»­', 'Lịch sử'),
    ('Đ\'Ã£', 'đã'),
    ('QUáº¢N TRá»Š', 'QUẢN TRỊ'),
    ('ngÆ°á»i dÃ¹ng', 'người dùng'),
    ('Ã¢m', 'âm'),
    ('Nghá»‡ SĐ©', 'Nghệ Sĩ'),
    ('nghá»‡ sĐ©', 'nghệ sĩ'),
    ('Há»"', 'Hồ'),
    ('sÆ¡', 'sơ'),
    ('BÃ i', 'Bài'),
    ('hÃ¡t', 'hát'),
    ('cÃ¡c', 'các'),
    ('báº£ng', 'bảng'),
    ('háº¡ng', 'hạng'),
]

for file_path in files_to_fix:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        for wrong, correct in replacements:
            content = content.replace(wrong, correct)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {os.path.basename(file_path)}')
        else:
            print(f'OK: {os.path.basename(file_path)}')
            
    except Exception as e:
        print(f'Error: {file_path} - {e}')

print('\nDone!')
