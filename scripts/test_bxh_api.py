import requests
import json

# Thay đổi URL nếu backend không chạy ở localhost:5000
url = 'http://127.0.0.1:5000/api/bxh/songs?filter=all'

response = requests.get(url)
print('Status:', response.status_code)
try:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print('Không phải JSON:', e)
    print(response.text)
