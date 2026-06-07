// Wrap in IIFE to avoid global scope pollution
(function() {
const loginForm = document.getElementById("loginForm");
console.log("Kết quả tìm form:", loginForm);
const result = document.getElementById("result");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

  // prefer legacy ids (loginUsername/loginPassword) to keep behavior identical to older pages
  const usernameEl = document.getElementById("loginUsername") || document.getElementById("username");
  const passwordEl = document.getElementById("loginPassword") || document.getElementById("password");
  const username = usernameEl ? usernameEl.value.trim() : '';
  const password = passwordEl ? passwordEl.value.trim() : '';

    try {
          // If the user typed an email (contains '@'), send it as email so server will lookup by email.
          const isEmail = username && username.indexOf('@') !== -1;
          const payload = isEmail ? { email: username, password } : { username, password };
          const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
          });

      // Try to parse JSON only when response has JSON content-type
      let data = {};
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
            try { 
              data = await res.json(); 
            } catch (e) { 
              data = {}; 
            }
      } else {
        // If server returned HTML (error page), capture text for debugging
        const txt = await res.text();
        console.error('Non-JSON response from /auth/login:', res.status, txt.slice(0, 200));
      }

      if (res.ok) {
        console.log('[Login] Success! Cookie should be set by server');
        
        // Server already set the JWT cookie via set_access_cookies()
        // No need to manually save to localStorage
        
        // Save user info to localStorage for UI purposes only
        const usernameFromResp = (data && data.user && data.user.username) || (data && data.username);
        if (usernameFromResp) {
          localStorage.setItem('username', usernameFromResp);
          const roleFromResp = data && data.user && data.user.role;
          if (roleFromResp) localStorage.setItem('role', roleFromResp);
          const uid = data && data.user && data.user.id;
          if (uid) localStorage.setItem('user_id', String(uid));
        }

        // Update UI immediately
        if (typeof checkLoginStatus === 'function') {
          checkLoginStatus();
        }
        
        // Show success message
        result.textContent = data?.msg || 'Đăng nhập thành công!';
        result.style.color = '#1db954';
        
        // Navigate to home page after short delay
        setTimeout(() => {
          window.location.href = '/';
        }, 800);
      } else {
        const errMsg = data.error || data.message || res.statusText || 'Đăng nhập thất bại!';
        result.textContent = errMsg;
      }
    } catch (err) {
      console.error(err);
      result.innerText = "Không kết nối được server!";
    }
  });
}

// ---- Logout ----
const logoutBtn = document.getElementById("logout-btn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    try {
      // Call server logout (optional) and clear localStorage tokens
    const res = await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
    localStorage.removeItem("username");
    localStorage.removeItem('role');
    localStorage.removeItem('user_id');
    localStorage.removeItem('access_token');
      // show small inline message or fallback to console then redirect
      console.log('Logged out', res.status);
      // update UI immediately
      if (typeof window.updateUserUIonPageLoad === 'function') window.updateUserUIonPageLoad();
      window.location.href = '/';
    } catch (err) {
      console.error('Logout failed', err);
      // still redirect to homepage
      window.location.href = '/';
    }
    
  });
  
}

// Update header UI based on localStorage username/role
function updateUserUIonPageLoad(){
  try{
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('role');
    const loggedInView = document.getElementById('logged-in-view');
    const loggedOutView = document.getElementById('logged-out-view');
    const profileUsername = document.getElementById('profile-username');
  const createBtn = document.getElementById('create-playlist-btn');
  const myPlaylistsLink = document.getElementById('my-playlists-link');

    if(username){
      if(loggedInView) loggedInView.style.display = 'block';
      if(loggedOutView) loggedOutView.style.display = 'none';
      if(profileUsername) profileUsername.innerText = username;
      // show create playlist only to allowed roles
      if(createBtn){
        if(['user','uploader','admin'].includes(role)) createBtn.style.display = 'inline';
        else createBtn.style.display = 'none';
      }
      if(myPlaylistsLink){
        if(['user','uploader','admin'].includes(role)) myPlaylistsLink.style.display = 'inline';
        else myPlaylistsLink.style.display = 'none';
      }
    } else {
      if(loggedInView) loggedInView.style.display = 'none';
      if(loggedOutView) loggedOutView.style.display = 'block';
  if(createBtn) createBtn.style.display = 'none';
  if(myPlaylistsLink) myPlaylistsLink.style.display = 'none';
    }
  }catch(e){console.error('updateUserUIonPageLoad error', e)}
}

// Run on load so header reflects current login state
document.addEventListener('DOMContentLoaded', ()=>{
  updateUserUIonPageLoad();
});

// expose globally so other scripts can call it
window.updateUserUIonPageLoad = updateUserUIonPageLoad;
})(); // End IIFE
