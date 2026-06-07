
// Prevent duplicate execution
if (window.loginButtonJsInitialized) {
    // Already initialized, skipping silently
} else {
    window.loginButtonJsInitialized = true;

(function() {
    'use strict';

// Lắng nghe sự kiện khi toàn bộ trang đã được tải
document.addEventListener("DOMContentLoaded", function () {
    // Lắng nghe SPA navigation để refresh trạng thái đăng nhập + danh sách nghệ sĩ đã follow
    window.addEventListener('spa-navigated', function() {
        checkLoginStatus();
        // Luôn thử reload danh sách nghệ sĩ đã follow (phòng trường hợp section bị thay thế khi chuyển trang SPA)
        try {
            const token = getJwtToken();  // Get from cookie instead
            if (window.loadFollowedArtistsSidebar) window.loadFollowedArtistsSidebar(token);
        } catch(e) { console.debug('[followed-artists] spa-navigated reload error', e); }
    });
  

    // --- PHẦN 1: LOGIC LUÔN CHẠY TRÊN MỌI TRANG ---
    checkLoginStatus(); // Luôn kiểm tra trạng thái đăng nhập đầu tiên
    loadTrendingArtistsSidebar(); // Luôn load trending artists cho sidebar
    // Thử load danh sách nghệ sĩ đã follow ngay khi DOM sẵn sàng (trước cả khi /auth/me phản hồi)
    try {
        const earlyToken = getJwtToken();  // Get from cookie instead
        if (window.loadFollowedArtistsSidebar) window.loadFollowedArtistsSidebar(earlyToken);
    } catch(e) { console.debug('[followed-artists] early DOM load error', e); }

    // Force re-check after auth may have finished but sidebar still shows 'Đang tải...'
    setTimeout(() => { try { maybeForceReloadFollowed(); } catch(e){} }, 1000);
    setTimeout(() => { try { maybeForceReloadFollowed(); } catch(e){} }, 3000);
// Hàm load sidebar nghệ sĩ đang nổi
function loadTrendingArtistsSidebar() {
    const section = document.getElementById('trending-artists-section');
    const list = document.getElementById('trending-artists-list');
    if (!section || !list) return;
    list.innerHTML = '<li style="color:#888;font-size:13px;">Đang tải...</li>';
    fetch('/api/trending-artists')
        .then(res => res.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                list.innerHTML = '<li style="color:#888;font-size:13px;">Không có dữ liệu</li>';
                return;
            }
            list.innerHTML = '';
            data.forEach(artist => {
                const li = document.createElement('li');
                li.className = 'sidebar-artist-item';
                li.innerHTML = `
                    <a href="/artist/${artist.id}" style="display:flex;align-items:center;gap:8px;text-decoration:none;color:inherit;">
                        <img src="${artist.image_path ? ('/static/' + artist.image_path) : '/static/images/default.jpg'}" alt="${artist.name}" style="width:28px;height:28px;object-fit:cover;border-radius:50%;border:1.5px solid #444;">
                        <span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${artist.name}</span>
                        <span style="font-size:12px;color:#0af;font-weight:600;">${artist.score}</span>
                    </a>
                `;
                list.appendChild(li);
            });
        })
        .catch(() => {
            list.innerHTML = '<li style="color:#888;font-size:13px;">Lỗi tải dữ liệu</li>';
        });
}

  // --- PHẦN 2: LOGIC CHỈ DÀNH CHO MENU DROPDOWN (NẾU CÓ) ---
  // Mã này sẽ tự kiểm tra và không gây lỗi nếu không có menu
  const dropdown = document.querySelector(".dropdown");
  if (dropdown) {
    const menu = dropdown.querySelector(".dropdown-content");
    if(menu) { // Kiểm tra thêm menu có tồn tại không
        let hideTimeout;

        dropdown.addEventListener("mouseenter", () => {
          clearTimeout(hideTimeout);
          menu.style.opacity = "1";
          menu.style.visibility = "visible";
        });
    
        dropdown.addEventListener("mouseleave", () => {
          hideTimeout = setTimeout(() => {
            menu.style.opacity = "0";
            menu.style.visibility = "hidden";
          }, 400);
        });
    }
  }

  // --- PHẦN 3: LOGIC CHỈ DÀNH CHO TRANG PROFILE.HTML ---
  // Tất cả các lệnh dưới đây đã được "bảo vệ" bằng 'if' để không gây lỗi
  
  // Chỉ tải thông tin user khi ở trang profile
  if (document.getElementById("username")) { 
      loadUserProfile();
  }
  
  const changeAvatarBtn = document.getElementById("change-avatar");
  if (changeAvatarBtn) {
    changeAvatarBtn.addEventListener("click", function () {
      document.getElementById("avatar-form").style.display = "block";
    });
  }
  
  const avatarForm = document.getElementById("avatar-form");
  if (avatarForm) {
      avatarForm.addEventListener("submit", handleAvatarSubmit); // Tách ra hàm riêng cho gọn
  }

  const editInfoBtn = document.getElementById("edit-info-btn");
  if (editInfoBtn) {
      editInfoBtn.addEventListener("click", function() {
          document.getElementById("edit-info").style.display = "block";
          document.getElementById("change-password-form").style.display = "none";
      });
  }

  // ... (Tương tự, bạn có thể thêm các 'if' cho các nút còn lại trên trang profile nếu cần)
});

// --- CÁC HÀM CỐT LÕI ---

// Kiểm tra trạng thái đăng nhập bằng cách gọi /auth/me (gửi cookie + fallback Authorization)
async function checkLoginStatus() {
    const token = getJwtToken();  // Get from cookie instead
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    try {
        const res = await fetch('/auth/me', { credentials: 'include', headers });
        if (!res.ok) {
            resetUI();
            return;
        }
        const data = await res.json().catch(()=>null);
        if (!data) { 
            resetUI(); 
            return; 
        }
        // Update UI with returned user data (reuse logic from setLoggedInUI)
        applyLoggedInUIFromData(data);
    } catch (err) {
        console.error('[checkLoginStatus] Error:', err);
        resetUI();
    }
}

function applyLoggedInUIFromData(data){
    const loggedOutView = document.getElementById("logged-out-view");
    const loggedInView = document.getElementById("logged-in-view");
    const userControls = document.querySelector(".user-controls");

    if (loggedOutView) loggedOutView.style.display = "none";
    if (loggedInView) loggedInView.style.display = "flex";
    if (userControls) userControls.style.visibility = "visible";

    if (data.username) {
        const profileUsername = document.getElementById("profile-username");
        const profileAvatar = document.getElementById("profile-avatar");
        if(profileUsername) profileUsername.textContent = data.username;
        if(profileAvatar) {
            const avatarUrl = data.avatar_url || 'images/default.jpg';
            profileAvatar.src = '/static/' + avatarUrl.replace(/^\/+/, '') + '?t=' + Date.now();
        }

        const role = (data.role || '').toLowerCase();

        // Show auth-required sections
        const authRequiredElements = document.querySelectorAll('.auth-required');
        authRequiredElements.forEach(el => { el.style.display = 'block'; });

        // Show admin section in sidebar
        const adminSection = document.getElementById('admin-section');
        const adminManageUsersLink = document.getElementById('admin-manage-users-link');
        const adminManageMusicLink = document.getElementById('admin-manage-music-link');
        if(adminSection && (role === 'admin' || role === 'uploader')) {
            adminSection.style.display = 'block';
            if(role === 'admin'){
                if(adminManageUsersLink) adminManageUsersLink.parentElement.style.display = 'list-item';
                if(adminManageMusicLink) adminManageMusicLink.parentElement.style.display = 'list-item';
            } else {
                if(adminManageUsersLink) adminManageUsersLink.parentElement.style.display = 'none';
                if(adminManageMusicLink) adminManageMusicLink.parentElement.style.display = 'list-item';
            }
        } else {
            if(adminSection) adminSection.style.display = 'none';
        }
    }
    // load followed artists
    try { loadFollowedArtistsSidebar(getJwtToken() || ''); } catch(e){}
}

// Cập nhật giao diện KHI ĐÃ ĐĂNG NHẬP (Dùng cho nút Spotify)
function setLoggedInUI() {
    const loggedOutView = document.getElementById("logged-out-view");
    const loggedInView = document.getElementById("logged-in-view");
    const userControls = document.querySelector(".user-controls");

    if (loggedOutView) loggedOutView.style.display = "none";
    if (loggedInView) loggedInView.style.display = "flex";
    if (userControls) userControls.style.visibility = "visible";

    // Lấy thông tin người dùng và cập nhật
    const token = getJwtToken();
    console.log("[DEBUG] Token found:", token ? "YES" : "NO");
    if (token) {
            fetch("/auth/me", {
            headers: { 'Authorization': `Bearer ${token}` },
            credentials: 'include'
        })
        .then(res => {
            console.log("[DEBUG] /auth/me response status:", res.status);
            return res.json();
        })
        .then(data => {
            console.log("[DEBUG] User data from /auth/me:", data);
            const adminManageUsersLink = document.getElementById("admin-manage-users-link");
            const adminManageMusicLink = document.getElementById("admin-manage-music-link");
            const adminSection = document.getElementById("admin-section");
            
            console.log("[DEBUG] adminManageUsersLink:", adminManageUsersLink);
            console.log("[DEBUG] adminManageMusicLink:", adminManageMusicLink);
            console.log("[DEBUG] adminSection:", adminSection);
            
            if (data.username) {
                const profileUsername = document.getElementById("profile-username");
                const profileAvatar = document.getElementById("profile-avatar");
                if(profileUsername) profileUsername.textContent = data.username;
                if(profileAvatar) {
                    const avatarUrl = data.avatar_url || 'images/default.jpg';
                    profileAvatar.src = '/static/' + avatarUrl.replace(/^\/+/,'') + '?t=' + Date.now();
                    console.log("[DEBUG] Avatar loaded:", avatarUrl);
                }
                console.log("[DEBUG] User role:", data.role);
                
                const role = (data.role || '').toLowerCase();
                console.log("[DEBUG] Role after toLowerCase:", role);
                
                // Show auth-required sections
                const authRequiredElements = document.querySelectorAll(".auth-required");
                authRequiredElements.forEach(el => {
                    el.style.display = "block";
                });
                
                // Show admin section in sidebar
                if(adminSection && (role === 'admin' || role === 'uploader')) {
                    adminSection.style.display = 'block';
                    
                    // Admin: show both users + music; Uploader: only music
                    if(role === 'admin') {
                        if(adminManageUsersLink) adminManageUsersLink.parentElement.style.display = 'list-item';
                        if(adminManageMusicLink) adminManageMusicLink.parentElement.style.display = 'list-item';
                    } else {
                        // Uploader: hide user management
                        if(adminManageUsersLink) adminManageUsersLink.parentElement.style.display = 'none';
                        if(adminManageMusicLink) adminManageMusicLink.parentElement.style.display = 'list-item';
                    }
                } else {
                    if(adminSection) adminSection.style.display = 'none';
                }
            }
        })
        .catch(err => console.error("[DEBUG] Lỗi lấy thông tin user:", err));
    // Load sidebar nghệ sĩ đã follow
    loadFollowedArtistsSidebar(token);
// Hàm load sidebar nghệ sĩ đã follow
// Make this function resilient and accessible globally so other pages can refresh the sidebar
function loadFollowedArtistsSidebar(token) {
    const section = document.getElementById('followed-artists-section');
    const list = document.getElementById('followed-artists-list');
    if (!section || !list) return;
    section.style.display = 'block';
    // Nếu đã có server render danh sách (ít nhất 1 <li> và không phải loading-state) thì không reset về 'Đang tải...'
    const alreadyPopulated = list.querySelector('li') && !list.querySelector('[data-state="loading"]') && list.querySelectorAll('li').length > 0;
    if (!alreadyPopulated) {
        list.innerHTML = '<li data-state="loading" style="color:#888;font-size:13px;">Đang tải...</li>';
    }

    // build headers preferring cookie-based auth when possible
    const headers = (window.buildHeaders ? window.buildHeaders('application/json') : (token ? { 'Authorization': `Bearer ${token}`, 'Content-Type':'application/json' } : { 'Content-Type':'application/json' }));
    console.debug('[sidebar] fetching /api/user/followed-artists, with headers:', headers);

    // timeout fallback: if no response within 2s, probe /auth/me (cookie-only)
    let resolved = false;
    const fallbackCheck = setTimeout(() => {
        if (!resolved && list.querySelector('[data-state="loading"]')) {
            console.warn('[sidebar] slow response -> retry once without Authorization header');
            fetch('/api/user/followed-artists', { credentials: 'include' })
                .then(r => r.ok ? r.json() : [])
                .then(data => { resolved = true; renderFollowedArtistsList(list, data); })
                .catch(e => { console.error('[sidebar] retry error', e); list.innerHTML = '<li style="color:#888;font-size:13px;">Lỗi tải danh sách.</li>'; });
        }
    }, 1800);

    fetch('/api/user/followed-artists', { headers, credentials: 'include' })
        .then(res => {
            console.debug('[sidebar] first call status', res.status);
            if (!res.ok) {
                if ((res.status === 401 || res.status === 403) && headers['Authorization']) {
                    return fetch('/api/user/followed-artists', { credentials: 'include' })
                        .then(r2 => r2.ok ? r2.json() : []);
                }
                if (res.status === 401 || res.status === 403) return [];
                throw new Error('non-ok');
            }
            return res.json();
        })
        .then(data => { resolved = true; clearTimeout(fallbackCheck); renderFollowedArtistsList(list, data); })
        .catch(err => { resolved = true; clearTimeout(fallbackCheck); console.error('[sidebar] load error', err); list.innerHTML = '<li style="color:#888;font-size:13px;">Lỗi tải danh sách.</li>'; });
}

// expose for other modules/pages to call after follow/unfollow actions
try { window.loadFollowedArtistsSidebar = loadFollowedArtistsSidebar; } catch(e){}
    }
}

// Cập nhật giao diện KHI CHƯA ĐĂNG NHẬP (Dùng cho nút Spotify)
function resetUI() {
    const loggedOutView = document.getElementById("logged-out-view");
    const loggedInView = document.getElementById("logged-in-view");
    const userControls = document.querySelector(".user-controls");
    const adminSection = document.getElementById("admin-section");
    const authRequiredElements = document.querySelectorAll(".auth-required");

    if (loggedOutView) loggedOutView.style.display = "block";
    if (loggedInView) loggedInView.style.display = "none";
    if (userControls) userControls.style.visibility = "visible";
    if (adminSection) adminSection.style.display = "none";
    
    // Hide auth-required sidebar sections
    authRequiredElements.forEach(el => {
        el.style.display = "none";
    });
}

// Hàm xử lý đăng xuất
function onLogout(e) {
    e.preventDefault();
    document.cookie = "access_token=;expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    resetUI();
    window.location.href = "/"; // Chuyển về trang chủ
}

// Hàm tải thông tin user cho trang profile
function loadUserProfile() {
    const token = getJwtToken();
    if (!token) return;

    fetch("/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.username) {
            const usernameEl = document.getElementById("username");
            const emailEl = document.getElementById("email");
            const avatarEl = document.getElementById("avatar");
            if(usernameEl) usernameEl.textContent = data.username;
            if(emailEl) emailEl.textContent = data.email;
            if(data.avatar_url && avatarEl) {
                avatarEl.src = data.avatar_url;
            }
        }
    })
    .catch(error => console.error("Lỗi tải thông tin user:", error));
}

