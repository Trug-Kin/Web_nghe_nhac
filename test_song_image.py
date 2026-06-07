"""
Script test xem ảnh bài hát có hiển thị không sau khi sửa
"""
import requests

# Test API trả về image_path của bài hát
print("🧪 Testing song image API...")

# Test search API
response = requests.get('http://127.0.0.1:5000/api/search?q=a')
if response.status_code == 200:
    data = response.json()
    if data.get('songs'):
        song = data['songs'][0]
        print(f"\n✅ Search API Response:")
        print(f"   Song: {song.get('title')}")
        print(f"   image_path: {song.get('image_path')}")
        print(f"   album_image_path: {song.get('album_image_path')}")
    else:
        print("⚠️ No songs found in search")
else:
    print(f"❌ Search API failed: {response.status_code}")

# Test artist detail API
response = requests.get('http://127.0.0.1:5000/api/artist/1')
if response.status_code == 200:
    data = response.json()
    if data.get('songs'):
        song = data['songs'][0]
        print(f"\n✅ Artist Detail API Response:")
        print(f"   Song: {song.get('title')}")
        print(f"   image_path: {song.get('image_path')}")
        print(f"   album_image_path: {song.get('album_image_path')}")
    else:
        print("⚠️ No songs found for this artist")
else:
    print(f"❌ Artist API failed: {response.status_code}")

print("\n" + "="*60)
print("Nếu image_path có giá trị (không phải None), nghĩa là API đã OK!")
print("Bây giờ hãy F5 trang web để xem ảnh hiển thị")
print("="*60)
