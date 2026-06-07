"""
Script test API Like & Comment
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# Thông tin test
TEST_USER = {
    "username": "testuser",
    "password": "test123"
}

def test_like_comment_api():
    print("🧪 Testing Like & Comment API\n")
    
    # 1. Login để lấy token
    print("1️⃣ Đăng nhập...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json=TEST_USER
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get('access_token')
        print(f"   ✅ Login thành công! Token: {token[:20]}...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return
    
    # Test với song_id = 1
    song_id = 1
    
    # 2. Test Like
    print(f"\n2️⃣ Like bài hát {song_id}...")
    like_response = requests.post(
        f"{BASE_URL}/api/song/{song_id}/like",
        headers=headers
    )
    print(f"   Status: {like_response.status_code}")
    print(f"   Response: {like_response.json()}")
    
    # 3. Get Like Status
    print(f"\n3️⃣ Lấy trạng thái like...")
    status_response = requests.get(f"{BASE_URL}/api/song/{song_id}/likes")
    print(f"   Status: {status_response.status_code}")
    print(f"   Response: {status_response.json()}")
    
    # 4. Add Comment
    print(f"\n4️⃣ Thêm bình luận...")
    comment_response = requests.post(
        f"{BASE_URL}/api/song/{song_id}/comments",
        headers=headers,
        json={'content': 'Bài hát hay quá! 🎵'}
    )
    print(f"   Status: {comment_response.status_code}")
    print(f"   Response: {comment_response.json()}")
    
    # 5. Get Comments
    print(f"\n5️⃣ Lấy danh sách bình luận...")
    comments_response = requests.get(f"{BASE_URL}/api/song/{song_id}/comments")
    print(f"   Status: {comments_response.status_code}")
    data = comments_response.json()
    print(f"   Số lượng comments: {data.get('count')}")
    if data.get('comments'):
        for comment in data['comments'][:3]:
            print(f"   - {comment['username']}: {comment['content']}")
    
    # 6. Unlike
    print(f"\n6️⃣ Unlike bài hát...")
    unlike_response = requests.post(
        f"{BASE_URL}/api/song/{song_id}/like",
        headers=headers
    )
    print(f"   Status: {unlike_response.status_code}")
    print(f"   Response: {unlike_response.json()}")
    
    print("\n✅ Test hoàn tất!")

if __name__ == "__main__":
    try:
        test_like_comment_api()
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối server. Hãy chạy: python app.py")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
