# -*- coding: utf-8 -*-
import codecs

files_to_fix = {
    'c:/Users/HP/web_nghe_nhac/src/templates/playlists.html': [
        ('Đ\'Ã£ Đ\'ưỏ£c tạo thà nh công', 'đã được tạo thành công'),
        ('káº¿t nỏ\'i', 'kết nối'),
        ('Đ\'áº¿n máy chỏ§', 'đến máy chủ'),
        ('thà nh công', 'thành công'),
        ('playlist nà o', 'playlist nào'),
        ('bà i hát', 'bài hát'),
        ('Đã tải', 'Đã tải'),
        ('Đáº·t rià ªng tư', 'Đặt riêng tư'),
        ('Đang Đ\'áº·t', 'Đang đặt'),
        ('rià ªng tư', 'riêng tư'),
        ('Đà £ Đ\'áº·t', 'Đã đặt'),
        ('playlist nà y', 'playlist này'),
        ('Đà £ xóa', 'Đã xóa'),
    ],
    'c:/Users/HP/web_nghe_nhac/src/templates/playlist.html': [
        ('bà i hát', 'bài hát'),
        ('bà i nà y', 'bài này'),
        ('Chưa có bà i hát nà o', 'Chưa có bài hát nào'),
        ('Thêm bà i hát', 'Thêm bài hát'),
        ('Xóa các bà i Đ\'à £ chỏn', 'Xóa các bài đã chọn'),
        ('Tìm và  thêm bà i hát', 'Tìm và thêm bài hát'),
        ('Tìm bà i hát', 'Tìm bài hát'),
        ('hoáº·c', 'hoặc'),
        ('Thêm các bà i Đ\'à £ tick', 'Thêm các bài đã tick'),
        ('Chỏ‰nh sỏ­a chi tiáº¿t', 'Chỉnh sửa chi tiết'),
        ('Đ\'à £ công khai', 'đã công khai'),
        ('Đ\'à £ chuyỏƒn rià ªng tư', 'đã chuyển riêng tư'),
        ('thông tin bà i hát', 'thông tin bài hát'),
        ('Xóa bà i nà y', 'Xóa bài này'),
        ('Đà £ xóa bà i', 'Đã xóa bài'),
    ],
    'c:/Users/HP/web_nghe_nhac/src/templates/user_profile.html': [
        ('bà i hát', 'bài hát'),
        ('Ngưỏi dùng nà y', 'Người dùng này'),
        ('nà o', 'nào'),
    ],
    'c:/Users/HP/web_nghe_nhac/src/templates/profile.html': [
        ('Bà i hát yêu thích', 'Bài hát yêu thích'),
        ('thà nh công', 'thành công'),
        ('Tỏ\'i thiỏƒu', 'Tối thiểu'),
        ('ká½ tỏ±', 'ký tự'),
        ('Chỏ‰ dùng chỏ¯', 'Chỉ dùng chữ'),
        ('sỏ\'', 'số'),
        ('Đà £ tỏ"n tại', 'Đã tồn tại'),
        ('Đà £ cập nhật', 'Đã cập nhật'),
        ('cháº¯c muỏ\'n', 'chắc muốn'),
        ('Đ\'Đƒng xuất', 'đăng xuất'),
    ],
}

fixed = 0
for fpath, reps in files_to_fix.items():
    try:
        with codecs.open(fpath, 'r', 'utf-8') as f:
            content = f.read()
        
        original = content
        for wrong, correct in reps:
            content = content.replace(wrong, correct)
        
        if content != original:
            with codecs.open(fpath, 'w', 'utf-8') as f:
                f.write(content)
            print(f'✓ Fixed: {fpath.split("/")[-1]}')
            fixed += 1
        else:
            print(f'  OK: {fpath.split("/")[-1]}')
    except Exception as e:
        print(f'✗ Error: {fpath} - {e}')

print(f'\n=== Done! Fixed {fixed} files ===')
