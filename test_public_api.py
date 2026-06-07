"""Test API public playlists"""
import urllib.request
import json

response = urllib.request.urlopen('http://127.0.0.1:5000/api/playlists/public')
data = json.loads(response.read().decode('utf-8'))

print(f"Status: {response.status}")
print(f"📊 Số playlist công khai: {len(data)}")

if data:
    print("\n📋 Chi tiết:")
    for p in data:
        print(f"  - ID {p['id']}: {p['name']}")
        print(f"    User: {p['username']}")
        print(f"    Bài hát: {p['song_count']}")
        print(f"    Ảnh: {p['image_path']}")
        print()
