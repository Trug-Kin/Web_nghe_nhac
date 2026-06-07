"""Test xem route home có trả về public playlists không"""
import urllib.request

response = urllib.request.urlopen('http://127.0.0.1:5000/')
html = response.read().decode('utf-8')
print(f"Status: {response.status}")

# Kiểm tra có chứa text "Playlist Công Khai" không
if "Playlist Công Khai" in html:
    print("✅ Tìm thấy section 'Playlist Công Khai'")
else:
    print("❌ Không tìm thấy section 'Playlist Công Khai'")

# Kiểm tra có playlist nào không
if "playlist-card" in html:
    print("✅ Tìm thấy playlist card")
    
    # Đếm số lượng playlist cards
    count = html.count('<div class="playlist-card"')
    print(f"📊 Số playlist cards: {count}")
else:
    print("❌ Không tìm thấy playlist card nào")

# Kiểm tra có text fallback "Chưa có playlist công khai nào" không
if "Chưa có playlist công khai nào" in html:
    print("⚠️ Hiển thị message rỗng (không có playlist công khai)")
