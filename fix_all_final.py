# -*- coding: utf-8 -*-
import codecs
import glob

files = glob.glob('c:/Users/HP/web_nghe_nhac/src/templates/*.html')

# Dictionary với tất cả các replacement cần thiết
replacements = {
    # Basic characters
    'vÃ ': 'và ',
    'VÃ ': 'Và ',
    'bÃ i': 'bài',
    'BÃ i': 'Bài',
    'thÃªm': 'thêm',
    'nÃ o': 'nào',
    'nÃ y': 'này',
    'ĐÃ£': 'Đã',
    'thÃ nh': 'thành',
    'káº¿t nỏ\'i': 'kết nối',
    'Đ\'áº¿n': 'đến',
    'chỏ§': 'chủ',
    'Đáº·t': 'Đặt',
    'riÃªng tư': 'riêng tư',
    'Đ\'áº§u': 'đầu',
    'Đ\'ỏƒ': 'để',
    'báº¯t': 'bắt',
    'Đ\'ưỏ£c': 'được',
    'Đ\'Ã£': 'đã',
    'chỏn': 'chọn',
    'Chỏn': 'Chọn',
    'Ngưỏi': 'Người',
    'ngưỏi': 'người',
    'HÃ£y': 'Hãy',
    'nhỏ¯ng': 'những',
    'Đ\'ây': 'đây',
    'Nháº­p': 'Nhập',
    'kiáº¿m': 'kiếm',
    'hoáº±c': 'hoặc',
    'Chỏ‰nh': 'Chỉnh',
    'sỏ­a': 'sửa',
    'chi tiáº¿t': 'chi tiết',
    'âœ"': '✓',
    'chuyỏƒn': 'chuyển',
    'náº¿u': 'nếu',
    'muỏ\'n': 'muốn',
    'Đ\'ỏ•i': 'đổi',
    'Giỏ¯': 'Giữ',
    'nhiỏu': 'nhiều',
    'Điỏn': 'Điền',
    'vÃ o': 'vào',
    'sáº»': 'sẻ',
    'mỏi': 'mời',
    'cháº¯c': 'chắc',
    'Đ\'Đƒng': 'đăng',
    'ĐĐƒng': 'Đăng',
    'kÃ½': 'ký',
    'Xanh dưÆ¡ng': 'Xanh dương',
    'VÃ ng': 'Vàng',
    'MÃ u': 'Màu',
    'thuỏ™c': 'thuộc',
    'Tiêu Đ\'ỏ': 'Tiêu đề',
    'Ảnh bÃ i': 'Ảnh bài',
    'Hiỏ‡n': 'Hiển',
    'hiỏƒn thị': 'hiển thị',
    'Nỏ•i Báº­t': 'Nổi Bật',
    'DÃ nh': 'Dành',
    'Tuáº§n nÃ y': 'Tuần này',
    'Tháng nÃ y': 'Tháng này',
    'Nháº¥n Đ\'ỏƒ': 'Nhấn để',
    'Đ\'ỏ™ng': 'động',
    'báº±ng': 'bằng',
    'lưỏ£t': 'lượt',
    'nháº¥t': 'nhất',
    'Láº¥y': 'Lấy',
    'Đ\'úng': 'đúng',
    'cỏ™t': 'cột',
    'gáº§n Đ\'ây': 'gần đây',
    'Thỏi gian': 'Thời gian',
    'Sỏ\'': 'Số',
    'láº§n': 'lần',
    'ngÃ y trưỏ›c': 'ngày trước',
    'lỏ‹ch sỏ­': 'lịch sử',
    'Tỏ\'i Đ\'a': 'Tối đa',
    'Đ\'Ã£ nghe': 'đã nghe',
    'hỏ" sÆ¡': 'hồ sơ',
    'Hỏ" sÆ¡': 'Hồ sơ',
    'Tỏ\'i thiỏƒu': 'Tối thiểu',
    'tỏ±': 'tự',
    'Chỉ dùng chữ, sỏ\'': 'Chỉ dùng chữ, số',
    'tỏ"n': 'tồn',
    'âœï¸': '✏️',
    'ðŸŽµ': '🎵',
    'Bình luáº­n': 'Bình luận',
    'bình luáº­n': 'bình luận',
    'Viáº¿t': 'Viết',
    'Gỏ­i': 'Gửi',
    'Nỏ™i dung': 'Nội dung',
    'Quản LÃ½': 'Quản Lý',
    'tùy chỏn': 'tùy chọn',
}

fixed_count = 0
for fpath in files:
    try:
        with codecs.open(fpath, 'r', 'utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply all replacements
        for wrong, correct in replacements.items():
            content = content.replace(wrong, correct)
        
        if content != original:
            with codecs.open(fpath, 'w', 'utf-8') as f:
                f.write(content)
            fname = fpath.split('/')[-1]
            print(f'✓ Fixed: {fname}')
            fixed_count += 1
        else:
            fname = fpath.split('/')[-1]
            print(f'  OK: {fname}')
            
    except Exception as e:
        print(f'✗ Error: {fpath} - {e}')

print(f'\n=== Completed! Fixed {fixed_count} files ===')
