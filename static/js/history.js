// history.js - always loads listening history when /history page is shown
// Fix: previous version triggered MANY concurrent fetches (DOMContentLoaded, popstate,
// spa-navigated, mutation observer, link click) causing flicker Đang tải ⇄ Lỗi kết nối.
// We debounce + guard in-flight fetches and handle 401 (unauthorized) gracefully.

let __historyFetchInProgress = false;
let __historyLoadedOnce = false;
let __historyLastRequestTs = 0;
const HISTORY_MIN_INTERVAL_MS = 1500; // throttle repeated automatic reloads

function headers(){
    const h={'Content-Type':'application/json'};
    const tokenLocal = localStorage.getItem('access_token');
    const tokenCookie = document.cookie.split('; ').find(r=>r.startsWith('access_token='));
    const token = tokenLocal || (tokenCookie ? tokenCookie.split('=')[1] : null);
    if(token) h['Authorization'] = 'Bearer ' + token;
    return h;
}

function loadHistory(force=false){
    const bodyEl = document.getElementById('history-body');
    const statusEl = document.getElementById('history-status');
    if (!bodyEl || !statusEl) return;
    const now = Date.now();
    if(!force){
        if(__historyFetchInProgress) return; // already fetching
        if(__historyLoadedOnce && (now - __historyLastRequestTs) < HISTORY_MIN_INTERVAL_MS) return; // throttle
    }
    __historyFetchInProgress = true;
    __historyLastRequestTs = now;
    statusEl.textContent='Đang tải...';
    fetch('/api/listening_history', {
        credentials:'include', 
        headers: headers()
    })
    .then(r=>{
        return r.json().then(j=>({ok:r.ok, status:r.status, data:j}));
    })
    .then(obj=>{
        if(!obj.ok){
            if(obj.status === 401){
                statusEl.textContent = 'Bạn cần đăng nhập để xem lịch sử nghe';
                bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Chưa đăng nhập</td></tr>';
                __historyLoadedOnce = true; // stop further auto retries until user action
                return;
            }
            const errorMsg = (obj.data && (obj.data.msg||obj.data.error)) || 'Không tải được lịch sử.';
            statusEl.textContent = errorMsg + ' (sẽ không tự tải lại)';
            bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Lỗi tải dữ liệu</td></tr>';
            __historyLoadedOnce = true; // avoid flicker loop
            return;
        }
        const arr = Array.isArray(obj.data) ? obj.data : [];
        if(arr.length === 0){
            bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Chưa có lịch sử nghe</td></tr>';
            statusEl.textContent = '';
            return;
        }
        bodyEl.innerHTML = '';
        arr.forEach((item, idx)=>{
            const tr=document.createElement('tr');
            tr.className='song-row';
            tr.setAttribute('data-song-id', item.song_id || '');
            tr.setAttribute('data-mp3-path', item.mp3_path ? `/static/${item.mp3_path}` : '');
            tr.setAttribute('data-title', item.title || '');
            tr.setAttribute('data-artist-name', item.artist_name || '');
            tr.setAttribute('data-album-image', item.album_image_path || '/static/images/default.jpg');
            let dt='';
            if(item.listened_at){ 
                try{ dt=new Date(item.listened_at).toLocaleString('vi-VN'); }catch(e){} 
            }
            tr.innerHTML = `
                <td>${idx+1}</td>
                <td>
                    <div class="song-info">
                        <i class="fas fa-play-circle play-icon"></i>
                        <a href="/song/${item.song_id}" onclick="event.stopPropagation()" class="song-title-link" style="color:#fff;text-decoration:none;margin-left:8px;">${item.title||''}</a>
                    </div>
                </td>
                <td>${item.artist_name||''}</td>
                <td style="font-size:12px;color:#aaa;">${dt}</td>
            `;
            bodyEl.appendChild(tr);
        });
        statusEl.textContent = arr.length + ' lượt nghe.';
        __historyLoadedOnce = true;
    })
    .catch(err=>{ 
        statusEl.textContent='Lỗi kết nối: ' + err.message + ' (dừng tự tải)';
        bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Lỗi tải dữ liệu</td></tr>';
        __historyLoadedOnce = true;
    })
    .finally(()=>{
        __historyFetchInProgress = false;
    });
}

// Tự động gọi lại khi vào đúng trang /history (SPA hoặc reload)
function ensureHistoryLoaded(force=false){
    if (document.getElementById('history-body')) {
        loadHistory(force);
    }
}

document.addEventListener('DOMContentLoaded', ensureHistoryLoaded);
window.addEventListener('popstate', ensureHistoryLoaded);
// Lắng nghe cả sự kiện SPA custom (spa-navigated)
window.addEventListener('spa-navigated', ensureHistoryLoaded);

// Nếu user truy cập trực tiếp /history (nhập URL, open tab mới) nhưng table chưa kịp render ngay, dùng MutationObserver
(function attachHistoryObserver(){
    try {
        if (window.__historyObserverAttached) return; // tránh gắn nhiều lần
        const observer = new MutationObserver(() => {
            if (__historyLoadedOnce) return; // stop observing once loaded
            if (document.getElementById('history-body')) ensureHistoryLoaded();
        });
        observer.observe(document.body, { childList: true, subtree: true });
        window.__historyObserverAttached = true;
    } catch(e) { console.debug('[history] observer error', e); }
})();

// Gắn global để các script khác có thể ép reload nếu cần
try { window.ensureHistoryLoaded = ensureHistoryLoaded; } catch(e){}

// Also trigger load when the user clicks a link to /history (covers SPA click navigation)
document.addEventListener('click', function (e) {
    try {
        const a = e.target.closest && e.target.closest('a');
        if (!a) return;
        // Use anchor pathname to match /history (works for relative and absolute links)
        const hrefPath = a.pathname || '';
        if (hrefPath === '/history') {
            // Let the navigation happen, then ensure the history is loaded.
            // Use a short timeout to allow SPA content swap to complete.
            setTimeout(ensureHistoryLoaded, 50);
        }
    } catch (err) {
        console.error('history link click handler error', err);
    }
});