// Hàm xử lý khi submit form avatar
function handleAvatarSubmit(e) {
    e.preventDefault();
    const avatarFile = document.getElementById("avatar-file").files[0];
    if (avatarFile) {
        const formData = new FormData();
        formData.append("avatar", avatarFile);
        const token = getJwtToken();
        fetch("/user/avatar", {
            method: "POST",
            body: formData,
            headers: { Authorization: `Bearer ${token}` },
        })
        .then(response => response.json())
        .then(data => {
            if (data.avatar_url) {
                document.getElementById("avatar").src = data.avatar_url;
                alert("Cập nhật avatar thành công!");
                document.getElementById("avatar-form").style.display = "none";
            } else {
                alert(data.error || "Có lỗi xảy ra!");
            }
        })
        .catch(err => console.error("Lỗi cập nhật avatar:", err));
    } else {
        alert("Vui lòng chọn một ảnh!");
    }
}


// Hiển thị form sửa thông tin người dùng khi nhấn vào nút "Sửa thông tin"

if (!window.editInfoBtn2Initialized) {
    window.editInfoBtn2Initialized = true;
    const editInfoBtn2 = document.getElementById("edit-info-btn");
    if (editInfoBtn2) {
    editInfoBtn2.addEventListener("click", function() {
        const editInfo = document.getElementById("edit-info");
        const changePasswordForm = document.getElementById("change-password-form");
        if(editInfo) editInfo.style.display = "block";
        if(changePasswordForm) changePasswordForm.style.display = "none";
    });
    }
}

