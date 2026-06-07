// ========================
// HÀM TIỆN ÍCH PLAYER STATE
// ========================
function getPlayerState() {
    try {
        return JSON.parse(localStorage.getItem('player_state') || '{}');
    } catch (e) {
        return {};
    }

}

function savePlayerState(state) {
    try {
        localStorage.setItem('player_state', JSON.stringify(state));
    } catch (e) {}
}

function clearPlayerState() {
    try {
        localStorage.removeItem('player_state');
    } catch (e) {}
}

function formatTime(seconds) {
    seconds = Math.floor(seconds || 0);
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// File: static/js/app.js

// =================================================================
// PHẦN 1: LOGIC CHẠY TRÊN MỌI TRANG
// =================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. Ensure auth state is synchronized with server and update UI
    (async function(){
        try{
            const r = await fetchWithAuth('/auth/me');
            if (r && r.ok){
                const data = await r.json().catch(()=>null);
                if (data && data.username){
                    try{ localStorage.setItem('username', data.username); }catch(e){}
                    try{ if(data.role) localStorage.setItem('role', data.role); }catch(e){}
                    try{ if(data.id) localStorage.setItem('user_id', String(data.id)); }catch(e){}
                } else {
                    try{ localStorage.removeItem('username'); localStorage.removeItem('role'); localStorage.removeItem('user_id'); }catch(e){}
                }
            } else {
                try{ localStorage.removeItem('username'); localStorage.removeItem('role'); localStorage.removeItem('user_id'); }catch(e){}
            }
        }catch(e){ console.warn('Auth sync failed', e); }
        updateUserUIonPageLoad();
    })();

    // 2. Gắn sự kiện cho nút đăng xuất (nếu có)
    setupLogoutButton();

    // 3. Khởi tạo trình phát nhạc
    setupMusicPlayer();
    
    // 4. SPA navigation for Home links (logo, sidebar, nav)
    setupHomeNavigation();
    // 4b. SPA navigation for Admin Manage Users
    setupAdminManageUsersNavigation();
    
    // 5. Xác định trang hiện tại và tải dữ liệu tương ứng
    const currentPagePath = window.location.pathname;
    const entityId = document.getElementById('entity-id')?.value;
    const entityType = document.getElementById('entity-type')?.value;

    if (currentPagePath === '/') {
        loadHomePage();
    } else if (entityId && (['artist', 'genre', 'album','playlists'].includes(entityType))) {
        // supports artist/genre/album and playlists via same loader
        loadDetailPage(entityType, entityId);
    }
});

function setupHomeNavigation() {
    // Intercept clicks on all Home links (logo, sidebar menu, etc.)
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a[href="/"], a[href="' + window.location.origin + '/"]');
        if (link && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
            e.preventDefault();
            console.debug('[SPA] Home link clicked, loading via API');
            loadHomePage();
        }
    });
}

// Helper to always send credentials and add Authorization header from localStorage fallback
async function fetchWithAuth(url, opts = {}){
    opts = opts || {};
    opts.credentials = opts.credentials || 'include';
    opts.headers = opts.headers || {};
    if (!opts.headers['Content-Type'] && !opts.headers['content-type']) {
        // don't force JSON for GET with no body
    }
    // Attach fallback Authorization header if access_token present in localStorage
    try{
        const token = localStorage.getItem('access_token');
        if (token && !opts.headers['Authorization'] && !opts.headers['authorization']){
            opts.headers['Authorization'] = `Bearer ${token}`;
        }
    }catch(e){}
    return fetch(url, opts);
}

// =================================================================
// PHẦN 2: CÁC HÀM XỬ LÝ GIAO DIỆN VÀ DỮ LIỆU
// =================================================================

function updateUserUIonPageLoad() {
    const loggedOutView = document.getElementById("logged-out-view");
    const loggedInView = document.getElementById("logged-in-view");
    const profileUsername = document.getElementById("profile-username");
    const username = localStorage.getItem('username');

    if (username) {
        if (loggedOutView) loggedOutView.style.display = "none";
        if (loggedInView) loggedInView.style.display = "flex";
        if (profileUsername) profileUsername.textContent = username;
    } else {
        if (loggedOutView) loggedOutView.style.display = "flex";
        if (loggedInView) loggedInView.style.display = "none";
    }
}

function setupLogoutButton() {
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function(e) {
            e.preventDefault();
            // Clear client-side auth state (localStorage)
            try {
                localStorage.removeItem('username');
                localStorage.removeItem('access_token');
                localStorage.removeItem('role');
            } catch (err) {}
            // Tell server to unset JWT cookie; include credentials so cookie is sent
            fetch('/auth/logout', { method: 'POST', credentials: 'include' })
                .then(() => {
                    alert('Đăng xuất thành công!');
                    // Force reload without cache
                    window.location.href = '/';
                })
                .catch(() => {
                    // Fallback: still navigate away
                    window.location.href = '/';
                });
        });
    }
}

