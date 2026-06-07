// Xem trước tên file nhạc khi chọn file
document.getElementById('song_mp3_file')?.addEventListener('change', function(e) {
    const preview = document.getElementById('song-mp3-preview');
    const file = this.files[0];
    if (preview) {
        if (file) {
            preview.textContent = `Đã chọn: ${file.name}`;
        } else {
            preview.textContent = '';
        }
    }
});
// Đóng modal bài hát
function closeSongModal() {
    document.getElementById('song-modal').style.display = 'none';
}

// Hiển thị danh sách bài hát trên trang quản lý
async function renderSongs() {
    console.log('[manage_song] renderSongs called');
    try {
        let songs = await fetchSongs();
        console.log('Fetched songs:', songs);
        
        // Nếu có filter (từ ô tìm kiếm), chỉ hiển thị bài hát khớp tên
        if (typeof arguments[0] === 'string' && arguments[0].length > 0) {
            const keyword = arguments[0];
            songs = songs.filter(song => song.title.toLowerCase().includes(keyword));
        }
        
        const container = document.getElementById('songs-container');
        if (!container) {
            console.error('songs-container not found!');
            return;
        }
        
        container.innerHTML = '';
        
        if (!songs || songs.length === 0) {
            container.innerHTML = '<div style="color:#eee;padding:20px;">Chưa có bài hát nào.</div>';
            return;
        }
        
        function normalizeImgPath(imgPath){
            const defaultImg = '/static/images/default_song.png';
            if(!imgPath) return defaultImg;
            imgPath = String(imgPath).trim();
            if(!imgPath || imgPath === 'None' || imgPath === 'null') return defaultImg;
            if(imgPath.startsWith('/static/')) return imgPath;
            if(imgPath.startsWith('static/')) return '/' + imgPath;
            if(imgPath.startsWith('/')) return '/static' + imgPath;
            return '/static/' + imgPath.replace(/^\/+/, '');
        }

        songs.forEach(song => {
            const div = document.createElement('div');
            // Add 'song-row' class and data-song-id so global context menu (right-click) works here like other pages
            div.className = 'item-card song-row';
            div.setAttribute('data-song-id', song.id);
            // Provide minimal attributes used by player/context where possible
            div.setAttribute('data-mp3-path', song.mp3_path ? (song.mp3_path.startsWith('/static/') ? song.mp3_path : '/static/' + song.mp3_path.replace(/^\/+/, '')) : '');
            div.setAttribute('data-title', song.title || '');
            div.setAttribute('data-artist-name', (song.artist_name || song.artist || '') + '');
            div.setAttribute('data-album-image', normalizeImgPath(song.image_path || song.album_image_path));
            
            // Style giống như Thể loại/Nghệ sĩ/Album
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.justifyContent = 'space-between';
            div.style.background = 'rgba(255,255,255,0.18)';
            div.style.borderRadius = '8px';
            div.style.padding = '10px 16px';
            div.style.marginBottom = '10px';
            div.style.color = '#fff';
            
            const imgPath = normalizeImgPath(song.image_path);
            
            // Hiển thị nghệ sĩ nếu có
            const artistInfo = song.artist_name || song.artist || '';
            const artistDisplay = artistInfo ? `<span style="color:#aaa; font-size:14px; margin-left:8px;">• ${artistInfo}</span>` : '';
            
            div.innerHTML = `
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="${imgPath}" alt="${song.title}" style="width:38px; height:38px; object-fit:cover; border-radius:8px; background:#eee;">
                    <div style="display:flex; flex-direction:column;">
                        <span style="font-size:17px;">${song.title}</span>
                        ${artistDisplay}
                    </div>
                </div>
                <div>
                    <button class="edit-btn" onclick="openEditSongModal(${song.id})" style="background:transparent; border:none; color:#ffd700; font-size:18px; cursor:pointer; margin-right:8px;"><i class="fa fa-edit"></i></button>
                    <button class="delete-btn" onclick="deleteSong(${song.id})" style="background:transparent; border:none; color:#ff4d4f; font-size:18px; cursor:pointer;"><i class="fa fa-trash"></i></button>
                </div>
            `;
            container.appendChild(div);
        });
        
        console.log('Songs rendered:', songs.length);
    } catch (error) {
        console.error('Error in renderSongs:', error);
    }
}
// Quản lý bài hát: hiển thị, thêm, sửa, xóa, chọn nhiều nghệ sĩ

async function fetchSongs() {
    const res = await fetch('/admin/api/song', {
        method: 'GET',
        headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
        credentials: 'include'
    });
    return res.ok ? await res.json() : [];
}