// Hiển thị form thay đổi mật khẩu khi nhấn vào nút "Đổi mật khẩu"

if (!window.changePasswordBtnInitialized) {
    window.changePasswordBtnInitialized = true;
    const changePasswordBtn = document.getElementById("change-password-btn");
    if (changePasswordBtn) {
    changePasswordBtn.addEventListener("click", function() {
        const changePasswordForm = document.getElementById("change-password-form");
        const editInfo = document.getElementById("edit-info");
        if(changePasswordForm) changePasswordForm.style.display = "block";
        if(editInfo) editInfo.style.display = "none";
    });
    }
}

// Lưu thay đổi thông tin cá nhân (Tên người dùng và Email)

const saveInfoBtn = document.getElementById("save-info-btn");
if (saveInfoBtn) {
    saveInfoBtn.addEventListener("click", function() {
        const newUsername = document.getElementById("edit-username")?.value;
        const newEmail = document.getElementById("edit-email")?.value;
        if (newUsername && newEmail) {
            const token = getJwtToken(); // Lấy token
            fetch("/user/update_profile", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ username: newUsername, email: newEmail }),
            })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Có lỗi xảy ra khi cập nhật thông tin!");
                }
                return response.json();
            })
            .then((data) => {
                if (data.message) {
                    alert(data.message);
                    loadUserProfile(); // Cập nhật lại thông tin người dùng
                    document.getElementById("edit-info").style.display = "none"; // Ẩn form sửa thông tin
                } else {
                    alert("Có lỗi xảy ra!");
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert(err.message || "Có lỗi xảy ra, vui lòng thử lại!");
            });
    } else {
        alert("Vui lòng nhập đầy đủ thông tin!");

        }
    });
}