async function loadHomePage() {
    console.debug('[loadHomePage] Loading homepage content via API');
    const mainContent = document.getElementById('main-content');
    if (!mainContent) {
        console.warn('[loadHomePage] #main-content not found');
        return;
    }
    
    try {
        const res = await fetchWithAuth('/api/home');
        if (!res.ok) throw new Error('Failed to fetch homepage data');
        const data = await res.json();
        
        // Build homepage HTML (refactored layout: Genres grid, Artists tabs, Albums grid)
        let html = '<div class="container">';
        
        // Genres section
        html += '<div class="section-header"><h2>Thể loại</h2></div>';
        html += '<div class="genres-row" id="genres-container" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:24px;padding-bottom:12px;-webkit-overflow-scrolling:touch;">';
        if (data.genres && data.genres.length > 0) {
            data.genres.forEach(g => {
                const imgPath = g.image_path ? `/static/${g.image_path}` : '/static/images/default_genre.png';
                html += `
                    <a href="/genre/${g.id}" style="flex:0 0 auto; text-decoration:none; color:inherit;">
                        <div class="card ${g.color_class || 'default-color'}" style="width:180px; min-width:180px; margin:0 8px;">
                            <div class="title">${g.name}</div>
                            <img src="${imgPath}" alt="${g.name}">
                        </div>
                    </a>`;
            });
        } else {
            html += '<p>Chưa có thể loại nào.</p>';
        }
        html += '</div>';
        
        // Artists unified section with tabs
        html += '<div class="section-header" style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">';
        html += '<h2 style="margin:0;">Nghệ sĩ</h2>';
        if (data.trending_generated_at) {
            html += `<small id="artists-meta" style="color:#888;font-size:12px;">Cập nhật ${new Date(data.trending_generated_at).toLocaleString('vi-VN')}</small>`;
        }
        html += '</div>';
        html += '<div class="artist-tabs" style="display:flex;gap:18px;border-bottom:1px solid #222;margin:6px 0 18px 0;">';
        html += '<button class="artist-tab active" data-tab="all" style="background:none;border:none;border-bottom:2px solid #1db954;color:#fff;padding:8px 4px;font-weight:600;cursor:pointer;">Tất cả</button>';
        html += '<button class="artist-tab" data-tab="trending" style="background:none;border:none;border-bottom:2px solid transparent;color:#aaa;padding:8px 4px;font-weight:600;cursor:pointer;">Đang nổi</button>';
        html += '<button class="artist-tab" data-tab="recommended" style="background:none;border:none;border-bottom:2px solid transparent;color:#aaa;padding:8px 4px;font-weight:600;cursor:pointer;">Dành cho bạn</button>';
        html += '</div>';
        html += '<div id="artists-tab-content" style="min-height:190px;">';
        // All panel (horizontal scroll)
        html += '<div class="artists-panel" data-panel="all" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:18px;padding:6px 0 14px 0;-webkit-overflow-scrolling:touch;">';
        if (data.artists && data.artists.length > 0) {
            data.artists.forEach(a => {
                const img = a.image_path ? `/static/${a.image_path}` : '/static/images/default_artist.png';
                html += `<a href="/artist/${a.id}" style="flex:0 0 auto;text-decoration:none;color:inherit;">
                    <div class="artist-card" style="width:140px;min-width:140px;background:#181818;border-radius:16px;padding:14px 10px 12px 10px;display:flex;flex-direction:column;align-items:center;gap:10px;height:190px;box-shadow:0 2px 8px rgba(0,0,0,0.12);">
                        <img src="${img}" alt="${a.name}" style="width:90px;height:90px;object-fit:cover;border-radius:50%;">
                        <h3 style="font-size:15px;margin:0 0 4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;">${a.name}</h3>
                        <p style="font-size:11px;color:#aaa;margin:0;">Artist</p>
                    </div>
                </a>`;
            });
        } else {
            html += '<p style="color:#888;">Chưa có nghệ sĩ nào.</p>';
        }
        html += '</div>';
        // Trending panel
        html += '<div class="artists-panel" data-panel="trending" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:18px;padding:6px 0 14px 0;-webkit-overflow-scrolling:touch;">';
        if (Array.isArray(data.trending_artists) && data.trending_artists.length > 0) {
            data.trending_artists.forEach(a => {
                const img = a.image_path ? (a.image_path.startsWith('/static/') ? a.image_path : ('/static/' + a.image_path.replace(/^\/+/,''))) : '/static/images/default_artist.png';
                html += `<a href="/artist/${a.id}" style="flex:0 0 auto;text-decoration:none;color:inherit;">
                    <div class="artist-card" style="width:140px;min-width:140px;background:#181818;border-radius:16px;padding:14px 10px 12px 10px;display:flex;flex-direction:column;align-items:center;gap:8px;height:190px;box-shadow:0 2px 8px rgba(0,0,0,0.12);">
                        <img src="${img}" alt="${a.name}" style="width:90px;height:90px;object-fit:cover;border-radius:50%;">
                        <h3 style="font-size:15px;margin:0 0 2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;">${a.name}</h3>
                        <p style="font-size:11px;color:#1db954;margin:0;">🔥 ${a.score}</p>
                        ${a.smooth_score !== undefined ? `<p style='font-size:10px;color:#6ec1ff;margin:0;'>EMA ${a.smooth_score}</p>`:''}
                        ${a.growth_rate_pct !== undefined ? `<p style='font-size:10px;color:#ffae42;margin:0;'>↑ ${a.growth_rate_pct}%</p>`:''}
                    </div>
                </a>`;
            });
        } else {
            html += '<div style="color:#888;font-size:13px;padding:8px;">Đang tải dữ liệu...</div>';
        }
        html += '</div>';
        // Recommended panel (lazy load later)
        html += '<div class="artists-panel" data-panel="recommended" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:18px;padding:6px 0 14px 0;-webkit-overflow-scrolling:touch;">';
        html += '<div style="color:#888;font-size:13px;padding:8px;">Đang tải đề xuất...</div>';
        html += '</div>';
        html += '</div>'; // end tab content
        
        // (Removed separate trending section - merged inside tabs)

        // Albums section (horizontal scroll)
        html += '<section class="content-section" style="margin-top:34px;">';
        html += '<div class="section-header" style="margin-bottom:14px;"><h2 style="margin:0;">Album Nổi Bật</h2></div>';
        html += '<div class="albums-row" id="albums-row" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:20px;padding:6px 0 14px 0;-webkit-overflow-scrolling:touch;">';
        if (data.albums && data.albums.length > 0) {
            data.albums.forEach(al => {
                const imgPath = al.cover_image_path ? `/static/${al.cover_image_path}` : '/static/images/default_album.png';
                html += `<a href="/album/${al.id}" style="flex:0 0 auto;text-decoration:none;color:inherit;">
                    <div class="album-card" style="width:160px;min-width:160px;background:#181818;border-radius:16px;padding:14px;display:flex;flex-direction:column;align-items:center;gap:10px;height:220px;">
                        <img src="${imgPath}" alt="${al.title}" style="width:100%;height:120px;object-fit:cover;border-radius:12px;">
                        <h3 style="font-size:15px;margin:0 0 4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;">${al.title}</h3>
                        <p style="font-size:12px;color:#aaa;margin:0;">${al.artist_name || ''}</p>
                    </div>
                </a>`;
            });
        }
        html += '</div>';
        html += '</section>';
        
        // Public Playlists section - dynamically load from server
        html += '<section class="content-section" style="margin-top:40px;">';
        html += '<div class="section-header" style="margin-bottom:14px;"><h2 style="margin:0;">Playlist Công Khai</h2></div>';
        html += '<div id="public-playlists-container" style="display:flex;flex-wrap:nowrap;overflow-x:auto;gap:20px;padding:6px 0 14px 0;-webkit-overflow-scrolling:touch;">';
        html += '<div style="color:#888;font-size:13px;padding:8px;">Đang tải...</div>';
        html += '</div>';
        html += '</section>';
        
        html += '</div>';
        
        mainContent.innerHTML = html;
        // Tab switching logic (client-side replication of server script)
        try {
            const tabs = mainContent.querySelectorAll('.artist-tab');
            const panels = mainContent.querySelectorAll('.artists-panel');
            const setActive = (name) => {
                tabs.forEach(t => {
                    const active = t.dataset.tab === name;
                    t.classList.toggle('active', active);
                    t.style.color = active ? '#fff' : '#aaa';
                    t.style.borderBottom = active ? '2px solid #1db954' : 'none';
                });
                panels.forEach(p => {
                    p.style.display = p.dataset.panel === name ? 'flex' : 'none';
                });
            };
            tabs.forEach(t => t.addEventListener('click', () => {
                const name = t.dataset.tab;
                setActive(name);
                if (name === 'recommended') {
                    const panel = mainContent.querySelector('.artists-panel[data-panel="recommended"]');
                    if (panel && panel.getAttribute('data-loaded') !== 'yes') {
                        fetchWithAuth('/api/home').then(r => r.json()).then(d => {
                            if (Array.isArray(d.recommended_artists) && d.recommended_artists.length > 0) {
                                panel.innerHTML = d.recommended_artists.map(a => {
                                    const img = a.image_path ? `/static/${a.image_path}` : '/static/images/default_artist.png';
                                    return `<a href="/artist/${a.id}" style="flex:0 0 auto;text-decoration:none;color:inherit;">
                                        <div class="artist-card" style="width:140px;min-width:140px;background:#181818;border-radius:16px;padding:14px 10px 12px 10px;display:flex;flex-direction:column;align-items:center;gap:10px;height:190px;box-shadow:0 2px 8px rgba(0,0,0,0.12);">
                                            <img src="${img}" alt="${a.name}" style="width:90px;height:90px;object-fit:cover;border-radius:50%;">
                                            <h3 style="font-size:15px;margin:0 0 4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;text-align:center;">${a.name}</h3>
                                            <p style="font-size:11px;color:#aaa;margin:0;">Artist</p>
                                        </div>
                                    </a>`;
                                }).join('');
                            } else {
                                panel.innerHTML = '<div style="color:#888;font-size:13px;padding:8px;">Chưa có dữ liệu đề xuất.</div>';
                            }
                            panel.setAttribute('data-loaded', 'yes');
                        }).catch(() => {
                            panel.innerHTML = '<div style="color:#d55;font-size:13px;padding:8px;">Lỗi tải đề xuất.</div>';
                            panel.setAttribute('data-loaded', 'yes');
                        });
                    }
                }
            }));
            setActive('all');
        } catch (e) { console.warn('Tab init failed', e); }
        
        // Load public playlists
        try {
            const publicPlaylistsContainer = mainContent.querySelector('#public-playlists-container');
            if (publicPlaylistsContainer) {
                fetchWithAuth('/api/playlists/public').then(r => r.json()).then(playlists => {
                    if (Array.isArray(playlists) && playlists.length > 0) {
                        publicPlaylistsContainer.innerHTML = playlists.map(p => {
                            const imgPath = p.image_path ? `/static/${p.image_path}` : '/static/images/playlist_image.png';
                            return `<a href="/playlist/${p.id}" style="flex:0 0 auto;text-decoration:none;color:inherit;">
                                <div class="playlist-card" style="width:160px;min-width:160px;background:#181818;border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:10px;height:240px;transition:background 0.3s;" onmouseover="this.style.background='#282828'" onmouseout="this.style.background='#181818'">
                                    <img src="${imgPath}" alt="${p.name}" style="width:100%;height:120px;object-fit:cover;border-radius:12px;">
                                    <h3 style="font-size:15px;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;width:100%;">${p.name}</h3>
                                    <p style="font-size:12px;color:#aaa;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.username || 'Người dùng'}</p>
                                    <p style="font-size:11px;color:#888;margin:0;">${p.song_count || 0} bài hát</p>
                                </div>
                            </a>`;
                        }).join('');
                    } else {
                        publicPlaylistsContainer.innerHTML = '<div style="color:#888;font-size:13px;padding:8px;">Chưa có playlist công khai nào.</div>';
                    }
                }).catch(() => {
                    publicPlaylistsContainer.innerHTML = '<div style="color:#888;font-size:13px;padding:8px;">Chưa có playlist công khai nào.</div>';
                });
            }
        } catch (e) { console.warn('Public playlists load failed', e); }
        
        // Enforce horizontal scroll styles if any other script/CSS tries to override
        // Removed horizontal scroll enforcement (using grids now)
        
        // Update page state
        try {
            window.history.pushState({ page: 'home' }, 'Trang chủ - Melune', '/');
        } catch (e) {
            console.debug('pushState failed', e);
        }
        
        console.debug('[loadHomePage] Homepage content loaded successfully (refactored)');
    } catch (e) {
        console.error('[loadHomePage] Error loading homepage:', e);
        if (mainContent) {
            mainContent.innerHTML = '<div class="container"><p>Không thể tải trang chủ. Vui lòng thử lại.</p></div>';
        }
    }
}

// ========================
// SPA: Load Manage Users Page
// ========================
function setupAdminManageUsersNavigation(){
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a#admin-manage-users-link, a[href="/admin/users"]');
        if (link && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
            e.preventDefault();
            console.debug('[SPA] Manage Users link intercepted');
            loadManageUsersPage();
        }
    });
    // Handle direct load if current path is /admin/users (always fetch to fill data)
    if (window.location.pathname === '/admin/users') {
        loadManageUsersPage();
    }
}

