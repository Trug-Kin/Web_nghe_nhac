# -*- coding: utf-8 -*-
import os
import glob
import codecs

# Đọc và sửa từng file
html_files = glob.glob('c:/Users/HP/web_nghe_nhac/src/templates/*.html')

replacements = [
    # Cụm từ dài
    ('vÃ  khÃ¡m phÃ¡', 'và khám phá'),
    ('bÃ i hÃ¡t', 'bài hát'),
    ('ChÆ°a cÃ³', 'Chưa có'),
    ('playlist nÃ o', 'playlist nào'),
    ('Nghá»‡ sĐ©', 'Nghệ Sĩ'),
    ('nghá»‡ sĐ©', 'nghệ sĩ'),
    ('thành cÃ´ng', 'thành công'),
    ('riÃªng tÆ°', 'riêng tư'),
    ('cÃ´ng khai', 'công khai'),
    ('hết hạn', 'hết hạn'),
    ('ket noi', 'kết nối'),
    ('may chu', 'máy chủ'),
    ('Đ\'áº¿n', 'đến'),
    ('thá»±c hiá»‡n', 'thực hiện'),
    ('thao tÃ¡c', 'thao tác'),
    ('tùy chá»n', 'tùy chọn'),
    ('Há»" sÆ¡', 'Hồ sơ'),
    ('ĐĐƒng xuáº¥t', 'Đăng xuất'),
    ('ĐĐƒng nháº­p', 'Đăng nhập'),
    ('Đ\'Đƒng', 'đăng'),
    ('nháº­p', 'nhập'),
    ('xuáº¥t', 'xuất'),
    ('hiá»‡n', 'hiện'),
    ('thá»‹', 'thị'),
    ('dá»¯ liá»‡u', 'dữ liệu'),
    ('cáº­p nháº­t', 'cập nhật'),
    ('Cáº­p nháº­t', 'Cập nhật'),
    ('Báº¡n chÆ°a', 'Bạn chưa'),
    ('láº¥y', 'lấy'),
    ('ĐÃ£', 'Đã'),
    ('tìm tháº¥y', 'tìm thấy'),
    ('Đáº·t', 'Đặt'),
    ('Thá»ƒ Loáº¡i', 'Thể Loại'),
    ('thể loáº¡i', 'thể loại'),
    ('khi táº¡o', 'khi tạo'),
    ('nÃºt', 'nút'),
    ('trÃªn', 'trên'),
    ('gá»­i', 'gửi'),
    ('lÃªn', 'lên'),
    ('báº¥m', 'bấm'),
    ('chá»‰', 'chỉ'),
    ('vÃ o', 'vào'),
    ('ra ngoÃ i', 'ra ngoài'),
    ('má»™t', 'một'),
    ('LuÃ´n', 'Luôn'),
    ('CÃ³ lá»—i', 'Có lỗi'),
    ('thá»­ lại', 'thử lại'),
    
    # Từ đơn
    ('LÃ m', 'Làm'),
    ('má»›i', 'mới'),
    ('Má»›i', 'Mới'),
    ('nÃ o', 'nào'),
    ('tiÃªn', 'tiên'),
    ('TÃªn', 'Tên'),
    ('tÃªn', 'tên'),
    ('MÃ´', 'Mô'),
    ('táº£', 'tả'),
    ('tÃ¹y', 'tùy'),
    ('chá»n', 'chọn'),
    ('Há»§y', 'Hủy'),
    ('Sá»­a', 'Sửa'),
    ('XÃ³a', 'Xóa'),
    ('khÃ´ng', 'không'),
    ('KhÃ´ng', 'Không'),
    ('táº¡o', 'tạo'),
    ('PhiÃªn', 'Phiên'),
    ('háº¿t', 'hết'),
    ('háº¡n', 'hạn'),
    ('lÃ²ng', 'lòng'),
    ('láº¡i', 'lại'),
    ('Lá»—i', 'Lỗi'),
    ('xÃ¡c', 'xác'),
    ('ThÃªm', 'Thêm'),
    ('áº¢nh', 'Ảnh'),
    ('diá»‡n', 'diện'),
    ('táº£i', 'tải'),
    ('TiÃªu', 'Tiêu'),
    ('LÆ°á»£t', 'Lượt'),
    ('LÆ°u', 'Lưu'),
    ('ThÃ­ch', 'Thích'),
    ('thÃ´ng', 'thông'),
    ('tÃ¬m', 'tìm'),
    ('tháº¥y', 'thấy'),
    ('tá»«', 'từ'),
    ('sÃ¡ch', 'sách'),
    ('thá»ƒ', 'thể'),
    ('nháº¡c', 'nhạc'),
    ('vÃ ', 'và'),
    ('cÃ³', 'có'),
    ('ĐÃ£', 'Đã'),
    ('MÃ u', 'Màu'),
    ('Đang', 'Đang'),
    
    # Ký tự đặc biệt
    ('Đ\'áº§u', 'đầu'),
    ('Đ\'á»ƒ', 'để'),
    ('Đ\'Æ°á»£c', 'được'),
    ('Đ\'Ã£', 'đã'),
    ('Đ\'á»‹nh', 'định'),
    ('Đ\'áº¡i', 'đại'),
    ('Đ\'á»', 'đề'),
    ('Đ\'áº¿n', 'đến'),
]

for file_path in html_files:
    try:
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        for wrong, correct in replacements:
            content = content.replace(wrong, correct)
        
        if content != original:
            with codecs.open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {os.path.basename(file_path)}')
        else:
            print(f'OK: {os.path.basename(file_path)}')
            
    except Exception as e:
        print(f'Error: {file_path} - {e}')

print('\n=== Complete! ===')