// Lưu thay đổi mật khẩu
const savePasswordBtn = document.getElementById("save-password-btn");
if (savePasswordBtn) {
    savePasswordBtn.addEventListener("click", function() {
        const newPassword = document.getElementById("new-password")?.value;
        const confirmPassword = document.getElementById("confirm-password")?.value;
        if (newPassword === confirmPassword) {
            const token = getJwtToken();
            fetch("/user/update_profile", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ password: newPassword }),
            })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Có lỗi xảy ra khi cập nhật mật khẩu!");
                }
                return response.json();
            })
            .then((data) => {
                if (data.message) {
                    alert(data.message);
                    const changePasswordForm = document.getElementById("change-password-form");
                    if(changePasswordForm) changePasswordForm.style.display = "none";
                } else {
                    alert("Có lỗi xảy ra!");
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert(err.message || "Có lỗi xảy ra, vui lòng thử lại!");
            });
        } else {
            alert("Mật khẩu không khớp!");
        }
    });
}

// Tải thông tin người dùng khi trang được tải
document.addEventListener("DOMContentLoaded", function() {
    if (typeof loadUserProfile === 'function') loadUserProfile();
    const uploadInput = document.getElementById('upload');
    if (uploadInput) {
        uploadInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file && file.size > 2 * 1024 * 1024) {
                alert("Dung lượng ảnh vượt quá 2MB!");
                event.target.value = ""; // Reset file
            }
        });
    }
    // Fallback: try to populate followed-artists sidebar using cookie-based auth
    try {
        const followedSection = document.getElementById('followed-artists-section');
        if (followedSection && window.loadFollowedArtistsSidebar) {
            // delay slightly to allow any cookie setting to finish
            setTimeout(() => {
                console.debug('[sidebar] attempting cookie-only load on DOMContentLoaded');
                try { window.loadFollowedArtistsSidebar(); } catch(e){ console.error('[sidebar] fallback call failed', e); }
            }, 200);
        }
    } catch(e) { console.error('Error attempting followed artists fallback:', e); }
});