async function loadManageUsersPage(){
    const mainContent = document.getElementById('main-content');
    if(!mainContent){ console.warn('[loadManageUsersPage] #main-content not found'); return; }
    // Skeleton HTML
    let html = `
    <div class="manage-users-container">
      <div class="manage-users-header"><h2>Quản Lý Người Dùng</h2></div>
      <div class="search-users-bar" style="margin-bottom:18px;display:flex;gap:12px;align-items:center;">
        <input type="text" id="search-username-input" placeholder="Tìm theo username..." style="padding:6px 12px;width:240px;border-radius:6px;border:1px solid #444;background:#222;color:#eee;">
        <button id="refresh-users-btn" style="padding:6px 14px;border-radius:6px;border:1px solid #333;background:#1db954;color:#fff;cursor:pointer;">Làm mới</button>
      </div>
      <div class="users-table-wrapper">
        <table id="users-table" style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#222;">
              <th style="padding:8px 10px;border:1px solid #333;">STT</th>
              <th style="padding:8px 10px;border:1px solid #333;">Username</th>
              <th style="padding:8px 10px;border:1px solid #333;">Email</th>
              <th style="padding:8px 10px;border:1px solid #333;">Role</th>
              <th style="padding:8px 10px;border:1px solid #333;">Actions</th>
            </tr>
          </thead>
          <tbody id="users-table-body">
            <tr><td colspan="5" style="text-align:center;padding:16px;" class="loading-message">Đang tải dữ liệu...</td></tr>
          </tbody>
        </table>
      </div>
      <p id="manage-users-message" style="margin-top:12px;font-size:14px;color:#ccc;"></p>
    </div>`;
    mainContent.innerHTML = html;
    try {
        const res = await fetchWithAuth('/admin/api/users');
        if(!res.ok){ throw new Error('Fetch users failed '+res.status); }
        const users = await res.json();
        renderUsersTable(users);
        try { window.history.pushState({page:'admin-users'}, 'Quản Lý Người Dùng', '/admin/users'); }catch(e){ console.debug('pushState failed', e); }
    } catch(err){
        console.error('[loadManageUsersPage] error', err);
        const body = document.getElementById('users-table-body');
        if(body){ body.innerHTML = `<tr><td colspan="5" style="color:#ff6b6b;padding:16px;text-align:center;">Lỗi tải dữ liệu: ${err.message}</td></tr>`; }
    }
    attachManageUsersEvents();
    // Inform legacy scripts listening for SPA navigation
    try { window.dispatchEvent(new CustomEvent('spa-navigated', {detail:{page:'admin-users'}})); } catch(e) {}
}

function renderUsersTable(users){
    const body = document.getElementById('users-table-body');
    if(!body) return;
    if(!Array.isArray(users) || users.length===0){
        body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:16px;color:#888;">Không có người dùng.</td></tr>';
        return;
    }
    let rows = '';
    users.forEach((u,i)=>{
        const roleSel = `<select data-user-id="${u.id}" class="role-select" style="background:#222;color:#eee;border:1px solid #444;border-radius:4px;padding:4px 6px;">
            <option value="user" ${u.role==='user'?'selected':''}>user</option>
            <option value="uploader" ${u.role==='uploader'?'selected':''}>uploader</option>
            <option value="admin" ${u.role==='admin'?'selected':''}>admin</option>
        </select>`;
        rows += `<tr>
            <td style="border:1px solid #333;padding:6px 8px;text-align:center;">${i+1}</td>
            <td style="border:1px solid #333;padding:6px 8px;">${u.username}</td>
            <td style="border:1px solid #333;padding:6px 8px;">${u.email}</td>
            <td style="border:1px solid #333;padding:6px 8px;">${roleSel}</td>
            <td style="border:1px solid #333;padding:6px 8px;text-align:center;">
                <button class="save-role-btn" data-user-id="${u.id}" style="background:#1db954;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;">Lưu</button>
            </td>
        </tr>`;
    });
    body.innerHTML = rows;
}

function attachManageUsersEvents(){
    const refreshBtn = document.getElementById('refresh-users-btn');
    if(refreshBtn){ refreshBtn.addEventListener('click', loadManageUsersPage); }
    document.getElementById('users-table-body')?.addEventListener('click', async (e)=>{
        const btn = e.target.closest('.save-role-btn');
        if(!btn) return;
        const userId = btn.getAttribute('data-user-id');
        const select = document.querySelector(`select.role-select[data-user-id="${userId}"]`);
        const newRole = select ? select.value : null;
        if(!newRole){ return; }
        btn.disabled = true; btn.textContent = 'Đang lưu...';
        try {
            const res = await fetchWithAuth(`/admin/api/users/${userId}/role`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: newRole })
            });
            const msgEl = document.getElementById('manage-users-message');
            if(res.ok){
                msgEl && (msgEl.textContent = 'Cập nhật role thành công');
            } else {
                const txt = await res.text();
                msgEl && (msgEl.textContent = 'Lỗi: '+txt);
            }
        } catch(err){
            const msgEl = document.getElementById('manage-users-message');
            msgEl && (msgEl.textContent = 'Lỗi kết nối: '+ err.message);
        } finally {
            btn.disabled = false; btn.textContent = 'Lưu';
        }
    });
    // Live search
    const searchInput = document.getElementById('search-username-input');
    if(searchInput){
        searchInput.addEventListener('input', ()=>{
            const q = searchInput.value.trim().toLowerCase();
            document.querySelectorAll('#users-table-body tr').forEach(tr=>{
                const userCell = tr.children[1];
                if(!userCell) return;
                const name = userCell.textContent.trim().toLowerCase();
                tr.style.display = (!q || name.includes(q)) ? '' : 'none';
            });
        });
    }
}

