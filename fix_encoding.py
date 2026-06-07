# -*- coding: utf-8 -*-
import os
import glob

# Ánh xạ các ký tự bị lỗi encoding
encoding_map = {
    'cá»§a': 'của',
    'tÃ´i': 'tôi',
    'Quáº£n': 'Quản',
    'lÃ½': 'lý',
    'vÃ ': 'và',
    'khÃ¡m': 'khám',
    'phÃ¡': 'phá',
    'cÃ¡c': 'các',
    'báº¡n': 'bạn',
    'TÃ¬m': 'Tìm',
    'Táº¡o': 'Tạo',
    'má»›i': 'mới',
    'LÃ m': 'Làm',
    'CÃ´ng': 'Công',
    'RiÃªng': 'Riêng',
    'tÆ°': 'tư',
    'báº£ng': 'bảng',
    'xáº¿p': 'xếp',
    'háº¡ng': 'hạng',
    'Háº¡ng': 'Hạng',
    'sá': 'sá',
    'tái': 'tái',
    'Ä': 'Đ',
}

# Tìm tất cả file HTML
html_files = glob.glob('c:/Users/HP/web_nghe_nhac/src/templates/*.html')

for file_path in html_files:
    try:
        # Đọc file với encoding UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Thay thế các ký tự bị lỗi
        for wrong, correct in encoding_map.items():
            content = content.replace(wrong, correct)
        
        # Ghi lại file với encoding UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'Fixed: {os.path.basename(file_path)}')
    except Exception as e:
        print(f'Error fixing {file_path}: {e}')

print('\nDone! Fixed encoding for all HTML files.')
