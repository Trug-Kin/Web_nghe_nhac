# Tính năng Bài hát yêu thích & Lịch sử nghe

## Đã thêm:

### 1. Routes mới (`src/music/routes.py`):
- **`/liked-songs`** - Hiển thị danh sách bài hát user đã like
  - JOIN Like với Song để lấy thông tin đầy đủ
  - Sắp xếp theo thời gian like (mới nhất trước)
  - Yêu cầu JWT authentication

- **`/history`** - Hiển thị lịch sử nghe nhạc
  - JOIN ListeningHistory với Song
  - GROUP BY bài hát, đếm số lần nghe (`play_count`)
  - Hiển thị thời gian nghe gần nhất (`last_played`)
  - Giới hạn 100 bài gần nhất
  - Yêu cầu JWT authentication

### 2. Templates mới:

**`src/templates/liked_songs.html`**:
- Table hiển thị bài hát yêu thích với columns: #, Tiêu đề, Nghệ sĩ, Album, Thể loại, Thích
- Nút like màu đỏ (đã thích) trên mỗi hàng
- Click row để phát nhạc
- Empty state nếu chưa có bài nào

**`src/templates/history.html`**:
- Table với columns: #, Tiêu đề, Nghệ sĩ, Album, Số lần nghe, Nghe gần nhất, Thích
- Badge số lần nghe với icon headphones
- Format thời gian relative (vừa xong, 5 phút trước, 2 giờ trước, etc.)
- Load like status cho mỗi bài
- Empty state nếu chưa nghe bài nào

### 3. Navigation:
- Thêm 2 links trong dropdown menu profile (base.html):
  - ❤️ Bài hát yêu thích
  - 🕐 Lịch sử nghe
- Cả 2 chỉ hiển thị khi đã đăng nhập

### 4. Styling:
- Dark theme matching với design hiện tại
- Hover effects trên table rows
- Play icon xuất hiện khi hover
- Like button với animation
- Responsive layout

## Cách sử dụng:

1. **Đăng nhập** vào tài khoản
2. **Click vào avatar** ở góc phải navbar
3. **Chọn "Bài hát yêu thích"** hoặc **"Lịch sử nghe"**
4. Click bài hát để phát, click ❤️ để unlike

## API Endpoints (internal):
- `GET /liked-songs` - Render template liked songs
- `GET /history` - Render template listening history
- `POST /api/song/<id>/like` - Toggle like (đã có sẵn)
- `GET /api/listening_history` - API lấy lịch sử (đã có sẵn)

## Database:
- Sử dụng table `likes` (user_id, song_id, created_at)
- Sử dụng table `listening_history` (user_id, song_id, listened_at)
- Cả 2 đã tồn tại trong MySQL database

## Notes:
- Cần đăng nhập (JWT token) để xem 2 trang này
- Nếu chưa login → redirect về login page
- Like status tự động load khi mở trang
- Integration với player hiện tại (app.js)
