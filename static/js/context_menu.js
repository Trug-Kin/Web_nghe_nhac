// Context menu logic for adding songs to playlists
(function(){
  // Fallback bootstrap if window.__SongContextMenu missing (e.g. base template script failed earlier)
  if(!window.__SongContextMenu){
    const menu = document.getElementById('song-context-menu');
    if(menu){
      let currentSongId=null;
      window.__SongContextMenu={
        showFor(songId,x,y){
          currentSongId=songId;
          menu.style.left=x+'px';
          menu.style.top=y+'px';
          menu.style.display='block';
          console.debug('[ContextMenu:Fallback] show', songId);
        },
        hide(){ menu.style.display='none'; currentSongId=null; },
        getSongId:()=>currentSongId
      };
      console.debug('[ContextMenu] Fallback init applied');
    } else {
      console.warn('[ContextMenu] menu element not found for fallback');
    }
  }
  const menu = document.getElementById('song-context-menu');
  if(!menu) return;
  const listEl = document.getElementById('context-playlist-list');
  const searchInput = document.getElementById('context-playlist-search');
  const createBtn = document.getElementById('context-create-playlist-btn');
  const createForm = document.getElementById('context-create-form');
  const newName = document.getElementById('context-new-playlist-name');
  const newDesc = document.getElementById('context-new-playlist-desc');
  const saveBtn = document.getElementById('context-save-playlist');
  const cancelCreate = document.getElementById('context-cancel-create');
  const createMsg = document.getElementById('context-create-msg');
  const toastContainer = document.getElementById('toast-container');
  let playlistsCache = null;
  let playlistsLoadedAt = 0;
  let fetchInFlight = null;
  const CACHE_TTL_MS = 60 * 1000;

  function getTokenHeaders(){
    const headers = {'Content-Type':'application/json'};
  const t = localStorage.getItem('access_token');
    if(t) headers['Authorization'] = 'Bearer ' + t;
    return headers;
  }
  function showToast(message, type='info', timeout=3200){
    if(!toastContainer) return; 
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.innerHTML = `<span>${message}</span><button class="close-btn" aria-label="Đóng">×</button>`;
    toastContainer.appendChild(el);
    const remove = ()=>{ el.style.animation='toast-out .25s forwards'; setTimeout(()=> el.remove(), 240); };
    el.querySelector('.close-btn').addEventListener('click', remove);
    if(timeout>0) setTimeout(remove, timeout);
  }
  function clearList(){
    listEl.innerHTML='';
  }
  function renderPlaylists(filter=''){
    if(!Array.isArray(playlistsCache)) return;
    const term = filter.trim().toLowerCase();
    clearList();
    const filtered = term ? playlistsCache.filter(p => p.name.toLowerCase().includes(term)) : playlistsCache;
    if(filtered.length === 0){
      listEl.innerHTML = '<div style="padding:8px 14px;color:#777;font-size:12px;">Không có playlist</div>';
      return;
    }
    filtered.forEach(p => {
      const item = document.createElement('div');
      item.className = 'playlist-item';
      item.setAttribute('data-playlist-id', p.id);
      item.textContent = p.name + (p.song_count != null ? ` (${p.song_count})` : '');
      item.addEventListener('click', () => addCurrentSongToPlaylist(p.id));
      listEl.appendChild(item);
    });
  }
  async function loadPlaylists(force=false){
    const now = Date.now();
    if(!force && playlistsCache && (now - playlistsLoadedAt < CACHE_TTL_MS)){
      renderPlaylists(searchInput.value);
      return playlistsCache;
    }
    if(fetchInFlight) return fetchInFlight;
    listEl.innerHTML = '<div style="padding:8px 14px;color:#777;font-size:12px;">Đang tải playlist...</div>';
    fetchInFlight = fetch('/api/playlists/', {headers: getTokenHeaders(), credentials:'include'})
      .then(r => r.json().then(j=>({ok:r.ok,data:j,status:r.status})))
      .then(obj => {
        fetchInFlight = null;
        if(obj.ok && Array.isArray(obj.data)){
          playlistsCache = obj.data;
          playlistsLoadedAt = Date.now();
          renderPlaylists(searchInput.value);
        } else {
          // Better error message
          let errMsg = 'Lỗi tải playlist';
          if(obj.status === 401 || obj.status === 422){
            errMsg = 'Vui lòng đăng nhập';
          } else if(obj.data && obj.data.msg){
            errMsg = obj.data.msg;
          }
          listEl.innerHTML = `<div style="padding:8px 14px;color:#d55;font-size:12px;">${errMsg}</div>`;
          console.error('Playlist load error:', obj.status, obj.data);
        }
        return playlistsCache;
      })
      .catch(err => {
        fetchInFlight = null;
        listEl.innerHTML = '<div style="padding:8px 14px;color:#d55;font-size:12px;">Lỗi mạng</div>';
        console.error('Network error loading playlists:', err);
      });
    return fetchInFlight;
  }
  async function addCurrentSongToPlaylist(playlistId){
    const songId = window.__SongContextMenu?.getSongId();
    if(!songId){ showToast('Không xác định bài hát', 'error'); return; }
    const payload = { song_id: parseInt(songId) };
    const listItem = listEl.querySelector(`.playlist-item[data-playlist-id="${playlistId}"]`);
    if(listItem){ listItem.classList.add('disabled'); }
    try {
      const resp = await fetch(`/api/playlists/${playlistId}/add_song`, { method:'POST', headers:getTokenHeaders(), credentials:'include', body: JSON.stringify(payload)});
      const data = await resp.json();
      if(resp.ok){
        showToast('Đã thêm vào playlist', 'success');
        if(listItem){ listItem.classList.add('added'); listItem.classList.remove('disabled'); }
      } else {
        showToast(data.msg || 'Không thêm được', 'error');
        if(listItem) listItem.classList.remove('disabled');
      }
    } catch(e){
      showToast('Lỗi mạng khi thêm', 'error');
      if(listItem) listItem.classList.remove('disabled');
    }
  }

  // Create playlist with current song
  async function createPlaylistWithCurrent(){
    console.log('[ContextMenu] createPlaylistWithCurrent called');
    const name = newName.value.trim();
    const description = newDesc.value.trim();
    const songId = window.__SongContextMenu?.getSongId();
    console.log('[ContextMenu] Create playlist data:', { name, description, songId });
    
    if(!name){ 
      createMsg.textContent='Nhập tên playlist'; 
      createMsg.style.color='#d55'; 
      console.warn('[ContextMenu] No playlist name provided');
      return; 
    }
    if(!songId){ 
      createMsg.textContent='Không xác định bài hát'; 
      createMsg.style.color='#d55'; 
      console.warn('[ContextMenu] No song ID found');
      return; 
    }
    
    createMsg.textContent='Đang tạo...'; 
    createMsg.style.color='#888';
    saveBtn.disabled = true;
    
    const payload = { name, description, song_ids:[parseInt(songId)] };
    console.log('[ContextMenu] Creating playlist with payload:', payload);
    
    try {
      const resp = await fetch('/api/playlists', { 
        method:'POST', 
        headers:getTokenHeaders(), 
        credentials:'include', 
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      console.log('[ContextMenu] Create response:', resp.status, data);
      
      if(resp.ok){
        createMsg.textContent='Tạo thành công!'; 
        createMsg.style.color='#2ecc71';
        showToast('Playlist đã tạo', 'success');
        // Clear form
        newName.value = '';
        newDesc.value = '';
        // Refresh cache after small delay then re-render
        playlistsCache = null; // force reload
        setTimeout(()=>{ 
          loadPlaylists(true);
          createForm.style.display='none';
          createMsg.textContent='';
        }, 400);
        setTimeout(()=>{ window.__SongContextMenu?.hide(); }, 1000);
      } else {
        createMsg.textContent = data.msg || 'Lỗi tạo playlist'; 
        createMsg.style.color='#d55';
        console.error('[ContextMenu] Failed to create playlist:', data);
      }
    } catch(e){
      createMsg.textContent='Lỗi mạng'; 
      createMsg.style.color='#d55';
      console.error('[ContextMenu] Network error creating playlist:', e);
    } finally { 
      saveBtn.disabled = false; 
    }
  }

  // Event wiring
  if(createBtn){
    createBtn.addEventListener('click', ()=>{
      console.log('[ContextMenu] Create button clicked, form display:', createForm.style.display);
      if(createForm.style.display==='none' || !createForm.style.display){ 
        createForm.style.display='block'; 
        newName.focus();
        console.log('[ContextMenu] Showing create form');
      }
      else {
        createForm.style.display='none';
        console.log('[ContextMenu] Hiding create form');
      }
    });
  } else {
    console.warn('[ContextMenu] Create button not found!');
  }
  
  if(cancelCreate){ 
    cancelCreate.addEventListener('click', ()=>{ 
      createForm.style.display='none'; 
      createMsg.textContent='';
      console.log('[ContextMenu] Create cancelled');
    }); 
  }
  
  if(saveBtn){ 
    saveBtn.addEventListener('click', ()=>{
      console.log('[ContextMenu] Save button clicked');
      createPlaylistWithCurrent();
    });
  } else {
    console.warn('[ContextMenu] Save button not found!');
  }
  
  if(searchInput){ 
    searchInput.addEventListener('input', ()=> renderPlaylists(searchInput.value)); 
  }

  // Right-click listener (delegated): Works on tables or any element with data-song-id
  document.addEventListener('contextmenu', async (e)=>{
    const row = e.target.closest('tr[data-song-id], .song-row[data-song-id]');
    if(row){
      e.preventDefault();
      const songId = row.getAttribute('data-song-id');
      console.log('[ContextMenu] Right-click on song, ID:', songId);
      if(!songId) return;
      window.__SongContextMenu?.showFor(songId, clampX(e.clientX), clampY(e.clientY));
      // load playlists (async) but user can start searching
      loadPlaylists();
      searchInput.value='';
    } else {
      // Debugging: show message when right-click not on song row
      // console.debug('[ContextMenu] contextmenu ignored (no song-row target)');
    }
  });

  function clampX(x){
    const w = menu.offsetWidth || 260; const vw = window.innerWidth; return Math.min(x, vw - w - 4);
  }
  function clampY(y){
    const h = menu.offsetHeight || 320; const vh = window.innerHeight; return Math.min(y, vh - h - 4);
  }
  window.addEventListener('resize', ()=>{ if(menu.style.display==='block'){ menu.style.left=clampX(parseInt(menu.style.left||'0'))+'px'; menu.style.top=clampY(parseInt(menu.style.top||'0'))+'px'; } });

})();