async function loadDetailPage(type, id) {
    const entityImage = document.getElementById('entity-image');
    const entityName = document.getElementById('entity-name');
    const songListBody = document.getElementById('song-list-body');
    console.debug('[loadDetailPage] start', {type, id});
    // If server already rendered song rows on initial full page load (F5),
    // avoid fetching and overwriting them. Just attach events and return.
    try {
        if (songListBody && songListBody.querySelectorAll && songListBody.querySelectorAll('tr.song-row').length > 0) {
            console.debug('[loadDetailPage] detected server-rendered rows - skipping fetch');
            try { attachSongRowEvents(); } catch (e) { console.warn('attachSongRowEvents failed', e); }
            return;
        }
    } catch (e) { /* ignore and continue to fetch */ }
    try {
    const res = await fetchWithAuth(`/api/${type}/${id}`);
        let data;
        try {
            data = await res.json();
        } catch (e) {
            console.error('[loadDetailPage] invalid JSON response', e);
            throw e;
        }
        console.debug('[loadDetailPage] api response', {status: res.status, ok: res.ok, data});
        if (!res.ok) throw new Error(data.msg || `Fetch lỗi ${res.status}`);
        // Hiển thị tên (fallback nếu trống)
        if (entityName) {
            // Album có thể trả về data.name hoặc data.title
            let displayName = '';
            if (data.name && data.name.trim()) {
                displayName = data.name;
            } else if (data.title && data.title.trim()) {
                displayName = data.title;
            } else {
                displayName = 'Không có tên';
            }
            entityName.textContent = displayName;
        }

        // Xử lý đường dẫn ảnh linh hoạt
        if (entityImage) {
            const rawPath = data.image_path || '';
            let finalSrc = '';
            // Chỉ nối đúng 1 lần /static/ nếu chưa có
            if (rawPath.startsWith('/static/')) {
                finalSrc = rawPath;
            } else if (rawPath.startsWith('static/')) {
                finalSrc = '/' + rawPath;
            } else if (rawPath.startsWith('/')) {
                finalSrc = '/static' + rawPath;
            } else if (rawPath.length > 0) {
                finalSrc = '/static/' + rawPath;
            } else {
                finalSrc = '/static/images/default.jpg';
            }
            // Loại bỏ static/static nếu có lỗi dữ liệu
            finalSrc = finalSrc.replace(/\/static\/static\//g, '/static/');
            entityImage.src = finalSrc;
            entityImage.alt = data.name || 'Ảnh';
        }
        let html = '';
        // Support both array and object API responses
        const songArray = Array.isArray(data) ? data : data.songs;
        if (Array.isArray(songArray) && songArray.length) {
            songArray.forEach((item, idx) => {
                // BXH API: item may have .song and .total_plays at top level
                const song = item.song || item;
                const songImage = song.image_path 
                    ? (song.image_path.startsWith('/static/') ? song.image_path : `/static/${song.image_path}`)
                    : (song.album_image_path || '/static/images/default.jpg');

                // BXH: use item.total_plays if present, else fallback to song.listen_count
                let listenCount = (typeof item.total_plays === 'number') ? item.total_plays : (song.listen_count ?? 0);

                html += `
                <tr class="song-row" data-song-id="${song.id}" data-mp3-path="/static/${song.mp3_path}" data-title="${song.title}" data-artist-name="${song.artist_name}" data-artist-id="${song.artist_id ?? ''}" data-album-id="${song.album_id ?? ''}" data-album-image="${songImage}">
                    <td>${idx + 1}</td>
                    <td>
                        <div class="song-title">
                            <i class="fa-solid fa-play play-icon"></i>
                            <a href="/song/${song.id}" class="song-title-link" onclick="event.stopPropagation();" style="color:#fff;text-decoration:none;margin-left:8px;">${song.title}</a>
                        </div>
                    </td>
                    <td>
                        ${song.artist_id ? `<a href=\"/artist/${song.artist_id}\" class=\"artist-link\" onclick=\"event.stopPropagation();\">${song.artist_name}</a>` : song.artist_name}
                    </td>
                    <td class="listen-count" style="text-align:center;vertical-align:middle;padding:0;">
                        <span style="display:inline-block;min-width:32px;">${listenCount}</span>
                    </td>
                    <td class="like-cell" style="text-align:center;vertical-align:middle;padding:0;">
                        <button class="like-button" onclick="toggleLike(${song.id}, this); event.stopPropagation();" title="Thích" style="background:transparent;border:none;min-width:32px;">
                            <i class="fa-regular fa-heart like-icon"></i>
                            <span class="like-count">0</span>
                        </button>
                    </td>
                </tr>`;
            });
        } else {
            html = '<tr><td colspan="5">Chưa có bài hát nào.</td></tr>';
        }
    if (songListBody) songListBody.innerHTML = html;
        // Gắn lại event delegation sau khi render bảng
        attachSongRowEvents();

        // Load like status for all songs
        if (Array.isArray(data.songs) && data.songs.length) {
            data.songs.forEach(song => {
                const row = document.querySelector(`tr[data-song-id="${song.id}"]`);
                if (row) {
                    loadLikeStatus(song.id, row);
                }
            });
        }
    } catch (e) {
        console.error('[loadDetailPage] Lỗi tải chi tiết', type, e);
        if (entityName) entityName.textContent = 'Không thể tải dữ liệu.';
        if (songListBody) songListBody.innerHTML = '<tr><td colspan="5">Lỗi tải bài hát (xem console)</td></tr>';
        try { attachSongRowEvents(); } catch (err) { console.warn('attachSongRowEvents failed', err); }
    }
}

// =================================================================
// PHẦN 3: LOGIC CỦA TRÌNH PHÁT NHẠC
// =================================================================

// Flag để đảm bảo setupMusicPlayer chỉ chạy 1 lần
if (typeof window.musicPlayerInitialized === 'undefined') {
    window.musicPlayerInitialized = false;
}
// Giữ ngữ cảnh playlist hiện tại (container và khóa) để tránh chuyển ngược về danh sách cũ
if (typeof window.playlistContextKey === 'undefined') {
    window.playlistContextKey = null;
}
if (typeof window.lastPlayedSongElement === 'undefined') {
    window.lastPlayedSongElement = null;
}

function attachSongRowEvents() {
    // Attach to all song list containers, not just #song-list-body
    const containers = document.querySelectorAll('#song-list-body, tbody, .songs-table-wrapper, .song-table tbody');
    
    containers.forEach(container => {
        if (container && !container._songRowEventAttached) {
            container.addEventListener('click', (event) => {
                const songRow = event.target.closest('.song-row');
                if (!songRow) return;
                // Prevent playing when clicking on links or buttons
                if (event.target.closest('.artist-link, .album-link')) return;
                if (event.target.closest('.like-button, .like-icon')) return;
                if (event.target.closest('.song-title-link')) return;
                playSelectedSong(songRow);
            });
            container._songRowEventAttached = true;
        }
    });
}

// Expose to window scope for use in other templates
window.attachSongRowEvents = attachSongRowEvents;

function setupMusicPlayer() {
    if (window.musicPlayerInitialized) {
        console.log('[DEBUG] Music player already initialized, skipping...');
        return;
    }
    
    console.log('[DEBUG] Initializing music player...');
    window.musicPlayerInitialized = true;
    
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const currentSongTitle = document.getElementById('current-song-title');
    const currentArtistName = document.getElementById('current-artist-name');
    const currentSongImage = document.getElementById('current-song-image');
    const progressBar = document.getElementById('progress-bar');
    const currentTimeEl = document.getElementById('current-time');
    const durationTimeEl = document.getElementById('duration-time');
    const volumeSlider = document.getElementById('volume-slider');
    const volumeBtn = document.getElementById('volume-btn');
    const mainContent = document.getElementById('main-content');

    // Playlist state for auto-advance / shuffle
    let playlist = [];
    let currentIndex = -1; // index in playlist of currently playing song
    let shuffle = false; // if true, pick random next
    // Minimal ad placeholders (no-op) so removed ad code doesn't break runtime
    let autoPlayCount = 0;
    let adShownThisSession = false;
    function resetAdSession(){ autoPlayCount = 0; adShownThisSession = false; }
    async function showRandomAd(){ /* no-op during debugging */ }

    // Optional shuffle UI button (if present in template)
    const shuffleBtn = document.getElementById('shuffle-btn');
    if (shuffleBtn) {
        // initialize UI state
        shuffle = localStorage.getItem('player_shuffle') === '1';
        shuffleBtn.classList.toggle('active', shuffle);
        shuffleBtn.addEventListener('click', () => {
            shuffle = !shuffle;
            localStorage.setItem('player_shuffle', shuffle ? '1' : '0');
            shuffleBtn.classList.toggle('active', shuffle);
            // Mutual exclusivity: turning shuffle ON disables repeat-one
            if (shuffle && typeof repeatMode !== 'undefined' && repeatMode === 1) {
                repeatMode = 0;
                localStorage.setItem('player_repeat', repeatMode);
                updateRepeatBtnUI();
            }
        });
    }

    // Repeat button logic: off (0) or repeat one (1). Highlight when active.
    const repeatBtn = document.getElementById('repeat-btn');
    let repeatMode = parseInt(localStorage.getItem('player_repeat') || '0', 10);
    function updateRepeatBtnUI() {
        if (!repeatBtn) return;
        const icon = repeatBtn.querySelector('i');
        repeatBtn.classList.toggle('repeat-active', repeatMode === 1);
        if (icon) {
            // Keep base icon class; just toggle helper and color via CSS class
            icon.classList.add('fa-repeat');
        }
        repeatBtn.title = repeatMode === 1 ? 'Lặp: Một bài' : 'Lặp: Tắt';
    }
    // Enforce mutual exclusivity on initial load (if both were somehow saved as active)
    function enforceRepeatShuffleExclusivity() {
        if (repeatMode === 1 && shuffle) {
            // Disable shuffle to prioritize repeat-one per requirement
            shuffle = false;
            localStorage.setItem('player_shuffle', '0');
            if (shuffleBtn) shuffleBtn.classList.remove('active');
        }
    }
    enforceRepeatShuffleExclusivity();
    updateRepeatBtnUI();
    if (repeatBtn) {
        repeatBtn.addEventListener('click', () => {
            repeatMode = (repeatMode + 1) % 2;
            localStorage.setItem('player_repeat', repeatMode);
            updateRepeatBtnUI();
            // Mutual exclusivity: enabling repeat-one disables shuffle
            if (repeatMode === 1 && shuffle) {
                shuffle = false;
                localStorage.setItem('player_shuffle', '0');
                if (shuffleBtn) shuffleBtn.classList.remove('active');
            }
        });
    }

    // Nếu không có audio element (ví dụ trang admin), thoát an toàn
    if (!audioPlayer) return;

    // Kiểm tra xem trang có được reload thật sự không (F5, Ctrl+F5)
    // Sử dụng Navigation Timing API v2
    const isPageReload = (function() {
        const navEntries = performance.getEntriesByType('navigation');
        if (navEntries && navEntries.length > 0) {
            return navEntries[0].type === 'reload';
        }
        // Fallback cho trình duyệt cũ
        return performance.navigation && performance.navigation.type === 1;
    })();
    
    // Nếu là reload thật sự, xóa trạng thái player
    if (isPageReload) {
        clearPlayerState();
        console.log('[Player] Page reloaded - player state cleared');
    }

    // Khôi phục trạng thái phát nhạc từ localStorage (chỉ khi không reload)
    const savedState = !isPageReload ? getPlayerState() : null;
    if (savedState && savedState.mp3) {
        audioPlayer.src = savedState.mp3;
        if (currentSongTitle) currentSongTitle.textContent = savedState.title || 'Không có bài hát';
        if (currentArtistName) currentArtistName.textContent = savedState.artist || '';
        if (currentSongImage) {
            currentSongImage.src = savedState.image || '/static/images/default_album.png';
            currentSongImage.alt = savedState.title || 'Album art';
        }
        if (savedState.songId) {
            window.currentSongId = savedState.songId;
            // Restore any existing play session persisted by player.js
            try {
                const ps = sessionStorage.getItem('currentPlaySession');
                if (ps) {
                    window.currentPlaySession = ps;
                    // If this playSession has already been logged earlier in sessionStorage,
                    // we should not reset the threshold flag or allow another log.
                    try {
                        const logged = JSON.parse(sessionStorage.getItem('loggedPlaySessions') || '[]');
                        if (Array.isArray(logged) && logged.indexOf(ps) !== -1) {
                            window.thresholdLogged = true;
                        } else {
                            window.thresholdLogged = false;
                        }
                    } catch (e) {
                        window.thresholdLogged = false;
                    }
                } else {
                    window.thresholdLogged = false;
                }
            } catch (e) {
                window.thresholdLogged = false;
            }
        }
        
        // Đợi audio load xong rồi mới seek và play
        audioPlayer.addEventListener('loadedmetadata', function restorePlayback() {
            // Cập nhật duration time
            if (durationTimeEl && audioPlayer.duration) {
                durationTimeEl.textContent = formatTime(audioPlayer.duration);
            }
            
            if (savedState.currentTime && savedState.currentTime > 0) {
                audioPlayer.currentTime = savedState.currentTime;
            }
            if (savedState.isPlaying) {
                audioPlayer.play().catch(err => console.warn('Auto-play blocked:', err));
            }
            // Remove listener sau khi đã restore
            audioPlayer.removeEventListener('loadedmetadata', restorePlayback);
        }, { once: true });
        
        audioPlayer.load();
    }
    // Gắn event delegation lần đầu khi player khởi tạo
    attachSongRowEvents();
    
    // Try to restore saved playlist on page load
    buildPlaylist(null);

    // Xử lý nút Play/Pause
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', () => {
            console.log('[DEBUG] Play/Pause button clicked');
            try {
                if (audioPlayer.src && audioPlayer.paused) {
                    console.log('[DEBUG] Playing audio...');
                    audioPlayer.play();
                } else {
                    console.log('[DEBUG] Pausing audio...');
                    audioPlayer.pause();
                }
            } catch (e) {
                console.error('Player error when toggling play/pause:', e);
            }
        });
        console.log('[DEBUG] Play/Pause button event listener attached');
    } else {
        console.error('[ERROR] Play/Pause button not found!');
    }

    // Cập nhật icon khi trạng thái phát thay đổi (guard các phần tử)
    audioPlayer.addEventListener('play', () => {
        if (playPauseBtn && playPauseBtn.querySelector('i')) {
            playPauseBtn.querySelector('i').classList.remove('fa-play');
            playPauseBtn.querySelector('i').classList.add('fa-pause');
        }
        // Cập nhật isPlaying trong localStorage
        const state = getPlayerState();
        if (state) {
            state.isPlaying = true;
            savePlayerState(state);
        }
    });
    audioPlayer.addEventListener('pause', () => {
        if (playPauseBtn && playPauseBtn.querySelector('i')) {
            playPauseBtn.querySelector('i').classList.remove('fa-pause');
            playPauseBtn.querySelector('i').classList.add('fa-play');
        }
        // Cập nhật isPlaying trong localStorage
        const state = getPlayerState();
        if (state) {
            state.isPlaying = false;
            savePlayerState(state);
        }
    });

    // Cập nhật progress bar khi audio phát
    if (progressBar) {
        audioPlayer.addEventListener('timeupdate', () => {
            if (audioPlayer.duration && !isNaN(audioPlayer.duration)) {
                const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
                progressBar.value = percent;
                
                // Cập nhật thời gian hiển thị
                if (currentTimeEl) {
                    currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
                }
                if (durationTimeEl && audioPlayer.duration) {
                    durationTimeEl.textContent = formatTime(audioPlayer.duration);
                }
                
                // Cập nhật currentTime vào localStorage mỗi 2 giây
                if (Math.floor(audioPlayer.currentTime) % 2 === 0) {
                    const state = getPlayerState();
                    if (state) {
                        state.currentTime = audioPlayer.currentTime;
                        state.isPlaying = !audioPlayer.paused;
                        savePlayerState(state);
                    }
                }
            }
        });

        // Seek khi user thay đổi progress
        let isSeeking = false;
        progressBar.addEventListener('input', (e) => {
            isSeeking = true;
            if (audioPlayer.duration && !isNaN(audioPlayer.duration)) {
                const newTime = (e.target.value / 100) * audioPlayer.duration;
                audioPlayer.currentTime = newTime;
            }
        });
        progressBar.addEventListener('change', () => { isSeeking = false; });
    }

    // Volume control
    if (volumeSlider && audioPlayer) {
        // Load saved volume or default to 70%
        const savedVolume = localStorage.getItem('player_volume');
        const initialVolume = savedVolume ? parseFloat(savedVolume) : 0.7;
        audioPlayer.volume = initialVolume;
        volumeSlider.value = initialVolume * 100;
        
        // Update volume icon based on level
        function updateVolumeIcon(volume) {
            if (!volumeBtn) return;
            const icon = volumeBtn.querySelector('i');
            if (!icon) return;
            
            icon.classList.remove('fa-volume-up', 'fa-volume-down', 'fa-volume-off', 'fa-volume-mute');
            if (volume === 0) {
                icon.classList.add('fa-volume-mute');
            } else if (volume < 0.5) {
                icon.classList.add('fa-volume-down');
            } else {
                icon.classList.add('fa-volume-up');
            }
        }
        
        updateVolumeIcon(initialVolume);
        
        // Handle volume slider change
        volumeSlider.addEventListener('input', (e) => {
            const volume = e.target.value / 100;
            audioPlayer.volume = volume;
            localStorage.setItem('player_volume', volume);
            updateVolumeIcon(volume);
        });
        
        // Toggle mute on volume button click
        if (volumeBtn) {
            let lastVolume = initialVolume;
            volumeBtn.addEventListener('click', () => {
                if (audioPlayer.volume > 0) {
                    lastVolume = audioPlayer.volume;
                    audioPlayer.volume = 0;
                    volumeSlider.value = 0;
                    updateVolumeIcon(0);
                    localStorage.setItem('player_volume', 0);
                } else {
                    audioPlayer.volume = lastVolume || 0.7;
                    volumeSlider.value = (lastVolume || 0.7) * 100;
                    updateVolumeIcon(lastVolume || 0.7);
                    localStorage.setItem('player_volume', lastVolume || 0.7);
                }
            });
        }
    }

    // Error handler cho audio
    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        // bạn có thể hiển thị thông báo UI ở đây
    });

    // Build a playlist array from existing .song-row elements
    // Simple cache để lưu trạng thái preload của ảnh
    window.imageCache = window.imageCache || {};
    function normalizeImagePath(p) {
        if (!p) return '/static/images/default.jpg';
        // Loại bỏ domain nếu có (trường hợp API trả full URL)
        try {
            if (p.startsWith('http://') || p.startsWith('https://')) {
                const u = new URL(p);
                p = u.pathname; // chỉ lấy path
            }
        } catch(e) { /* ignore malformed */ }
        // Chuẩn hoá các legacy prefix '/DoAnCoSo/' -> '/static/'
        p = p.replace(/^\/DoAnCoSo\//, '/static/');
        // Nếu chưa có '/static/' và không bắt đầu bằng '/', cố gắng thêm
        if (!p.startsWith('/static/') && !p.startsWith('/')) {
            // Nhiều DB có thể lưu 'images/albums/xyz.jpg'
            if (p.startsWith('images/')) {
                p = '/static/' + p;
            } else if (p.startsWith('albums/') || p.startsWith('songs/') || p.startsWith('artists/')) {
                p = '/static/images/' + p;
            } else {
                p = '/static/' + p;
            }
        }
        // Nếu path là '/albums/xyz.jpg' thì thêm tiền tố '/static/images/'
        if (p.startsWith('/albums/')) {
            p = '/static/images' + p;
        }
        if (p.startsWith('/songs/')) {
            p = '/static/images' + p;
        }
        if (p.startsWith('/artists/')) {
            p = '/static/images' + p;
        }
        // Đảm bảo không bị '/static//images'
        p = p.replace(/\/static\/\/+/g,'/static/');
        // Tránh đúp '/static/static/'
        p = p.replace(/\/static\/static\//g,'/static/');
        return p;
    }
    function preloadPlaylistImages() {
        if (!playlist) return;
        // Ensure imageCache exists
        if (!window.imageCache) {
            window.imageCache = {};
        }
        playlist.forEach(p => {
            const url = p.image;
            if (!url) return;
            if (window.imageCache[url]) return; // đã preload
            const img = new Image();
            window.imageCache[url] = { img, loaded: false };
            img.onload = () => { window.imageCache[url].loaded = true; };
            img.onerror = () => { window.imageCache[url].error = true; };
            img.src = url;
        });
    }
    function findPlaylistContainer(el) {
        if (!el) return document;
        return el.closest('#song-list-body, tbody, .songs-table-wrapper, .playlist-container, .playlist-table') || document;
    }
    function computeContextKey(container) {
        if (!container || container === document) return 'GLOBAL';
        if (typeof container.getAttribute !== 'function') return 'GLOBAL';
        let key = container.getAttribute('data-playlist-context');
        if (!key) {
            key = (container.id ? ('#'+container.id) : '') + '|' + (location.pathname) + '|' + container.className;
        }
        return key;
    }
    function buildPlaylist(fromElement) {
        // First check if there's a saved playlist from navigation
        try {
            const savedPlaylistData = sessionStorage.getItem('saved_playlist');
            if (savedPlaylistData) {
                const parsed = JSON.parse(savedPlaylistData);
                if (parsed.playlist && Array.isArray(parsed.playlist)) {
                    playlist = parsed.playlist.map(item => ({
                        element: null,
                        mp3: item.mp3,
                        title: item.title,
                        artist: item.artist,
                        image: normalizeImagePath(item.image),
                        songId: item.songId,
                        isAutoplay: item.isAutoplay
                    }));
                    currentIndex = parsed.currentIndex || 0;
                    window.playlistContextKey = parsed.contextKey || 'RESTORED';
                    preloadPlaylistImages();
                    window.autoplayFetched = false;
                    
                    // Clear saved playlist after restoring
                    sessionStorage.removeItem('saved_playlist');
                    console.log('[Playlist] Restored saved playlist with', playlist.length, 'songs');
                    return;
                }
            }
        } catch(e) {
            console.warn('Failed to restore saved playlist:', e);
        }
        
        // Normal playlist building from DOM elements
        const container = findPlaylistContainer(fromElement);
        const rows = Array.from(container.querySelectorAll('.song-row'));
        
        // Only build playlist if we have song rows
        if (rows.length === 0) {
            console.log('[Playlist] No song rows found, skipping playlist build');
            return;
        }
        
        window.playlistContextKey = computeContextKey(container);
        playlist = rows.map((row) => ({
            element: row,
            mp3: row.dataset.mp3Path,
            title: row.dataset.title,
            artist: row.dataset.artistName,
            image: normalizeImagePath(row.dataset.albumImage),
            songId: row.dataset.songId
        }));
        preloadPlaylistImages();
        // Reset autoplay flag when building new playlist
        window.autoplayFetched = false;
    }
    
    // Expose buildPlaylist to window for external access
    window.buildPlaylist = buildPlaylist;

    // Play by index in playlist
    function playByIndex(index) {
    if (!playlist || playlist.length === 0) return;
        if (index < 0 || index >= playlist.length) return;
        const item = playlist[index];
        if (!item || !item.mp3) return;

        currentIndex = index;
    window.lastPlayedSongElement = item.element || window.lastPlayedSongElement;
        audioPlayer.src = item.mp3;
        if (currentSongTitle) currentSongTitle.textContent = item.title || '';
        if (currentArtistName) currentArtistName.textContent = item.artist || '';
        // Cập nhật ảnh bìa
        if (currentSongImage) {
            const imagePath = normalizeImagePath(item.image || item.element?.dataset?.albumImage);
            currentSongImage.alt = item.title || 'Album art';
            // Thêm class loading để tránh cảm giác giật/flicker
            currentSongImage.classList.add('loading');
            currentSongImage.dataset.pendingSrc = imagePath;
            
            // Ensure imageCache exists
            if (!window.imageCache) {
                window.imageCache = {};
            }
            
            const cacheEntry = window.imageCache[imagePath];
            if (cacheEntry && cacheEntry.loaded) {
                currentSongImage.src = cacheEntry.img.src;
                currentSongImage.classList.remove('loading');
            } else {
                // Nếu chưa có cache, tạo preload
                if (!cacheEntry) {
                    const img = new Image();
                    img.src = imagePath;
                    window.imageCache[imagePath] = { img, loaded: img.complete };
                    if (!img.complete) {
                        img.onload = () => {
                            window.imageCache[imagePath].loaded = true;
                            if (currentSongImage.dataset.pendingSrc === imagePath) {
                                currentSongImage.src = window.imageCache[imagePath].img.src;
                                currentSongImage.classList.remove('loading');
                            }
                        };
                        img.onerror = () => { window.imageCache[imagePath].error = true; if (currentSongImage.dataset.pendingSrc === imagePath){ currentSongImage.src = '/static/images/default.jpg'; currentSongImage.classList.remove('loading'); } };
                    }
                }
                // Đặt src ngay để bắt đầu tải (trường hợp preload chưa xong)
                currentSongImage.src = imagePath;
                // Nếu ảnh load nhanh (cache của trình duyệt), remove loading sớm
                if (currentSongImage.complete) {
                    currentSongImage.classList.remove('loading');
                } else {
                    currentSongImage.onload = () => currentSongImage.classList.remove('loading');
                    currentSongImage.onerror = () => { currentSongImage.src = '/static/images/default.jpg'; currentSongImage.classList.remove('loading'); };
                }
            }
        }
    // Nếu user chọn bài hát thủ công, reset ad session
    resetAdSession();

    // Lấy song_id từ element để log lịch sử
    const songId = item.element ? item.element.dataset.songId : null;
        if (songId && window.currentSongId !== songId) {
            window.currentSongId = songId;
            // Create a play session id and persist so player.js dedupe logic sees it
            try{
                const ps = String(songId) + ':' + String(Date.now());
                sessionStorage.setItem('currentPlaySession', ps);
                try{ window.currentPlaySession = ps; }catch(e){}
            }catch(e){}
            window.thresholdLogged = false;
            console.log('[DEBUG] Playing song ID:', songId, 'playSession:', window.currentPlaySession);
        }
        
        // Get context type and ID from current page
        let contextType = '';
        let contextId = null;
        const entityIdEl = document.getElementById('entity-id');
        const entityTypeEl = document.getElementById('entity-type');
        if (entityIdEl && entityTypeEl) {
            const type = entityTypeEl.value;
            if (type === 'playlists') contextType = 'playlist';
            else if (type === 'album') contextType = 'album';
            else if (type === 'genre') contextType = 'genre';
            else if (type === 'artist') contextType = 'artist';
            contextId = parseInt(entityIdEl.value);
        }
        
        // Lưu trạng thái phát nhạc vào localStorage
        savePlayerState({
            mp3: item.mp3,
            title: item.title,
            artist: item.artist,
            image: item.image || item.element?.dataset?.albumImage,
            songId: songId,
            currentTime: 0,
            isPlaying: true,
            contextType: contextType,
            contextId: contextId,
            currentIndex: currentIndex
        });
        
        audioPlayer.load();
        const p = audioPlayer.play();
        if (p !== undefined) p.catch((err) => console.warn('Play rejected:', err));
    }

    // Expose jump function for queue modal
    window.jumpToPlaylistIndex = function(newIndex) {
        if (playlist && newIndex >= 0 && newIndex < playlist.length) {
            playByIndex(newIndex);
        }
    };
    
    // Expose function to get current playlist for queue modal
    window.getCurrentPlaylist = function() {
        return {
            playlist: playlist,
            currentIndex: currentIndex,
            shuffle: shuffle,
            repeatMode: repeatMode
        };
    };
    
    // Expose function to create a single-song playlist (for song detail page)
    window.createSingleSongPlaylist = function(songData) {
        // Create a virtual playlist with just this one song
        playlist = [{
            element: null,  // No DOM element in this case
            mp3: songData.mp3,
            title: songData.title,
            artist: songData.artist,
            image: normalizeImagePath(songData.image),
            songId: songData.songId
        }];
        currentIndex = 0;
        window.playlistContextKey = 'SINGLE_SONG|' + songData.songId;
        window.autoplayFetched = false;
        
        // Preload the image
        preloadPlaylistImages();
        
        console.log('[Playlist] Created single-song playlist:', songData.title);
    };

    // Advance to next song (sequential or random if shuffle)
    async function advanceToNext() {
        if (!playlist || playlist.length === 0) return;
        
        // Check if autoplay is enabled and near end of playlist (5 songs or less remaining)
        const autoplayEnabled = localStorage.getItem('player_autoplay') !== '0';
        const remaining = playlist.length - currentIndex - 1;
        if (autoplayEnabled && remaining <= 5 && !window.autoplayFetched) {
            window.autoplayFetched = true;
            console.log('[Autoplay] Fetching suggestions, remaining:', remaining);
            await fetchAndAppendAutoplay();
        }
        
        const next = currentIndex + 1;
        
        if (shuffle) {
            if (playlist.length === 1) {
                playByIndex(0);
                return;
            }
            let nextIdx = Math.floor(Math.random() * playlist.length);
            // avoid immediate repeat when possible
            if (playlist.length > 1) {
                let tries = 0;
                while (nextIdx === currentIndex && tries < 10) {
                    nextIdx = Math.floor(Math.random() * playlist.length);
                    tries++;
                }
            }
            playByIndex(nextIdx);
        } else {
            if (next < playlist.length) {
                // Still have songs in queue
                playByIndex(next);
            } else {
                // Reached end - loop back to start
                console.log('[Autoplay] Reached end of playlist, looping back');
                playByIndex(0);
            }
        }
        // Ad logic: count auto-play, show ad after 3-4 consecutive auto-plays, only once per session
        if (!adShownThisSession) {
            autoPlayCount++;
            if (autoPlayCount === 3 || autoPlayCount === 4) {
                adShownThisSession = true;
                showRandomAd();
            }
        }
    }
    
    // Fetch autoplay suggestions and append to playlist
    async function fetchAndAppendAutoplay() {
        try {
            // Check if autoplay is enabled
            const autoplayEnabled = localStorage.getItem('player_autoplay') !== '0';
            if (!autoplayEnabled) {
                console.log('[Autoplay] Skip - autoplay is disabled');
                return;
            }
            
            const state = getPlayerState();
            const contextType = state.contextType || '';
            const contextId = state.contextId;
            
            console.log('[Autoplay] Fetching with context:', contextType, contextId);
            
            // Only fetch autoplay for genre, artist, album
            if (!['genre', 'artist', 'album'].includes(contextType) || !contextId) {
                console.log('[Autoplay] Skip - invalid context type or missing ID');
                return;
            }
            
            // Get exclude IDs from current playlist
            const excludeIds = playlist.map(item => item.songId).filter(id => id);
            
            const params = new URLSearchParams();
            if (state.currentSongId) params.append('current_song_id', state.currentSongId);
            if (contextType) params.append('context_type', contextType);
            if (contextId) params.append('context_id', contextId);
            params.append('current_index', currentIndex);
            params.append('total_in_context', playlist.length);
            
            console.log('[Autoplay] API call:', `/api/queue?${params.toString()}`);
            const response = await fetchWithAuth(`/api/queue?${params.toString()}`);
            if (!response.ok) {
                console.error('[Autoplay] API error:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('[Autoplay] API response:', data);
            
            if (data.autoplay_songs && data.autoplay_songs.length > 0) {
                // Append autoplay songs to playlist
                data.autoplay_songs.forEach(song => {
                    playlist.push({
                        mp3: `/static/${song.mp3_path}`,
                        title: song.title,
                        artist: song.artist_name,
                        image: normalizeImagePath(song.image_path),
                        songId: song.id,
                        isAutoplay: true
                    });
                });
                console.log(`[Autoplay] Added ${data.autoplay_songs.length} songs to queue, new total: ${playlist.length}`);
            }
        } catch (error) {
            console.error('[Autoplay] Failed to fetch suggestions:', error);
        }
    }
    
    // Expose fetchAndAppendAutoplay for queue modal
    window.fetchAndAppendAutoplay = fetchAndAppendAutoplay;

    // When a song ends: nếu repeat one thì phát lại, nếu không thì tự động chuyển bài tiếp theo
    audioPlayer.addEventListener('ended', () => {
        try {
            if (!playlist || playlist.length === 0) buildPlaylist();
            // Không có playlist thực sự thì thoát an toàn
            if (!playlist || playlist.length === 0) return;
            if (repeatMode === 1) {
                playByIndex(currentIndex);
            } else {
                advanceToNext();
            }
        } catch (e) {
            console.error('Error advancing to next song:', e);
        }
    });

    // Update duration when metadata is loaded
    audioPlayer.addEventListener('loadedmetadata', () => {
        if (durationTimeEl && audioPlayer.duration && !isNaN(audioPlayer.duration)) {
            durationTimeEl.textContent = formatTime(audioPlayer.duration);
        }
    });

    // Prev / Next buttons (wire to playlist functions)
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) {
        prevBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!playlist || playlist.length === 0) buildPlaylist();
            if (!playlist || playlist.length === 0) return;
            if (shuffle) {
                // when shuffle is on, just pick a random
                let prev = Math.floor(Math.random() * playlist.length);
                let tries = 0;
                while (prev === currentIndex && tries < 10) { prev = Math.floor(Math.random() * playlist.length); tries++; }
                playByIndex(prev);
            } else {
                // previous with wrap-around
                const prevIndex = (currentIndex - 1 + playlist.length) % playlist.length;
                playByIndex(prevIndex);
            }
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!playlist || playlist.length === 0) buildPlaylist();
            advanceToNext();
        });
    }

    // Hàm phát bài hát được chọn
    window.playSelectedSong = function playSelectedSong(songElement) {
        const mp3Path = songElement.dataset.mp3Path;
        const title = songElement.dataset.title;
        const artistName = songElement.dataset.artistName;
        const songId = songElement.dataset.songId;

        if (!mp3Path) {
            console.warn('Không tìm thấy đường dẫn mp3 cho bài hát này');
            return;
        }
        const container = findPlaylistContainer(songElement);
        const songContextKey = computeContextKey(container);
        // Nếu playlist chưa có hoặc khác ngữ cảnh, rebuild theo container của bài hát
        if (!playlist || playlist.length === 0 || window.playlistContextKey !== songContextKey) {
            buildPlaylist(songElement);
        }
        // Tìm index theo element (ưu tiên) hoặc mp3
        const idx = playlist.findIndex((p) => p.element === songElement || (p.mp3 && p.mp3 === mp3Path));
        if (idx === -1) {
            // if not found, add it to playlist end and play it
            playlist.push({ element: songElement, mp3: mp3Path, title, artist: artistName, songId });
            try{
                const ps = String(songId) + ':' + String(Date.now());
                sessionStorage.setItem('currentPlaySession', ps);
                try{ window.currentPlaySession = ps; }catch(e){}
            }catch(e){}
            playByIndex(playlist.length - 1);
        } else {
            try{
                const ps = String(songId) + ':' + String(Date.now());
                sessionStorage.setItem('currentPlaySession', ps);
                try{ window.currentPlaySession = ps; }catch(e){}
            }catch(e){}
            playByIndex(idx);
        }
    }
}

// File: static/js/app.js

// Hàm khởi tạo trang
function initializePage() {
    const entityId = document.getElementById('entity-id')?.value;
    const entityType = document.getElementById('entity-type')?.value;

    if (window.location.pathname === '/') {
        // Trang chủ
    } else if (entityId && (entityType === 'artist' || entityType === 'genre' || entityType === 'album')) {
        loadDetailPage(entityType, entityId);
    }
}

// ================= FOLLOW ARTIST (AJAX, NO F5) =================
function setupFollowArtistDynamic() {
    const followBtn = document.getElementById('follow-btn');
    const followerCountSpan = document.getElementById('follower-count');
    const artistId = document.getElementById('entity-id')?.value;
    if (!followBtn || !followerCountSpan || !artistId) return;

    function getAccessToken() {
        let token = localStorage.getItem('access_token');
        if (!token) {
            const tokenCookie = document.cookie.split('; ').find(r => r.startsWith('access_token='));
            if (tokenCookie) token = tokenCookie.split('=')[1];
        }
        return token;
    }

    function updateFollowInfo() {
        fetch(`/api/artist/${artistId}/follow-info`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : Promise.reject())
            .then(data => {
                followerCountSpan.textContent = `${data.follower_count} follower${data.follower_count !== 1 ? 's' : ''}`;
                followBtn.textContent = data.is_following ? 'Unfollow' : 'Follow';
                followBtn.classList.toggle('following', data.is_following);
            })
            .catch(() => {
                followerCountSpan.textContent = 'Lỗi follow';
            });
    }

    if (!followBtn._boundFollow) {
        followBtn.addEventListener('click', () => {
            if (followBtn.disabled) return;
            const token = getAccessToken();
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['Authorization'] = 'Bearer ' + token;
            followBtn.disabled = true;
            followBtn.style.opacity = 0.6;
            fetch(`/api/artist/${artistId}/follow`, { method: 'POST', headers, credentials: 'include' })
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(() => {
                    updateFollowInfo();
                    // Cập nhật sidebar danh sách nghệ sĩ đã follow nếu hàm tồn tại
                    try { if (window.loadFollowedArtistsSidebar) window.loadFollowedArtistsSidebar(getAccessToken()); } catch(e) {}
                })
                .catch(() => alert('Có lỗi khi follow/unfollow'))
                .finally(() => { followBtn.disabled = false; followBtn.style.opacity = 1; });
        });
        followBtn._boundFollow = true;
    }
    updateFollowInfo();
}

// Gọi khi trang tải lần đầu và sau mỗi SPA navigation
document.addEventListener('DOMContentLoaded', setupFollowArtistDynamic);
window.addEventListener('spa-navigated', setupFollowArtistDynamic);

// Listen for SPA navigation events
window.addEventListener('spa-navigated', () => {
    console.log('[SPA] Page navigated, re-initializing...');
    // Reset playlist context khi chuyển trang để tránh giữ danh sách cũ
    try { playlist = []; window.playlistContextKey = null; currentIndex = -1; } catch(e) {}
    initializePage();
    
    // Re-initialize artist tabs on main page after SPA navigation
    if (typeof initArtistTabs === 'function') {
        console.log('[SPA] Re-initializing artist tabs...');
        setTimeout(() => initArtistTabs(), 100); // Small delay to ensure DOM is ready
    }
});

// ========================
// QUEUE MODAL (Danh sách chờ)
// ========================
(function setupQueueModal() {
    const queueBtn = document.getElementById('queue-btn');
    const queueModal = document.getElementById('queue-modal');
    const closeQueueBtn = document.getElementById('close-queue-btn');
    
    if (!queueBtn || !queueModal || !closeQueueBtn) return;
    
    // Open queue modal
    queueBtn.addEventListener('click', async () => {
        queueModal.style.display = 'flex';
        await loadQueueData();
    });
    
    // Close queue modal
    closeQueueBtn.addEventListener('click', () => {
        queueModal.style.display = 'none';
    });
    
    // Close on backdrop click
    queueModal.addEventListener('click', (e) => {
        if (e.target === queueModal) {
            queueModal.style.display = 'none';
        }
    });
    
    async function loadQueueData() {
        const nowPlayingContainer = document.getElementById('now-playing-track');
        const nextTracksList = document.getElementById('next-tracks-list');
        
        if (!nowPlayingContainer || !nextTracksList) return;
        
        try {
            // Try to get queue from current playlist in memory first
            if (typeof window.getCurrentPlaylist === 'function') {
                const queueData = window.getCurrentPlaylist();
                if (queueData && queueData.playlist && queueData.playlist.length > 0) {
                    // Render now playing from current playlist
                    const currentIdx = queueData.currentIndex || 0;
                    const currentTrack = queueData.playlist[currentIdx];
                    
                    if (currentTrack) {
                        const imgSrc = currentTrack.image && currentTrack.image !== '/static/images/default.jpg' 
                            ? (currentTrack.image.startsWith('/') ? currentTrack.image : `/static/${currentTrack.image}`) 
                            : '/static/images/default.jpg';
                        nowPlayingContainer.innerHTML = `
                            <div class="queue-track now-playing">
                                <img class="queue-track-image" src="${imgSrc}" alt="${currentTrack.title}">
                                <div class="queue-track-info">
                                    <div class="queue-track-title">${escapeHtml(currentTrack.title)}</div>
                                    <div class="queue-track-artist">${escapeHtml(currentTrack.artist)}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        nowPlayingContainer.innerHTML = '<div class="queue-track-empty"><p>Chưa có bài hát nào</p></div>';
                    }
                    
                    // Render next tracks - separate regular and autoplay
                    const nextTracks = queueData.playlist.slice(currentIdx + 1);
                    const regularTracks = nextTracks.filter(t => !t.isAutoplay).slice(0, 20);
                    const autoplayTracks = nextTracks.filter(t => t.isAutoplay).slice(0, 15);
                    
                    // If autoplay enabled, near end, and no autoplay yet, trigger fetch
                    const autoplayEnabled = localStorage.getItem('player_autoplay') !== '0';
                    const remaining = queueData.playlist.length - currentIdx - 1;
                    if (autoplayEnabled && remaining <= 5 && autoplayTracks.length === 0 && !window.autoplayFetching) {
                        window.autoplayFetching = true;
                        fetchAndAppendAutoplay().then(() => {
                            window.autoplayFetching = false;
                            // Reload queue data after fetch
                            setTimeout(() => loadQueueData(), 500);
                        }).catch(() => {
                            window.autoplayFetching = false;
                        });
                    }
                    
                    let html = '';
                    
                    if (regularTracks.length > 0) {
                        html += regularTracks.map((track, idx) => {
                            const imgSrc = track.image && track.image !== '/static/images/default.jpg' 
                                ? (track.image.startsWith('/') ? track.image : `/static/${track.image}`) 
                                : '/static/images/default.jpg';
                            return `
                            <div class="queue-track" data-queue-index="${currentIdx + idx + 1}">
                                <img class="queue-track-image" src="${imgSrc}" alt="${track.title}">
                                <div class="queue-track-info">
                                    <div class="queue-track-title">${escapeHtml(track.title)}</div>
                                    <div class="queue-track-artist">${escapeHtml(track.artist)}</div>
                                </div>
                            </div>
                        `}).join('');
                    }
                    
                    // Always show autoplay divider with toggle button
                    const autoplayStartIndex = currentIdx + regularTracks.length + 1;
                    // Reuse autoplayEnabled variable declared above
                    html += `<div class="queue-autoplay-divider">
                        <span>Bài hát gợi ý (Tự động phát)</span>
                        <button class="autoplay-toggle-btn ${autoplayEnabled ? 'active' : ''}" title="${autoplayEnabled ? 'Tắt tự động phát' : 'Bật tự động phát'}">
                            <i class="fa ${autoplayEnabled ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                        </button>
                    </div>`;
                    
                    // Show autoplay tracks if available
                    if (autoplayTracks.length > 0) {
                        html += autoplayTracks.map((track, idx) => {
                            const imgSrc = track.image && track.image !== '/static/images/default.jpg' 
                                ? (track.image.startsWith('/') ? track.image : `/static/${track.image}`) 
                                : '/static/images/default.jpg';
                            return `
                            <div class="queue-track queue-track-autoplay" data-queue-index="${autoplayStartIndex + idx}">
                                <img class="queue-track-image" src="${imgSrc}" alt="${track.title}">
                                <div class="queue-track-info">
                                    <div class="queue-track-title">${escapeHtml(track.title)}</div>
                                    <div class="queue-track-artist">${escapeHtml(track.artist)}</div>
                                </div>
                            </div>
                        `}).join('');
                    } else if (autoplayEnabled) {
                        // Show message if autoplay enabled but no tracks yet
                        html += `<p class="queue-empty-message" style="text-align: center; padding: 12px; color: #888; font-size: 0.9rem;">Sẽ tự động thêm khi gần hết danh sách</p>`;
                    } else {
                        // Show message if autoplay disabled
                        html += `<p class="queue-empty-message" style="text-align: center; padding: 12px; color: #888; font-size: 0.9rem;">Tự động phát đang tắt</p>`;
                    }
                    
                    if (html) {
                        nextTracksList.innerHTML = html;
                        
                        // Add click handlers to jump to track
                        nextTracksList.querySelectorAll('.queue-track').forEach(trackEl => {
                            trackEl.addEventListener('click', async () => {
                                const queueIndex = parseInt(trackEl.dataset.queueIndex);
                                if (!isNaN(queueIndex)) {
                                    const queueData = window.getCurrentPlaylist();
                                    const targetSong = queueData.playlist[queueIndex];
                                    
                                    // If on song detail page and target has songId, navigate to new page
                                    if (window.location.pathname.startsWith('/song/') && targetSong && targetSong.songId) {
                                        // Save the target song's full state before navigation
                                        const targetState = {
                                            mp3: targetSong.mp3,
                                            title: targetSong.title,
                                            artist: targetSong.artist,
                                            image: targetSong.image,
                                            songId: targetSong.songId,
                                            currentTime: 0,
                                            isPlaying: true,
                                            contextType: getPlayerState().contextType || '',
                                            contextId: getPlayerState().contextId || null,
                                            currentIndex: queueIndex
                                        };
                                        localStorage.setItem('player_state', JSON.stringify(targetState));
                                        
                                        // Save entire playlist to preserve queue across navigation
                                        try {
                                            const playlistToSave = queueData.playlist.map(item => ({
                                                mp3: item.mp3,
                                                title: item.title,
                                                artist: item.artist,
                                                image: item.image,
                                                songId: item.songId,
                                                isAutoplay: item.isAutoplay
                                            }));
                                            sessionStorage.setItem('saved_playlist', JSON.stringify({
                                                playlist: playlistToSave,
                                                currentIndex: queueIndex,
                                                contextKey: window.playlistContextKey
                                            }));
                                        } catch(e) {
                                            console.warn('Failed to save playlist:', e);
                                        }
                                        
                                        // Update session tracking
                                        try {
                                            window.currentSongId = targetSong.songId;
                                            const playSession = String(targetSong.songId) + ':' + String(Date.now());
                                            sessionStorage.setItem('currentPlaySession', playSession);
                                            window.currentPlaySession = playSession;
                                            window.thresholdLogged = false;
                                        } catch(e) {}
                                        
                                        // Close modal and navigate
                                        queueModal.style.display = 'none';
                                        window.location.href = `/song/${targetSong.songId}`;
                                    } else {
                                        // Not on song detail page - just jump and refresh
                                        jumpToQueueIndex(queueIndex);
                                        await new Promise(resolve => setTimeout(resolve, 300));
                                        await loadQueueData();
                                    }
                                }
                            });
                        });
                        
                        // Add click handler for autoplay toggle button
                        const autoplayToggleBtn = nextTracksList.querySelector('.autoplay-toggle-btn');
                        if (autoplayToggleBtn) {
                            autoplayToggleBtn.addEventListener('click', async (e) => {
                                e.stopPropagation();
                                const currentState = localStorage.getItem('player_autoplay') !== '0';
                                const newState = !currentState;
                                localStorage.setItem('player_autoplay', newState ? '1' : '0');
                                
                                console.log('[Autoplay] Toggle:', newState ? 'ON' : 'OFF');
                                
                                // If disabled, reset autoplay flag
                                if (!newState) {
                                    window.autoplayFetched = false;
                                }
                                
                                // Refresh queue to update UI
                                await loadQueueData();
                            });
                        }
                    } else {
                        nextTracksList.innerHTML = '<p class="queue-empty-message">Không có bài hát tiếp theo</p>';
                    }
                    return;
                }
            }
            
            // Fallback to API if no playlist in memory
            const state = getPlayerState();
            const currentSongId = state.currentSongId;
            const contextType = state.contextType || '';
            const contextId = state.contextId;
            const currentIndex = state.currentIndex || 0;
            
            const params = new URLSearchParams();
            if (currentSongId) params.append('current_song_id', currentSongId);
            if (contextType) params.append('context_type', contextType);
            if (contextId) params.append('context_id', contextId);
            params.append('current_index', currentIndex);
            
            const response = await fetchWithAuth(`/api/queue?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch queue');
            
            const data = await response.json();
            
            // Render now playing
            if (data.now_playing) {
                const track = data.now_playing;
                nowPlayingContainer.innerHTML = `
                    <div class="queue-track now-playing">
                        <img class="queue-track-image" src="${track.image_path || '/static/images/default.jpg'}" alt="${track.title}">
                        <div class="queue-track-info">
                            <div class="queue-track-title">${escapeHtml(track.title)}</div>
                            <div class="queue-track-artist">${escapeHtml(track.artist_name)}</div>
                        </div>
                        <div class="queue-track-duration">${formatTime(track.duration)}</div>
                    </div>
                `;
            } else {
                nowPlayingContainer.innerHTML = '<div class="queue-track-empty"><p>Chưa có bài hát nào</p></div>';
            }
            
            // Render next tracks
            if (data.next_in_queue && data.next_in_queue.length > 0) {
                nextTracksList.innerHTML = data.next_in_queue.map((track, idx) => `
                    <div class="queue-track" data-song-id="${track.id}" data-queue-index="${currentIndex + idx + 1}">
                        <img class="queue-track-image" src="${track.image_path || '/static/images/default.jpg'}" alt="${track.title}">
                        <div class="queue-track-info">
                            <div class="queue-track-title">${escapeHtml(track.title)}</div>
                            <div class="queue-track-artist">${escapeHtml(track.artist_name)}</div>
                        </div>
                        <div class="queue-track-duration">${formatTime(track.duration)}</div>
                    </div>
                `).join('');
                
                // Add click handlers to jump to track
                nextTracksList.querySelectorAll('.queue-track').forEach(trackEl => {
                    trackEl.addEventListener('click', async () => {
                        const queueIndex = parseInt(trackEl.dataset.queueIndex);
                        const songId = trackEl.dataset.songId;
                        
                        if (!isNaN(queueIndex)) {
                            // If on song detail page, save state and navigate
                            if (window.location.pathname.startsWith('/song/') && songId) {
                                // Get the target song data from API response
                                const trackEl_data = data.next_in_queue[queueIndex - currentIndex - 1];
                                if (trackEl_data) {
                                    // Save full player state before navigation
                                    const targetState = {
                                        mp3: `/static/${trackEl_data.mp3_path}`,
                                        title: trackEl_data.title,
                                        artist: trackEl_data.artist_name,
                                        image: trackEl_data.image_path,
                                        songId: trackEl_data.id,
                                        currentTime: 0,
                                        isPlaying: true,
                                        contextType: contextType,
                                        contextId: contextId,
                                        currentIndex: queueIndex
                                    };
                                    localStorage.setItem('player_state', JSON.stringify(targetState));
                                    
                                    // Update session tracking
                                    try {
                                        window.currentSongId = trackEl_data.id;
                                        const playSession = String(trackEl_data.id) + ':' + String(Date.now());
                                        sessionStorage.setItem('currentPlaySession', playSession);
                                        window.currentPlaySession = playSession;
                                        window.thresholdLogged = false;
                                    } catch(e) {}
                                }
                                
                                // Close modal and navigate
                                queueModal.style.display = 'none';
                                window.location.href = `/song/${songId}`;
                            } else {
                                // Not on song detail page - just jump and refresh
                                jumpToQueueIndex(queueIndex);
                                await new Promise(resolve => setTimeout(resolve, 300));
                                await loadQueueData();
                            }
                        }
                    });
                });
            } else {
                nextTracksList.innerHTML = '<p class="queue-empty-message">Không có bài hát tiếp theo</p>';
            }
        } catch (error) {
            console.error('Error loading queue:', error);
            nowPlayingContainer.innerHTML = '<div class="queue-track-empty"><p>Lỗi khi tải danh sách chờ</p></div>';
            nextTracksList.innerHTML = '<p class="queue-empty-message">Lỗi khi tải danh sách chờ</p>';
        }
    }
    
    function jumpToQueueIndex(newIndex) {
        // Access playlist and currentIndex from setupMusicPlayer scope
        if (typeof window.jumpToPlaylistIndex === 'function') {
            window.jumpToPlaylistIndex(newIndex);
        } else {
            console.warn('Jump to queue index not available');
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();

// Hàm loadDetailPage của bạn đã đủ thông minh để xử lý "album" mà không cần sửa đổi.
// async function loadDetailPage(type, id) { ... }

// Hàm kiểm tra trạng thái like và cập nhật UI cho từng bài hát
async function loadLikeStatus(songId, row) {
    try {
        const res = await fetch(`/api/song/${songId}/like-status`, { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        const likeBtn = row.querySelector('.like-button');
        const likeIcon = row.querySelector('.like-icon');
        if (likeBtn && likeIcon) {
            if (data.liked) {
                likeIcon.classList.remove('fa-regular');
                likeIcon.classList.add('fa-solid');
                likeIcon.style.color = '#ff3b3b';
            } else {
                likeIcon.classList.remove('fa-solid');
                likeIcon.classList.add('fa-regular');
                likeIcon.style.color = '';
            }
            // Cập nhật số lượt thích nếu có
            if (typeof data.like_count === 'number') {
                const likeCount = row.querySelector('.like-count');
                if (likeCount) likeCount.textContent = data.like_count;
            }
        }
    } catch (e) {
        // ignore
    }
}

// Expose loadLikeStatus to window
window.loadLikeStatus = loadLikeStatus;