async function loadOptions() {
    // Load nghệ sĩ
    const resArtists = await fetch('/admin/api/artist', {
        method: 'GET',
        headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
        credentials: 'include'
    });
    const artists = resArtists.ok ? await resArtists.json() : [];
    const artistSelect = document.getElementById('song_artists');
    artistSelect.innerHTML = '';
    artists.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.name;
        artistSelect.appendChild(opt);
    });
    // Load album
    const resAlbums = await fetch('/admin/api/album', {
        method: 'GET',
        headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
        credentials: 'include'
    });
    const albums = resAlbums.ok ? await resAlbums.json() : [];
    const albumSelect = document.getElementById('song_album');
    albumSelect.innerHTML = '';
    // Add empty option for 'no album'
    const emptyOpt = document.createElement('option');
    emptyOpt.value = '';
    emptyOpt.textContent = '-- Không thuộc album nào --';
    albumSelect.appendChild(emptyOpt);
    albums.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.title;
        albumSelect.appendChild(opt);
    });
    // Load thể loại
    const resGenres = await fetch('/admin/api/genre', {
        method: 'GET',
        headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
        credentials: 'include'
    });
    const genres = resGenres.ok ? await resGenres.json() : [];
    const genreSelect = document.getElementById('song_genre');
    genreSelect.innerHTML = '';
    genres.forEach(g => {
        const opt = document.createElement('option');
        opt.value = g.id;
        opt.textContent = g.name;
        genreSelect.appendChild(opt);
    });
}

async function openAddSongModal() {
    document.getElementById('song_id').value = '';
    document.getElementById('song_title').value = '';
    document.getElementById('song_album').value = '';
    document.getElementById('song_genre').value = '';
    document.getElementById('song_artists').value = '';
    document.getElementById('song_image_path').value = '';
    await loadOptions();
    // Hiển thị preview ảnh rỗng
    const preview = document.getElementById('song-image-preview');
    preview.innerHTML = '<span style="color:#aaa;">Chưa có ảnh</span>';
    document.getElementById('song-modal').style.display = 'block';
}

async function openEditSongModal(id) {
    try {
        console.log('Opening edit modal for song:', id);
        const res = await fetch(`/admin/api/song/${id}`, {
            method: 'GET',
            headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
            credentials: 'include'
        });
        
        if (!res.ok) {
            alert('Không lấy được thông tin bài hát');
            return;
        }
        
        const song = await res.json();
        console.log('Song data:', song);
        
        await loadOptions();
        
        document.getElementById('song_id').value = song.id;
        document.getElementById('song_title').value = song.title;
        document.getElementById('song_album').value = song.album_id || '';
        document.getElementById('song_genre').value = song.genre_id || '';
        
        // Chọn nhiều nghệ sĩ
        const artistSelect = document.getElementById('song_artists');
        if (artistSelect && song.artists) {
            Array.from(artistSelect.options).forEach(opt => {
                opt.selected = song.artists.includes(parseInt(opt.value));
            });
        }
        
        document.getElementById('song_image_path').value = song.image_path || '';
        
        // Hiển thị preview ảnh bài hát
        const preview = document.getElementById('song-image-preview');
        if (song.image_path) {
            const imgPath = normalizeImgPath(song.image_path);
            preview.innerHTML = `<img src="${imgPath}" alt="Ảnh bài hát" style="max-width:120px;max-height:120px;border-radius:8px;">`;
        } else {
            preview.innerHTML = '<span style="color:#aaa;">Chưa có ảnh</span>';
        }
        
        document.getElementById('song-modal').style.display = 'block';
    } catch (error) {
        console.error('Error in openEditSongModal:', error);
        alert('Có lỗi xảy ra khi mở modal sửa bài hát');
    }
}

function normalizeImgPath(imgPath) {
    const defaultImg = '/static/images/default_song.png';
    if(!imgPath) return defaultImg;
    imgPath = String(imgPath).trim();
    if(!imgPath || imgPath === 'None' || imgPath === 'null') return defaultImg;
    if(imgPath.startsWith('/static/')) return imgPath;
    if(imgPath.startsWith('static/')) return '/' + imgPath;
    if(imgPath.startsWith('/')) return '/static' + imgPath;
    return '/static/' + imgPath.replace(/^\/+/, '');
}