// Toggle hiển thị form đổi mật khẩu
const changePasswordMenuItem = document.getElementById("changePasswordMenuItem");
if (changePasswordMenuItem) {
    changePasswordMenuItem.addEventListener("click", function() {
        const box = document.getElementById("changePasswordBox");
        if(box) box.style.display = box.style.display === "none" ? "block" : "none";
    });
}

const changePasswordForm = document.getElementById("changePasswordForm");
if (changePasswordForm) {
    changePasswordForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        const oldPassword = document.getElementById("oldPassword")?.value;
        const newPassword = document.getElementById("newPassword")?.value;
        const confirmPassword = document.getElementById("confirmPassword")?.value;
        const messageEl = document.getElementById("passwordMessage");
        if(messageEl) messageEl.style.color = "red";
        if (newPassword !== confirmPassword) {
            if(messageEl) messageEl.textContent = "Mật khẩu xác nhận không khớp!";
            return;
        }
        try {
            const response = await fetch("/change-password", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ oldPassword, newPassword }),
            });
            const data = await response.json();
            if (data.success) {
                if(messageEl) messageEl.style.color = "green";
                if(messageEl) messageEl.textContent = "Đổi mật khẩu thành công!";
            } else {
                if(messageEl) messageEl.textContent = data.message || "Lỗi đổi mật khẩu.";
            }
        } catch (error) {
            console.error("Error:", error);
            if(messageEl) messageEl.textContent = "Lỗi kết nối đến máy chủ.";
        }
    });
}

