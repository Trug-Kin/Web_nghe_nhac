// Wrap in IIFE to avoid global scope pollution
(function() {
const registerForm = document.getElementById("registerForm");

if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("regUsername").value;
    const email = document.getElementById("regEmail").value;
    const password = document.getElementById("regPassword").value;

    try {
        // Use relative URL so registration works from other devices/hosts
        const res = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include', // include cookies for cross-origin scenarios if needed
          body: JSON.stringify({ username, email, password })
        });

        // Try to parse JSON safely
        let data = {};
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          try { data = await res.json(); } catch (e) { data = {}; }
        }

        if (res.ok) {
          // show inline message (or fallback to alert)
          try { document.getElementById('registerMessage').innerText = data.message || 'Đăng ký thành công!'; } catch(e) { alert(data.message || 'Đăng ký thành công!'); }
          // redirect to login page
          setTimeout(()=> window.location.href = '/auth/login-page', 500);
        } else {
          if (res.status === 401) { window.location.href = '/auth/login-page'; return; }
          const msg = data.error || data.message || res.statusText || 'Đăng ký thất bại!';
          try { document.getElementById('registerMessage').innerText = msg; } catch(e) { alert(msg); }
        }
      } catch (err) {
        console.error('Register request failed:', err);
        alert('Không kết nối được server! Hãy kiểm tra địa chỉ và mạng.');
      }
  });
}
})(); // End IIFE
