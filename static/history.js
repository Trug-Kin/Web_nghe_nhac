// history.js - always loads listening history when /history page is shown

function headers(){
    const h={'Content-Type':'application/json'};
    const tokenLocal = localStorage.getItem('access_token');
    const tokenCookie = document.cookie.split('; ').find(r=>r.startsWith('access_token='));
    const token = tokenLocal || (tokenCookie ? tokenCookie.split('=')[1] : null);
    if(token) h['Authorization'] = 'Bearer ' + token;
    return h;
}

function loadHistory(){
    const bodyEl = document.getElementById('history-body');
    const statusEl = document.getElementById('history-status');
    if (!bodyEl || !statusEl) return;
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
            const errorMsg = (obj.data && obj.data.msg) || 'Không tải được lịch sử.';
            statusEl.textContent = errorMsg; 
            bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Chưa có lịch sử nghe</td></tr>';
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
    })
    .catch(err=>{ 
        statusEl.textContent='Lỗi kết nối: ' + err.message; 
        bodyEl.innerHTML='<tr><td colspan="4" style="text-align:center;color:#888;">Lỗi tải dữ liệu</td></tr>';
    });
}

// Tự động gọi lại khi vào đúng trang /history (SPA hoặc reload)
function ensureHistoryLoaded(){
    if (window.location.pathname === '/history') {
        setTimeout(loadHistory, 0);
    }
}

document.addEventListener('DOMContentLoaded', ensureHistoryLoaded);
window.addEventListener('popstate', ensureHistoryLoaded);
// Nếu dùng SPA custom event, có thể cần lắng nghe thêm sự kiện chuyển trang