// small renderer helper so retry code can reuse
function renderFollowedArtistsList(list, data) {
    try {
        if (Array.isArray(data) && data.length > 0) {
            list.innerHTML = '';
            data.forEach(artist => {
                const li = document.createElement('li');
                li.style.marginBottom = '8px';
                
                // Fix image path
                let imgPath = artist.image_path || 'images/default_artist.jpg';
                if (!imgPath.startsWith('/static/')) {
                    imgPath = '/static/' + imgPath.replace(/^\/+/, '');
                }
                
                li.innerHTML = `
                    <a href="/artist/${artist.id}" style="display:flex;align-items:center;gap:12px;padding:10px;border-radius:8px;text-decoration:none;color:#fff;transition:background 0.2s;">
                        <img src="${imgPath}" alt="${artist.name}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;">
                        <div style="flex:1;">
                            <div style="font-size:15px;font-weight:500;">${artist.name}</div>
                            <div style="font-size:12px;color:#aaa;">Nghệ sĩ</div>
                        </div>
                    </a>
                `;
                list.appendChild(li);
            });
        } else {
            list.innerHTML = `
                <li style="color:#888;font-size:14px;text-align:center;padding:40px 20px;">
                    <i class="fas fa-user-slash" style="font-size:48px;margin-bottom:16px;opacity:0.3;display:block;"></i>
                    <p style="margin:0;">Chưa follow nghệ sĩ nào.</p>
                </li>
            `;
        }
    } catch(e) {
        console.error('[sidebar] render error', e);
        list.innerHTML = '<li style="color:#888;font-size:14px;text-align:center;padding:20px;">Lỗi tải danh sách.</li>';
    }
}

// If list still in loading state but user appears logged in (auth-required sections visible), trigger reload
function maybeForceReloadFollowed(){
    const list = document.getElementById('followed-artists-list');
    const loading = list && list.querySelector('[data-state="loading"]');
    const authVisible = document.querySelector('.auth-required') && Array.from(document.querySelectorAll('.auth-required')).some(el => el.style.display !== 'none');
    if (loading && authVisible) {
        console.debug('[followed-artists] force reload because still loading while auth visible');
        try { loadFollowedArtistsSidebar(getJwtToken() || ''); } catch(e){}
    }
}

try { window.maybeForceReloadFollowed = maybeForceReloadFollowed; } catch(e){}

})(); // End IIFE
} // End duplicate check
