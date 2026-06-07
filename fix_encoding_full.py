# -*- coding: utf-8 -*-
import os
import glob

# Ánh xạ đầy đủ các ký tự bị lỗi encoding
encoding_map = {
    'á»§a': 'ủa',
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
    'bÃ i': 'bài',
    'hÃ¡t': 'hát',
    'ChÆ°a': 'Chưa',
    'cÃ³': 'có',
    'nÃ o': 'nào',
    'tiÃªn': 'tiên',
    'báº¯t': 'bắt',
    'TÃªn': 'Tên',
    'MÃ´': 'Mô',
    'táº£': 'tả',
    'tÃ¹y': 'tùy',
    'chá»n': 'chọn',
    'Há»§y': 'Hủy',
    'Sá»­a': 'Sửa',
    'XÃ³a': 'Xóa',
    'khÃ´ng': 'không',
    'trong': 'trống',
    'táº¡o': 'tạo',
    'thÃ nh': 'thành',
    'cÃ´ng': 'công',
    'PhiÃªn': 'Phiên',
    'nháº­p': 'nhập',
    'háº¿t': 'hết',
    'háº¡n': 'hạn',
    'lÃ²ng': 'lòng',
    'láº¡i': 'lại',
    'Lá»—i': 'Lỗi',
    'xÃ¡c': 'xác',
    'ThÃªm': 'Thêm',
    'Nghá»‡': 'Nghệ',
    'SĐ©': 'Sĩ',
    'sĐ©': 'sĩ',
    'áº¢nh': 'Ảnh',
    'diá»‡n': 'diện',
    'táº£i': 'tải',
    'TiÃªu': 'Tiêu',
    'LÆ°á»£t': 'Lượt',
    'ThÃ­ch': 'Thích',
    'thÃ´ng': 'thông',
    'tÃ¬m': 'tìm',
    'tháº¥y': 'thấy',
    'tá»«': 'từ',
    'Cáº­p': 'Cập',
    'nháº­t': 'nhật',
    'áº£nh': 'ảnh',
    'sÃ¡ch': 'sách',
    'thá»ƒ': 'thể',
    'nháº¡c': 'nhạc',
    'Đ'áº§u': 'đầu',
    'Đ'á»ƒ': 'để',
    'Đ'Æ°á»£c': 'được',
    'Đ'Ã£': 'đã',
    'Đ'Đƒng': 'đăng',
    'Đ'á»‹nh': 'định',
    'Đ'áº¡i': 'đại',
    'Đ'á»': 'đề',
    'Má»›i': 'Mới',
}

# Tìm tất cả file HTML
html_files = glob.glob('c:/Users/HP/web_nghe_nhac/src/templates/*.html')

for file_path in html_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Thay thế các ký tự bị lỗi
        for wrong, correct in encoding_map.items():
            content = content.replace(wrong, correct)
        
        # Chỉ ghi lại nếu có thay đổi
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {os.path.basename(file_path)}')
        else:
            print(f'No change: {os.path.basename(file_path)}')
            
    except Exception as e:
        print(f'Error fixing {file_path}: {e}')

print('\nDone!')
