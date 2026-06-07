import requests

# Test Artist API
print('=== Testing /api/artist/1 ===')
try:
    r = requests.get('http://127.0.0.1:5000/api/artist/1')
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Artist name: {data.get("name")}')
        print(f'Image path: {data.get("image_path")}')
        print(f'Number of songs: {len(data.get("songs", []))}')
        if data.get("songs"):
            print(f'First song: {data["songs"][0].get("title")}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Exception: {e}')

print('\n=== Testing /api/album/1 ===')
try:
    r = requests.get('http://127.0.0.1:5000/api/album/1')
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Album name: {data.get("name")}')
        print(f'Image path: {data.get("image_path")}')
        print(f'Number of songs: {len(data.get("songs", []))}')
        if data.get("songs"):
            print(f'First song: {data["songs"][0].get("title")}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
