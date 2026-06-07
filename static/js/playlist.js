// =======================================================
// Playlist Detail Page Functions
// =======================================================
if (typeof window.playlistJsLoaded === 'undefined') {
window.playlistJsLoaded = true;

// Note: Modal and creation form handling is now in playlists.html page
// This file only handles playlist detail page functionality

// --- Per-playlist page: load songs, add/remove ---
async function fetchJSON(url, opts={}){
    opts.headers = Object.assign({'Content-Type':'application/json'}, opts.headers || {});
    // Add fallback Authorization header from stored token if present
    const token = localStorage.getItem('access_token');
    if (token && !opts.headers['Authorization']) opts.headers['Authorization'] = `Bearer ${token}`;
    opts.credentials = 'include';
    const res = await fetch(url, opts);
    // If unauthorized, redirect to login page
    if (res.status === 401) {
        try { localStorage.removeItem('username'); localStorage.removeItem('role'); } catch(e){}
        window.location.href = '/auth/login-page';
        return { ok: false, status: 401, json: { msg: 'unauthorized' } };
    }
    const json = await res.json().catch(()=>({}));
    return {ok: res.ok, status: res.status, json};
}

async function loadPlaylist(playlistId){
    // If the global detail loader (app.js) is present and will handle rendering for entity pages,
    // avoid double-rendering here. App sets a hidden input `entity-type` when it will call loadDetailPage.
    const entityType = document.getElementById('entity-type');
    if (entityType && entityType.value && ['artist','genre','album','playlists'].includes(entityType.value)) {
        // Let app.js load and render the playlist via its loadDetailPage; but still fetch cache for other actions
        if (window._playlistCache && window._playlistCache.id === playlistId) {
            renderPlaylist(window._playlistCache.data);
            return;
        }
    }
    if(window._playlistCache && window._playlistCache.id === playlistId){
        // Render from cache without fetch
        renderPlaylist(window._playlistCache.data);
        return;
    }
    const r = await fetchJSON(`/api/playlists/${playlistId}`);
    if(!r.ok){
        if (r.status === 401) return; // fetchJSON already redirected
        // If server says playlist doesn't exist or is hidden for this user, redirect away
        if (r.status === 404) {
            // Clear any client-side auth hints then navigate home
            try { localStorage.removeItem('username'); localStorage.removeItem('access_token'); } catch(e){}
            window.location.href = '/';
            return;
        }
        // show a non-blocking message instead of alert for other errors
        console.warn('Không thể tải playlist:', r.json?.msg || r.status);
        const container = document.getElementById('playlist-songs');
        if (container) container.innerHTML = '<div class="alert">Không thể tải playlist.</div>';
        return;
    }
    const p = r.json;
    window._playlistCache = {id: playlistId, data: p, ts: Date.now()};
    renderPlaylist(p);
    // Initialize handlers (delete etc.) then reveal the page to ensure actions are ready
    try { initDeleteHandler(); showPlaylistContainer(); } catch(e){}
}

function renderPlaylist(p){
    const nameEl = document.getElementById('playlist-name');
    if(nameEl) nameEl.innerText = p.name;
    const descEl = document.getElementById('playlist-desc');
    if(descEl) descEl.innerText = p.description || '';
    const container = document.getElementById('playlist-songs');
    if(!container) return;
    container.innerHTML = '';
    p.songs.forEach(s => {
        // normalize mp3 path
    let mp3 = s.mp3_url || s.mp3_path || '';
        mp3 = (mp3 + '').trim();
        if (!/^https?:\/\//i.test(mp3) && !mp3.startsWith('/')) {
            if (mp3.includes('/')) mp3 = `/static/${mp3.replace(/^\/+/,'')}`;
            else mp3 = `/static/music/${mp3.replace(/^\/+/,'')}`;
        }
        try { mp3 = encodeURI(mp3); } catch(e){}

        // Create table row matching structure used by app.js
        const tr = document.createElement('tr');
        tr.className = 'song-row';
        tr.setAttribute('data-song-id', s.id || '');
        tr.setAttribute('data-mp3-path', mp3);
        tr.setAttribute('data-title', s.title || '');
        tr.setAttribute('data-artist-name', s.artist_name || '');
        tr.setAttribute('data-artist-id', s.artist_id || '');
        tr.setAttribute('data-album-image', s.album_image_path || '/static/images/default.jpg');
        tr.innerHTML = `
            <td style="text-align:center;vertical-align:middle;padding:6px;"><input type="checkbox" class="song-select-checkbox" data-song-id="${s.id}"></td>
            <td>—</td>
            <td>
                <div class="song-title">
                    <i class="fa-solid fa-play play-icon"></i>
                    <span style="margin-left:8px;color:#fff;">${escapeHtml(s.title)}</span>
                </div>
            </td>
            <td>${escapeHtml(s.artist_name || '')}</td>
                <td class="like-cell" style="text-align:center;vertical-align:middle;padding:0;"><button class="like-button" title="Thích" style="background:transparent;border:none;min-width:32px;"><i class="fa-regular fa-heart like-icon"></i><span class="like-count">${s.like_count || 0}</span></button></td>
            <td class="listen-count" style="text-align:center;vertical-align:middle;padding:0;"><span style="display:inline-block;min-width:32px;">${s.listen_count || 0}</span></td>
            <td style="text-align:center;vertical-align:middle;padding:0;"><button class="remove-song-btn" data-id="${s.id}" title="Xóa khỏi playlist" style="background:transparent;border:none;color:#ff6b6b;cursor:pointer;font-size:14px;padding:6px;">Xóa</button></td>
        `;
        container.appendChild(tr);
    });
    // No-op: remove buttons are handled by delegated listener registered below
}
// When playlist content is rendered, ensure the page container is visible
function showPlaylistContainer(){
    const page = document.getElementById('entity-page');
    if(page) page.style.display = '';
}

// Temporarily swap the playlist image to the default placeholder for a short time
// without modifying any server-side data. The original src is restored after
// `ms` milliseconds or earlier if the original image finishes loading.
function temporarilyShowDefaultImage(ms = 800){
    try {
        const img = document.getElementById('entity-image');
        if(!img) return;
        const defaultPath = '/static/images/playlist_image.png';
        // Normalize full URL comparisons: if already the default, do nothing
        const currentSrc = img.getAttribute('src') || img.src || '';
        if(!currentSrc) return;
        // If current is already the same as default, nothing to do
        if(currentSrc.indexOf('playlist_image.png') !== -1) return;

        // Store original (use data attribute so we don't clobber src)
        img.dataset.origSrc = currentSrc;
        // Swap to default placeholder
        img.src = defaultPath;

        // Only restore the original if it actually loads successfully.
        // This avoids setting a broken src back onto the img and ending up with no image.
        const originalSrc = currentSrc;
        let originalLoaded = false;

        const restore = () => {
            try {
                if(img.dataset && img.dataset.origSrc){
                    if(originalLoaded){
                        img.src = img.dataset.origSrc;
                    }
                    // cleanup stored original regardless
                    delete img.dataset.origSrc;
                }
            } catch(e){}
        };

        // Preload original to detect availability
        const probe = new Image();
        probe.onload = () => { originalLoaded = true; restore(); };
        probe.onerror = () => { /* keep default until timeout, then cleanup without restoring */ };
        probe.src = originalSrc;

        // After timeout, restore only if original actually loaded; otherwise keep placeholder
        setTimeout(() => { try { restore(); } catch(e){} }, Math.max(100, Math.min(ms, 1000)));
    } catch(e){ console.warn('temp image swap failed', e); }
}

// add song button
const addBtn = document.getElementById('add-song-btn');
const bulkAddBtn = document.getElementById('bulk-add-btn');
const bulkAddInput = document.getElementById('bulk-add-song-ids');
const editBtn = document.getElementById('edit-playlist-btn');
const bulkRemoveBtn = document.getElementById('bulk-remove-btn');
// Note: delete button binding is handled by initDeleteHandler() to ensure it's
// registered before the page is revealed (idempotent).
const actionMsg = document.getElementById('playlist-action-message');
if(addBtn){
    addBtn.addEventListener('click', async ()=>{
        const playlistId = location.pathname.split('/').pop();
        const songId = document.getElementById('add-song-id').value;
          actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang thêm...');
        const r = await fetchJSON(`/api/playlists/${playlistId}/add_song`, {method:'POST', body: JSON.stringify({song_id: songId})});
        if(r.ok){
            loadPlaylist(playlistId);
                document.getElementById('add-song-id').value='';
                actionMsg && (actionMsg.style.color='green', actionMsg.textContent='Đã thêm bài vào playlist');
        } else {
            if (r.status === 401) return; // redirected
            console.warn('Lỗi khi thêm bài:', r.json?.msg || r.status);
                actionMsg && (actionMsg.style.color='red', actionMsg.textContent=r.json?.msg || 'Lỗi thêm bài');
        }
    })
}

// --- Song search & add from search ---
const searchInput = document.getElementById('song-search-input');
const searchStatus = document.getElementById('song-search-status');
const searchResultsUl = document.getElementById('song-search-results');
const addSelectedSearchBtn = document.getElementById('add-selected-search-songs');
let searchDebounce;
if(searchInput){
    searchInput.addEventListener('input', ()=>{
        const term = searchInput.value.trim();
        clearTimeout(searchDebounce);
        if(!term){
            searchResultsUl.innerHTML='';
            searchStatus.textContent='';
            addSelectedSearchBtn.style.display='none';
            return;
        }
        searchStatus.style.color='#888';
        searchStatus.textContent='Đang tìm...';
        searchDebounce = setTimeout(()=>doSearch(term), 320);
    });
}

async function doSearch(term){
    try {
        const r = await fetchJSON(`/api/playlists/search_songs?q=${encodeURIComponent(term)}`);
        if(!r.ok){
            searchStatus.style.color='red';
            searchStatus.textContent=r.json?.msg || 'Lỗi tìm kiếm';
            return;
        }
        const songs = r.json.songs||[];
        searchResultsUl.innerHTML='';
        if(songs.length===0){
            searchStatus.style.color='#888';
            searchStatus.textContent='Không có kết quả';
            addSelectedSearchBtn.style.display='none';
            return;
        }
        searchStatus.style.color='#888';
        searchStatus.textContent=`${songs.length} kết quả`;
        songs.forEach(s=>{
            const li=document.createElement('li');
            li.style.padding='6px 8px';
            li.style.borderBottom='1px solid #222';
            li.innerHTML = `<label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                <input type="checkbox" class="search-song-checkbox" data-song-id="${s.id}">
                <span style="flex:1;">${escapeHtml(s.title)} <span style="color:#888;font-size:11px;">${s.artist_name||''}</span></span>
                <button type="button" class="add-single-search-btn" data-id="${s.id}" style="font-size:11px;">Thêm</button>
            </label>`;
            searchResultsUl.appendChild(li);
        });
        updateAddSelectedVisibility();
        // Bind single add buttons
        Array.from(document.getElementsByClassName('add-single-search-btn')).forEach(btn=>{
            btn.addEventListener('click', async (e)=>{
                const id = e.target.getAttribute('data-id');
                await addSingleSong(id);
            });
        });
        // Checkbox change
        searchResultsUl.addEventListener('change', (e)=>{
            if(e.target.classList && e.target.classList.contains('search-song-checkbox')) updateAddSelectedVisibility();
        }, {once:false});
    } catch(e){
        searchStatus.style.color='red';
        searchStatus.textContent='Lỗi mạng tìm kiếm';
    }
}

function updateAddSelectedVisibility(){
    if(!addSelectedSearchBtn) return;
    const checked = document.querySelectorAll('.search-song-checkbox:checked');
    addSelectedSearchBtn.style.display = checked.length>0 ? 'inline-block':'none';
}

async function addSingleSong(songId){
    if(!songId) return;
    const playlistId = location.pathname.split('/').pop();
    actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang thêm...');
    const r = await fetchJSON(`/api/playlists/${playlistId}/add_song`, {method:'POST', body: JSON.stringify({song_id: songId})});
    if(r.ok){
        actionMsg && (actionMsg.style.color='green', actionMsg.textContent='Đã thêm 1 bài');
        loadPlaylist(playlistId);
    } else {
        actionMsg && (actionMsg.style.color='red', actionMsg.textContent=r.json?.msg||'Lỗi thêm');
    }
}

if(addSelectedSearchBtn){
    addSelectedSearchBtn.addEventListener('click', async ()=>{
        const playlistId = location.pathname.split('/').pop();
        const ids = Array.from(document.querySelectorAll('.search-song-checkbox:checked')).map(cb=>parseInt(cb.getAttribute('data-song-id'))).filter(n=>!isNaN(n));
        if(ids.length===0) return;
        actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang thêm nhiều bài (tìm kiếm)...');
        const r = await fetchJSON(`/api/playlists/${playlistId}/add_songs`, {method:'POST', body: JSON.stringify({song_ids: ids})});
        if(r.ok){
            const added = r.json?.added_ids?.length || 0;
            const skipped = r.json?.skipped?.length || 0;
            actionMsg && (actionMsg.style.color='green', actionMsg.textContent=`Đã thêm: ${added}, Bỏ qua: ${skipped}`);
            loadPlaylist(playlistId);
            // uncheck
            document.querySelectorAll('.search-song-checkbox:checked').forEach(cb=>cb.checked=false);
            updateAddSelectedVisibility();
        } else {
            actionMsg && (actionMsg.style.color='red', actionMsg.textContent=r.json?.msg||'Lỗi thêm nhiều (tìm)');
        }
    });
}

// Delegated handler for remove-song buttons on playlist detail page
document.addEventListener('click', async function(e){
    const btn = e.target.closest && e.target.closest('.remove-song-btn');
    if(!btn) return;
    // ensure this is on a playlist detail page
    if(!location.pathname.includes('/playlist/')) return;
    const playlistId = location.pathname.split('/').pop();
    const songId = btn.getAttribute('data-id');
    if(!songId) return;
    if(!confirm('Xóa bài này khỏi playlist?')) return;
    actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang xóa...');
    const rr = await fetchJSON(`/api/playlists/${playlistId}/remove_song`, {method:'POST', body: JSON.stringify({song_id: songId})});
    if(rr.ok){
        actionMsg && (actionMsg.style.color='green', actionMsg.textContent='Đã xóa bài');
        try{ loadPlaylist(playlistId); } catch(e){ window.location.reload(); }
    } else {
        if (rr.status === 401) return; // fetchJSON redirected
        actionMsg && (actionMsg.style.color='red', actionMsg.textContent= rr.json?.msg || 'Lỗi xóa');
    }
});

function escapeHtml(str){
    return (str||'').replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
}

// Bulk add songs by IDs
if(bulkAddBtn){
    bulkAddBtn.addEventListener('click', async ()=>{
        const playlistId = location.pathname.split('/').pop();
        const raw = bulkAddInput ? bulkAddInput.value.trim() : '';
        if(!raw){
            actionMsg && (actionMsg.style.color='red', actionMsg.textContent='Nhập ID bài hát (vd: 12,15,20)');
            return;
        }
        const ids = raw.split(/[,\s]+/).map(x=>parseInt(x,10)).filter(n=>!isNaN(n));
        if(ids.length === 0){
            actionMsg && (actionMsg.style.color='red', actionMsg.textContent='Không có ID hợp lệ');
            return;
        }
        actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang thêm nhiều bài...');
        const r = await fetchJSON(`/api/playlists/${playlistId}/add_songs`, {method:'POST', body: JSON.stringify({song_ids: ids})});
        if(r.ok){
            const addedCount = r.json?.added?.length || 0;
            const skippedCount = r.json?.skipped?.length || 0;
            actionMsg && (actionMsg.style.color='green', actionMsg.textContent=`Đã thêm: ${addedCount}, Bỏ qua: ${skippedCount}`);
            bulkAddInput && (bulkAddInput.value='');
            loadPlaylist(playlistId);
        } else {
            if (r.status === 401) return; // redirected
            actionMsg && (actionMsg.style.color='red', actionMsg.textContent=r.json?.msg || 'Lỗi thêm nhiều bài');
        }
    });
}

// Delete playlist
// delete handler initialization (idempotent)
function initDeleteHandler(){
    try{
        if(window._playlistDeleteInit) return;
        const deleteBtn = document.getElementById('delete-playlist-btn');
        const actionEl = document.getElementById('playlist-action-message') || actionMsg;
        if(!deleteBtn) { window._playlistDeleteInit = true; return; }
        deleteBtn.addEventListener('click', async ()=>{
            if(!confirm('Xóa playlist này?')) return;
            const playlistId = location.pathname.split('/').pop();
            actionEl && (actionEl.style.color='gray', actionEl.textContent='Đang xóa...');
            const r = await fetchJSON(`/api/playlists/${playlistId}`, {method:'DELETE'});
            if(r.ok){
                actionEl && (actionEl.style.color='green', actionEl.textContent='Đã xóa playlist');
                setTimeout(()=>{ window.location.href='/playlists'; }, 800);
            } else {
                actionEl && (actionEl.style.color='red', actionEl.textContent=r.json?.msg || 'Xóa thất bại');
            }
        });
        window._playlistDeleteInit = true;
    } catch(e){ console.warn('initDeleteHandler failed', e); window._playlistDeleteInit = true; }
}

// Edit playlist
// Modal edit logic
const editModal = document.getElementById('editPlaylistModal');
const closeEdit = document.querySelector('#editPlaylistModal .close-edit');
const editForm = document.getElementById('editPlaylistForm');
const editNameInput = document.getElementById('editPlaylistName');
const editDescInput = document.getElementById('editPlaylistDesc');
const editMsg = document.getElementById('editPlaylistMessage');
const cancelEditBtn = document.getElementById('cancelEditBtn');

function openEditModal(){
    const currentName = document.getElementById('playlist-name')?.innerText || '';
    const currentDesc = document.getElementById('playlist-desc')?.innerText || '';
    editNameInput.value = currentName;
    editDescInput.value = currentDesc;
    editMsg.textContent='';
    editModal.style.display='block';
}
function closeEditModal(){ editModal.style.display='none'; }

if(editBtn){ editBtn.addEventListener('click', openEditModal); }
closeEdit && closeEdit.addEventListener('click', closeEditModal);
cancelEditBtn && cancelEditBtn.addEventListener('click', closeEditModal);

if(editForm){
    editForm.addEventListener('submit', async (e)=>{
        e.preventDefault();
        const playlistId = location.pathname.split('/').pop();
        const name = editNameInput.value.trim();
        const description = editDescInput.value.trim();
        if(!name){ editMsg.style.color='red'; editMsg.textContent='Tên không được trống'; return; }
        editMsg.style.color='gray'; editMsg.textContent='Đang lưu...';
        const r = await fetchJSON(`/api/playlists/${playlistId}`, {method:'PUT', body: JSON.stringify({name, description})});
        if(r.ok){
            editMsg.style.color='green'; editMsg.textContent='Đã cập nhật';
            actionMsg && (actionMsg.style.color='green', actionMsg.textContent='Đã cập nhật playlist');
            setTimeout(()=>{ closeEditModal(); loadPlaylist(playlistId); }, 600);
        } else {
            editMsg.style.color='red'; editMsg.textContent=r.json?.msg || 'Lỗi cập nhật';
        }
    });
}

// Bulk remove selected songs
function refreshBulkRemoveVisibility(){
  if(!bulkRemoveBtn) return;
  const checked = document.querySelectorAll('.song-select-checkbox:checked');
  bulkRemoveBtn.style.display = checked.length > 0 ? 'inline-block' : 'none';
}
if(bulkRemoveBtn){
  bulkRemoveBtn.addEventListener('click', async ()=>{
      const playlistId = location.pathname.split('/').pop();
      const checked = Array.from(document.querySelectorAll('.song-select-checkbox:checked'));
      if(checked.length === 0) return;
      if(!confirm(`Xóa ${checked.length} bài khỏi playlist?`)) return;
      actionMsg && (actionMsg.style.color='gray', actionMsg.textContent='Đang xóa bài...');
      const songIds = checked.map(cb=>parseInt(cb.getAttribute('data-song-id'))).filter(Number.isInteger);
      const r = await fetchJSON(`/api/playlists/${playlistId}/remove_songs`, {method:'POST', body: JSON.stringify({song_ids: songIds})});
      if(r.ok){
          actionMsg && (actionMsg.style.color='green', actionMsg.textContent=r.json?.msg || 'Đã xóa');
      } else {
          actionMsg && (actionMsg.style.color='red', actionMsg.textContent=r.json?.msg || 'Lỗi xóa');
      }
      loadPlaylist(playlistId);
  });
  document.addEventListener('change', (e)=>{
      if(e.target.classList && e.target.classList.contains('song-select-checkbox')) refreshBulkRemoveVisibility();
  });
}

// on page load, infer playlist id from url
(function(){
    // Show default placeholder briefly while the page is refreshing/loading
    try { temporarilyShowDefaultImage(800); } catch(e){}
    // Only attempt to auto-load when on the playlist page.
    // Heuristic: pathname contains '/playlist/' OR the playlist container exists in DOM.
    const path = location.pathname || '';
    const containerExists = !!document.getElementById('playlist-songs');
    if (path.includes('/playlist/') || containerExists) {
        const parts = path.split('/').filter(Boolean);
        const last = parts[parts.length-1];
        if (last && !isNaN(Number(last))) {
            const playlistId = Number(last);
            // If server already rendered song rows (server-side rendering when owner),
            // there's no need to fetch the playlist again on initial load — show immediately.
            const serverRows = document.querySelectorAll('#song-list-body tr.song-row');
            if (serverRows && serverRows.length > 0) {
                try { initDeleteHandler(); showPlaylistContainer(); } catch(e){}
                // Ensure management controls/hide logic still runs below
            } else {
                // No server-rendered rows: fetch via API as before
                loadPlaylist(playlistId);
            }
        }
    }
    // Hide management controls if not owner/admin (client hint; server still enforces)
    try {
        const current = window.CURRENT_USER;
        const ownerId = window.PLAYLIST_OWNER_ID;
        const role = current && current.role;
        const can = current && (current.id === ownerId || role === 'admin');
        if(!can){
            ['add-song-id','add-song-btn','bulk-add-song-ids','bulk-add-btn','edit-playlist-btn','delete-playlist-btn','bulk-remove-btn','song-search-panel']
              .forEach(id=>{ const el=document.getElementById(id); if(el) el.style.display='none'; });
        }
    } catch(e){}
})();

// Generic helper to augment existing song tables on artist/album/genre pages with checkboxes if not already present
document.addEventListener('DOMContentLoaded', function(){
    const tbody = document.getElementById('song-list-body');
    if(!tbody) return;
    // Wait a tick in case another script populates rows
    setTimeout(()=>{
        Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
            // No longer adding selection checkbox
            return;
            const songIdAttr = tr.getAttribute('data-song-id');
            if(!songIdAttr) return;
            const firstCell = tr.querySelector('td:nth-child(1)');
            // Insert checkbox in new cell before play button cell (structure may vary)
            const checkboxCell = document.createElement('td');
            // Checkbox UI removed
            checkboxCell.innerHTML = '';
            // Append before last cell if last is play button placeholder
            tr.insertBefore(checkboxCell, tr.children[tr.children.length-1]);
        });
    }, 500);
});
} // End if playlistJsLoaded check
