"""
Quick test để kiểm tra API endpoint có hoạt động không
"""
import requests

BASE_URL = "http://localhost:5000"

print("🧪 Testing API endpoints...\n")

# 1. Test endpoint có tồn tại không (GET likes)
print("1️⃣ Test GET /api/song/1/likes (không cần login)")
try:
    response = requests.get(f"{BASE_URL}/api/song/1/likes")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Test các route khác
print("\n2️⃣ Danh sách routes đã đăng ký:")
try:
    # Gọi một endpoint debug nếu có
    print("   Kiểm tra trong Flask console...")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n💡 Hướng dẫn:")
print("   - Mở DevTools (F12) trong browser")
print("   - Vào tab Network")
print("   - Click nút Like")
print("   - Xem request /api/song/X/like có được gửi không")
print("   - Kiểm tra response status và error message")
