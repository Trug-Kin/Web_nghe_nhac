"""
Test JWT token storage in browser
"""
print("""
🔍 KIỂM TRA JWT TOKEN TRONG BROWSER

Hãy mở DevTools (F12) trong browser và chạy đoạn code này trong Console:

// 1. Kiểm tra token trong localStorage
console.log('Access Token:', localStorage.getItem('access_token'));

// 2. Kiểm tra cookies
console.log('Cookies:', document.cookie);

// 3. Test API với token
const token = localStorage.getItem('access_token');
if (token) {
    fetch('/api/song/1/likes', {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    })
    .then(r => r.json())
    .then(data => console.log('API Response:', data))
    .catch(err => console.error('API Error:', err));
} else {
    console.log('❌ KHÔNG CÓ TOKEN - Hãy đăng nhập lại!');
}

// 4. Kiểm tra user hiện tại
fetch('/api/current_user', {
    headers: {
        'Authorization': 'Bearer ' + (localStorage.getItem('access_token') || '')
    }
})
.then(r => r.json())
.then(data => console.log('Current User:', data))
.catch(err => console.error('User Error:', err));

---

📝 CÁCH FIX NẾU KHÔNG CÓ TOKEN:

1. Vào trang login: http://127.0.0.1:5000/auth/login-page
2. Đăng nhập với:
   - Email: kaito2106150881234@gmail.com
   - Password: 123456
   
   HOẶC
   
   - Email: kaka@gmail.com  
   - Password: 12345678

3. Sau khi login thành công, token sẽ được lưu vào:
   - localStorage['access_token']
   - Cookie['access_token']

4. Thử lại vào trang "Lịch sử nghe"

---

⚠️  LƯU Ý:
- Route /history yêu cầu JWT token
- Nếu không có token → redirect về login page
- Token được lưu khi login thành công
- Token format: "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
""")
