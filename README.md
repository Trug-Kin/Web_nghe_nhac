## Nghệ Sĩ Đang Nổi (Rising Score)

Hệ thống tính điểm động để xếp hạng nghệ sĩ dựa trên tăng trưởng và mức độ tương tác trong 30 ngày gần nhất.

### Thành phần dữ liệu
- streams_current: lượt nghe 30 ngày gần nhất
- streams_previous: lượt nghe 30–60 ngày trước
- followers_new: số lượt follow mới (cần cột followed_at)
- playlist_adds: số lần bài thuộc nghệ sĩ được thêm playlist 30 ngày
- search_hits: số lượt tìm kiếm (ghi qua bảng `search_events`)
- social_mentions: placeholder (chưa tích hợp)
- growth_rate = (streams_current - streams_previous) / max(streams_previous, 1), clamp 500%
- rising_score: công thức trọng số trong `config.py` (RISING_SCORE_WEIGHTS)
- moving_avg_score (EMA): làm mịn (0.7 * cũ + 0.3 * mới)

### Migrations cần chạy
```powershell
alembic upgrade head
```
Đảm bảo các file migration mới:
1. `20251120_add_artist_stats_and_followed_at.py`
2. `20251120_add_artist_stats_badge_fields.py`
3. `20251120_add_search_events_and_moving_avg.py`

### Cập nhật thống kê
```powershell
python -m scripts.update_artist_stats
```
Nên lập lịch (Windows Task Scheduler / cron) chạy mỗi 6h hoặc hàng ngày:
```powershell
python -m scripts.update_artist_stats >> logs/artist_stats.log 2>&1
```

### Điều chỉnh trọng số
Sửa trong `config.py`:
```python
RISING_SCORE_WEIGHTS = {
	'growth_rate': 0.4,
	'followers_new': 0.25,
	'playlist_adds': 0.20,
	'search_hits': 0.10,
	'social_mentions': 0.05,
}
```
Tăng giảm theo ưu tiên nền tảng.

### Badges hiển thị
- Top 1/2/3: theo vị trí sau sắp xếp theo `moving_avg_score`.
- Mới: xuất hiện lần đầu trong top (<= 2 ngày kể từ `first_seen_in_top_at`).
- Growth: growth_rate_pct ≥ 150% (có thể đổi ngưỡng trong code).

### Ghi log tìm kiếm
Route `/api/search` tự ghi tối đa 5 nghệ sĩ khớp vào bảng `search_events`. Tránh ghi quá nhiều để giảm tải DB.

### Mở rộng tiếp theo
- Tích hợp social mentions
- Lưu log search chi tiết theo user (thêm user_id thực)
- Thống kê 7d rolling window riêng
- API bộ lọc theo genre

````markdown
# Web Nghe Nhạc (Flask)

This project is a Flask-based music site that serves a static frontend in `static` and a Flask backend under `src/`.

Quick goals:
- Keep the existing UI in `static` working.
- Provide instructions to run locally and publish to other devices.

## Requirements
- Python 3.10+ (virtualenv recommended)
- MySQL (or change `SQLALCHEMY_DATABASE_URI` to another DB)

## Setup (Windows PowerShell)
```powershell
# create virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# initialize DB (if needed)
python create_db.py

# run dev server
python app.py
```

## JWT Cookie Configuration
Development settings currently use:
- `JWT_COOKIE_SAMESITE = "Lax"` to allow cookie send on localhost without HTTPS.
- `JWT_COOKIE_SECURE = False`

For production (HTTPS domain):
1. Set `JWT_COOKIE_SECURE = True`
2. If you need cross-site requests (different frontend domain), change `JWT_COOKIE_SAMESITE = "None"`
3. Keep `JWT_TOKEN_LOCATION = ["cookies", "headers"]` so API clients (tests / mobile) can still pass `Authorization: Bearer <token>`.
4. Consider enabling CSRF protection (`JWT_COOKIE_CSRF_PROTECT = True`) and include the CSRF token header in POST/PUT/DELETE requests.

Troubleshooting:
- If login succeeds but subsequent requests say missing JWT, check DevTools Application > Cookies for `access_token`.
- Chrome requires Secure+SameSite=None together; using None on HTTP will silently drop the cookie.

The app serves static files from the `static` folder by default (see `app.create_app()`), so the UI should remain unchanged.

## Running in production (Windows)
Option A: Waitress (recommended on Windows)
```powershell
# activate venv first
pip install waitress
# run with waitress
python -c "from app import create_app; from waitress import serve; app=create_app(); serve(app, host='0.0.0.0', port=5000)"
```

Option B: Docker (Linux/any)
- Example Dockerfile (project root):
```
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENV FLASK_ENV=production
ENV DATABASE_URL=<your_db_url>
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t web-nghe-nhac .
docker run -p 5000:5000 -e DATABASE_URL="mysql+pymysql://..." web-nghe-nhac
```

## Public access
- Open port 5000 on your server and point your router / firewall to that machine.
- Ensure `SQLALCHEMY_DATABASE_URI` points to a DB accessible from the server.

## Notes
- The backend returns JWT access tokens on login. Frontend already saves tokens and updates the UI (login -> username) by reading token payload or the returned `user` object.
- If you want to switch to cookie-based auth (httponly cookies), let me know and I can update `src/auth/routes.py` + frontend.
- Smooth homepage transition & uninterrupted playback: Clicking Trang chủ now uses SPA (AJAX) navigation (see `static/js/spa-router.js`) so the audio player keeps playing. A fade-out/in effect around `#main-content` is applied; adjust durations in `navigateTo()` (transition `.28s`) and CSS in `base.html`. If a page really needs a full reload, add its path to `fullReloadPaths` inside `spa-router.js`.

If you want, I can add a small `docker-compose.yml` and example systemd service/unit file for Linux servers.
\n+## Right-Click Playlist Menu Feature\n+You can right-click (chuột phải) on any song row (BXH, playlist của tôi, bài hát yêu thích, v.v.) to open a custom context menu:\n+\n+**Chức năng trong menu:**\n+- Tìm kiếm playlist nhanh (lọc client-side).\n+- Thêm bài hát vào playlist đã có.\n+- Tạo playlist mới và tự động thêm bài hát vừa chọn.\n+- Toast thông báo thành công / lỗi.\n+\n+**Kỹ thuật:**\n+- Markup: `src/templates/base.html` (`#song-context-menu`).\n+- Logic: `static/js/context_menu.js` (dùng API `/api/playlists/`, `/api/playlists/<id>/add_song`, `POST /api/playlists`).\n+- Styles: `static/css/context_menu.css`.\n+- Cache: Danh sách playlist cache ~60s để hạn chế gọi API liên tiếp.\n+\n+**Cách dùng nhanh:**\n+1. Đăng nhập.\n+2. Chuột phải vào dòng bài hát.\n+3. Chọn playlist hoặc bấm tạo mới.\n+4. Xem dấu ✓ sau khi thêm thành công.\n+\n+Nếu cần thêm tính năng (ví dụ: bulk add từ context menu, ghim playlist hay phân trang) cứ yêu cầu.\n*** End Patch
````
---

If you want any of the next steps above, say which one and I'll implement it.
```