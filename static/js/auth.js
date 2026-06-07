async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if(!email || !password){
        alert('Vui lòng nhập đầy đủ email và mật khẩu');
        return;
    }
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // ✅ để nhận cookie JWT
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (response.ok) {
            // Cookie đã được backend set_access_cookies, không cần localStorage nữa
            console.log('[LOGIN] Success, user:', data.user);
            window.location.href = '/auth/profile';
        } else {
            alert(data.msg || 'Email hoặc mật khẩu không đúng!');
        }
    } catch(err){
        console.error('Login error:', err);
        alert('Lỗi kết nối server');
    }
}

function handleLogout() {
    fetch('/auth/logout', {method:'POST', credentials:'include'})
        .then(r=>r.json())
        .catch(()=>({}))
        .finally(()=>{ 
            try{ localStorage.removeItem('access_token'); localStorage.removeItem('user_id'); localStorage.removeItem('username'); localStorage.removeItem('role'); }catch(e){}
            window.location.href = '/'; 
        });
}

const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
}