// Xem trước ảnh bài hát khi chọn file mới
document.getElementById('song_image_file')?.addEventListener('change', function(e) {
    const preview = document.getElementById('song-image-preview');
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(evt) {
            preview.innerHTML = `<img src="${evt.target.result}" alt="Ảnh bài hát" style="max-width:120px;max-height:120px;border-radius:8px;">`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '<span style="color:#aaa;">Chưa có ảnh</span>';
    }
});

async function submitSongForm(e) {
    // e can be the event from onsubmit="submitSongForm(event)"
    if (e && e.preventDefault) e.preventDefault();
    const token = localStorage.getItem('access_token');
    const id = document.getElementById('song_id').value;
    const isEdit = !!id;
    const title = document.getElementById('song_title').value.trim();
    const album_id = document.getElementById('song_album').value || '';
    const genre_id = document.getElementById('song_genre').value || '';
    const artistSelect = document.getElementById('song_artists');
    const artists = Array.from(artistSelect ? artistSelect.selectedOptions : []).map(o => o.value);

    const imageFile = document.getElementById('song_image_file') ? document.getElementById('song_image_file').files[0] : null;
    const mp3File = document.getElementById('song_mp3_file') ? document.getElementById('song_mp3_file').files[0] : null;

    // Build FormData so files can be uploaded
    const formData = new FormData();
    formData.append('title', title);
    if (album_id) formData.append('album_id', album_id);
    if (genre_id) formData.append('genre_id', genre_id);
    // backend may expect artists as JSON string or array; send as JSON string
    formData.append('artists', JSON.stringify(artists));
    if (imageFile) formData.append('image', imageFile);
    if (mp3File) formData.append('mp3', mp3File);

    const url = isEdit ? `/admin/api/song/${id}` : '/admin/api/song';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method,
            headers: (window.buildHeaders ? window.buildHeaders() : {}),
            body: formData,
            credentials: 'include'
        });
        // Try to parse JSON, otherwise show raw text from server for better debugging
        let data = {};
        let rawText = '';
        const ct = res.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) {
            try { data = await res.json(); } catch(e){ console.warn('Failed to parse json', e); }
        } else {
            try { rawText = await res.text(); } catch(e) { console.warn('Failed to read text', e); }
        }
        if (res.ok) {
            alert(isEdit ? 'Đã cập nhật bài hát' : 'Đã thêm bài hát');
            // close modal and refresh list
            closeSongModal();
            if (typeof renderSongs === 'function') renderSongs();
        } else {
            alert((data && data.msg) || rawText || 'Lỗi khi lưu bài hát');
        }
    } catch (err) {
        console.error('submitSongForm error', err);
        alert('Lỗi kết nối server');
    }
}

async function deleteSong(id) {
    if(!window._songDeleteOps){ window._songDeleteOps = new Set(); }
    const key = 'del_song_' + id;
    if(window._songDeleteOps.has(key)) { console.warn('[manage_song] duplicate delete ignored'); return; }
    window._songDeleteOps.add(key);
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/api/song/${id}`, {
            method: 'DELETE',
            headers: (window.buildHeaders ? window.buildHeaders('application/json') : { 'Content-Type':'application/json' }),
            credentials: 'include'
        });
        let data = {}; let rawText = '';
        const ct = res.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) {
            try { data = await res.json(); } catch(e){ console.warn('parse json fail', e); }
        } else {
            try { rawText = await res.text(); } catch {}
        }
        const message = data.msg || rawText || (res.ok ? 'Đã xử lý xóa bài hát' : 'Lỗi khi xóa bài hát');
        if (res.ok || res.status === 404) {
            alert(message);
            if (typeof renderSongs === 'function') renderSongs();
        } else {
            alert(message);
        }
    } catch(err){
        console.error('[manage_song] deleteSong error', err);
        alert('Lỗi kết nối server');
    } finally {
        window._songDeleteOps.delete(key);
    }
}

// Expose functions to global scope
window.renderSongs = renderSongs;
window.fetchSongs = fetchSongs;
window.openAddSongModal = openAddSongModal;
window.openEditSongModal = openEditSongModal;
window.submitSongForm = submitSongForm;
window.deleteSong = deleteSong;
window.closeSongModal = closeSongModal;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[manage_song] DOMContentLoaded - checking for songs-container');
        if (document.getElementById('songs-container')) {
            console.log('[manage_song] Found songs-container, calling renderSongs()');
            renderSongs();
        }
    });
} else {
    // DOM already loaded
    console.log('[manage_song] DOM already ready - checking for songs-container');
    if (document.getElementById('songs-container')) {
        console.log('[manage_song] Found songs-container, calling renderSongs()');
        renderSongs();
    }
}
