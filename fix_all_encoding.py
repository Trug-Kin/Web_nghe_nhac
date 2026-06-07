# -*- coding: utf-8 -*-
import glob
import os

# Tìm tất cả file HTML
html_files = glob.glob('c:/Users/HP/web_nghe_nhac/src/templates/*.html')

# Danh sách replacement siêu đầy đủ
replacements = [
    # Title và header
    ('Quản lý Dữ liệu Ã\x82m nhạc', 'Quản lý Dữ liệu Âm nhạc'),
    ('Quản lý Dá»¯ liá»‡u Ã\x82m nhạc', 'Quản lý Dữ liệu Âm nhạc'),
    ('Quản LÃ½ Ngá»±i DÃ¹ng', 'Quản Lý Người Dùng'),
    ('đŸ"º Bảng Xếp Hạng Lượt Nghe', 'Bảng Xếp Hạng Lượt Nghe'),
    ('đŸ"ºÂ Bảng Xếp Hạng', 'Bảng Xếp Hạng'),
    ('Báº£ng Xáº¿p Hạng', 'Bảng Xếp Hạng'),
    
    # Common phrases
    ('Dá»¯ liá»‡u', 'Dữ liệu'),
    ('dá»¯ liá»‡u', 'dữ liệu'),
    ('Quản lÃ½', 'Quản lý'),
    ('quản lÃ½', 'quản lý'),
    ('Ngá»±i dÃ¹ng', 'Người dùng'),
    ('ngá»±i dÃ¹ng', 'người dùng'),
    ('Ã\x82m nhạc', 'Âm nhạc'),
    ('Ã¢m nhạc', 'âm nhạc'),
    ('liá»‡u', 'liệu'),
    ('Thá»ƒ loáº¡i', 'Thể loại'),
    ('thá»ƒ loáº¡i', 'thể loại'),
    ('BÃ i hÃ¡t', 'Bài hát'),
    ('bÃ i hÃ¡t', 'bài hát'),
    ('BÃ¡i hÃ¡t', 'Bài hát'),
    ('Nghá»‡ SÄ©', 'Nghệ Sĩ'),
    ('nghá»‡ sÄ©', 'nghệ sĩ'),
    ('Nghá»‡ sÄ©', 'Nghệ sĩ'),
    ('Há»" sÆ¡', 'Hồ sơ'),
    ('háº¡t', 'hát'),
    ('hÃ¡t', 'hát'),
    
    # Menu items
    ('Trang chá»§', 'Trang chủ'),
    ('Báº£ng xáº¿p hạng', 'Bảng xếp hạng'),
    ('yÃªu thÃ­ch', 'yêu thích'),
    ('Lá»‹ch sá»­', 'Lịch sử'),
    ('Lịch sá»­', 'Lịch sử'),
    
    # Buttons and actions
    ('Äá»•i tÃªn', 'Đổi tên'),
    ('Quản lý ngÆ°á»i dÃ¹ng', 'Quản lý người dùng'),
    ('Quản lý nhá»±c', 'Quản lý nhạc'),
    ('Äăng xuáº¥t', 'Đăng xuất'),
    ('Äăng nháº­p', 'Đăng nhập'),
    ('Táº¡o má»›i', 'Tạo mới'),
    ('LÃ m má»›i', 'Làm mới'),
    
    # Profile page
    ('Quản trá»‹ viÃªn', 'Quản trị viên'),
    ('Quản lý ngÆ°á»i Äá»ng', 'Quản lý người dùng'),
    ('Äang theo dá»•i', 'Đang theo dõi'),
    ('NgÆ°á»i theo dá»•i', 'Người theo dõi'),
    ('theo dá»•i', 'theo dõi'),
    
    # Admin pages
    ('TÃªn bÃ i hÃ¡t', 'Tên bài hát'),
    ('TiÃªu Äá»', 'Tiêu đề'),
    ('ThÃªm', 'Thêm'),
    ('Sá»­a', 'Sửa'),
    ('XÃ³a', 'Xóa'),
    ('Set Role', 'Set Role'),
    
    # BXH page
    ('Tuáº§n nÃ y', 'Tuần này'),
    ('ThÃ¡ng nÃ y', 'Tháng này'),
    ('Táº¥t cáº£', 'Tất cả'),
    ('Top BÃ i HÃ¡t', 'Top Bài Hát'),
    ('Lượt nghe', 'Lượt nghe'),
    
    # Playlist page
    ('Táº¡o playlist má»›i', 'Tạo playlist mới'),
    ('Tìm tháº¥y', 'Tìm thấy'),
    ('Hiá»ƒn thá»‹', 'Hiển thị'),
    
    # Single character fixes
    ('Ä', 'Đ'),
    ('Ã¡', 'á'),
    ('Ã ', 'à'),
    ('áº£', 'ả'),
    ('áº¡', 'ạ'),
    ('Ã¢', 'â'),
    ('Ã©', 'é'),
    ('Ã¨', 'è'),
    ('áº½', 'ẽ'),
    ('áº¹', 'ẹ'),
    ('Ã­', 'í'),
    ('Ã¬', 'ì'),
    ('Ã³', 'ó'),
    ('Ã²', 'ò'),
    ('á»', 'ỏ'),
    ('Ãµ', 'õ'),
    ('á»', 'ọ'),
    ('Ã´', 'ô'),
    ('Ãº', 'ú'),
    ('Ã¹', 'ù'),
    ('á»§', 'ủ'),
    ('Å©', 'ũ'),
    ('á»¥', 'ụ'),
    ('Æ°', 'ư'),
    ('á»±', 'ự'),
    ('á»­', 'ử'),
    ('á»«', 'ừ'),
    ('á»©', 'ứ'),
    ('á»¯', 'ữ'),
]

fixed_count = 0
for file_path in html_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        for wrong, correct in replacements:
            content = content.replace(wrong, correct)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print(f'✓ Fixed: {os.path.basename(file_path)}')
            fixed_count += 1
        else:
            print(f'  OK: {os.path.basename(file_path)}')
            
    except Exception as e:
        print(f'✗ Error: {file_path} - {e}')

print(f'\n=== Done! Fixed {fixed_count} files ===')
