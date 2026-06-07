// Guard toàn cục chống load đôi file JS (khi template include 2 lần)
if (window._adminMusicScriptOnce) {
    console.log('[manage_music] Duplicate script load ignored');
} else {
    window._adminMusicScriptOnce = true;
    console.log('[manage_music] Script initialized once');

    (function(){
    // --- begin scoped module for manage_music.js to avoid redeclarations on duplicate loads ---

    // Helper: build headers that include Authorization only when token exists.
    function buildHeaders(contentType){
        const headers = {};
        if (contentType) headers['Content-Type'] = contentType;
        try {
            // Prefer cookie-based auth when available. Only add Authorization header
            // from localStorage when there is no access_token cookie present.
            const cookieHas = (typeof document !== 'undefined') && (document.cookie.split('; ').find(row => row.startsWith('access_token=')));
            if (!cookieHas) {
                const t = (window.getToken && typeof window.getToken === 'function') ? window.getToken() : localStorage.getItem('access_token');
                if (t) headers['Authorization'] = 'Bearer ' + t;
            }
        } catch(e) {
            // ignore
        }
        return headers;
    }

    // Expose for other scripts so they can use cookie-first header behavior
    try { window.buildHeaders = buildHeaders; } catch(e) { /* ignore if not allowed */ }

// XÓA NGHỆ SĨ
let _lastDeleteArtistCall = 0;
async function deleteArtist(id, name) {
    const now = Date.now();
    if (now - _lastDeleteArtistCall < 800) {
        console.warn('[manage_music] Bỏ qua gọi xóa nghệ sĩ trùng (debounce)');
        return;
    }
    _lastDeleteArtistCall = now;
    console.log('[manage_music] deleteArtist invoked id=', id, 'name=', name);
    if (!confirm(`Bạn có chắc muốn xóa nghệ sĩ "${name}"?`)) return;
    const token = getToken();
    try {
        const opKey = 'del_artist_' + id;
        if(!beginOp(opKey)) { console.warn('[manage_music] deleteArtist ignored duplicate (in-flight)'); return; }
        const res = await fetch(`/admin/api/artist/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token },
            credentials: 'include'
        });
        console.log('[manage_music] DELETE /api/artist status:', res.status);
        let data = {};
        try { data = await res.json(); } catch(parseErr){ console.warn('Không parse được JSON delete artist:', parseErr); }
        if (res.ok || res.status === 404) {
            alert(data.msg || 'Đã xử lý xóa nghệ sĩ!');
            if (window.allArtistsCache) {
                window.allArtistsCache = window.allArtistsCache.filter(a => a.id !== id);
                renderArtistList(window.allArtistsCache);
            } else {
                fetchAllArtists();
            }
        } else {
            alert(data.msg || `Lỗi xóa nghệ sĩ (status ${res.status})`);
        }
        endOp(opKey);
    } catch (err) {
        console.error('[manage_music] Lỗi fetch DELETE artist:', err);
        alert('Lỗi kết nối server');
    }
}
// ====== XỬ LÝ SUBMIT FORM THÊM MỚI (ADD) ======
document.addEventListener('DOMContentLoaded', function() {
    if (window._adminMusicInit) { console.log('[manage_music] DOMContentLoaded ignored (already init)'); return; }
    window._adminMusicInit = true;
    console.log('[manage_music] DOMContentLoaded init');

    // Thêm mới Thể loại
    const addGenreForm = document.getElementById('addGenreForm');
    if (addGenreForm) {
        addGenreForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (addGenreForm.dataset.submitting === 'true') { console.warn('[manage_music] genre submit ignored (in-flight)'); return; }
            addGenreForm.dataset.submitting = 'true';
            const name = document.getElementById('add_genre_name').value.trim();
            const colorClass = document.getElementById('add_genre_color') ? document.getElementById('add_genre_color').value.trim() : '';
            const imageFile = document.getElementById('add_genre_image_file') ? document.getElementById('add_genre_image_file').files[0] : null;
            const formData = new FormData();
            formData.append('name', name);
            if (colorClass) formData.append('color_class', colorClass);
            if (imageFile) formData.append('image', imageFile);
            const token = getToken();
            try {
                const res = await fetch('/admin/api/genre', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token },
                    body: formData,
                    credentials: 'include'
                });
                const data = await res.json();
                if (res.ok) {
                    // Kiểm tra nếu đã có thể loại này trong danh sách thì không fetch lại
                    let existed = false;
                    if (window.allGenresCache && Array.isArray(window.allGenresCache)) {
                        existed = window.allGenresCache.some(g => g.name && g.name.trim().toLowerCase() === name.toLowerCase());
                    }
                    alert('Đã thêm thể loại thành công!');
                    if (!existed) fetchAllGenres();
                    addGenreForm.reset();
                } else {
                    alert(data.msg || 'Lỗi thêm thể loại');
                }
            } catch (err) {
                alert('Lỗi kết nối server');
            } finally {
                addGenreForm.dataset.submitting = 'false';
            }
        });
    }


    // Thêm mới Nghệ sĩ
    const addArtistForm = document.getElementById('addArtistForm');
    if (addArtistForm) {
        addArtistForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (addArtistForm.dataset.submitting === 'true') { console.warn('[manage_music] artist submit ignored (in-flight)'); return; }
            addArtistForm.dataset.submitting = 'true';
            const name = document.getElementById('add_artist_name').value.trim();
            const imageFile = document.getElementById('add_artist_image_file') ? document.getElementById('add_artist_image_file').files[0] : null;
            const formData = new FormData();
            formData.append('name', name);
            if (imageFile) formData.append('image', imageFile);
            const token = getToken();
            try {
                const res = await fetch('/admin/api/artist', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token },
                    body: formData,
                    credentials: 'include'
                });
                const data = await res.json();
                if (res.ok) {
                    // Kiểm tra nếu đã có nghệ sĩ này trong danh sách thì không fetch lại
                    let existed = false;
                    if (window.allArtistsCache && Array.isArray(window.allArtistsCache)) {
                        existed = window.allArtistsCache.some(a => a.name && a.name.trim().toLowerCase() === name.toLowerCase());
                    }
                    alert('Đã thêm nghệ sĩ thành công!');
                    if (!existed) fetchAllArtists();
                    addArtistForm.reset();
                } else {
                    alert(data.msg || 'Lỗi thêm nghệ sĩ');
                }
            } catch (err) {
                alert('Lỗi kết nối server');
            } finally {
                addArtistForm.dataset.submitting = 'false';
            }
        });
    }


    // Thêm mới Album
    const addAlbumForm = document.getElementById('addAlbumForm');
    if (addAlbumForm) {
        addAlbumForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (addAlbumForm.dataset.submitting === 'true') { console.warn('[manage_music] album submit ignored (in-flight)'); return; }
            addAlbumForm.dataset.submitting = 'true';
            const title = document.getElementById('add_album_title').value.trim();
            const artistId = document.getElementById('add_album_artist_id') ? document.getElementById('add_album_artist_id').value : '';
            const coverFile = document.getElementById('add_album_cover_file') ? document.getElementById('add_album_cover_file').files[0] : null;
            const formData = new FormData();
            formData.append('title', title);
            if (artistId) formData.append('artist_id', artistId);
            if (coverFile) formData.append('image', coverFile);
            const token = getToken();
            try {
                const res = await fetch('/admin/api/album', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token },
                    body: formData,
                    credentials: 'include'
                });
                const data = await res.json();
                if (res.ok) {
                    // Kiểm tra nếu đã có album này trong danh sách thì không fetch lại
                    let existed = false;
                    if (window.allAlbumsCache && Array.isArray(window.allAlbumsCache)) {
                        existed = window.allAlbumsCache.some(a => a.title && a.title.trim().toLowerCase() === title.toLowerCase());
                    }
                    alert('Đã thêm album thành công!');
                    if (!existed && typeof fetchAllAlbums === 'function') fetchAllAlbums();
                    addAlbumForm.reset();
                } else {
                    alert(data.msg || 'Lỗi thêm album');
                }
            } catch (err) {
                alert('Lỗi kết nối server');
            } finally {
                addAlbumForm.dataset.submitting = 'false';
            }
        });
    }
    
    // Event listeners cho nút Edit
    document.querySelectorAll('.edit-btn[data-genre-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const genreId = this.getAttribute('data-genre-id');
            if (genreId) openEditGenreModal(genreId);
        });
    });
    
    document.querySelectorAll('.edit-btn[data-artist-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const artistId = this.getAttribute('data-artist-id');
            if (artistId) openEditArtistModal(artistId);
        });
    });
    
    document.querySelectorAll('.edit-btn[data-album-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const albumId = this.getAttribute('data-album-id');
            if (albumId) openEditAlbumModal(albumId);
        });
    });
});
// Đảm bảo các hàm modal luôn có trên window (dùng cho onclick)
window.openModal = function(id) {
    var modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'block';
        modal.style.zIndex = 2000;
        if (modal.focus) modal.focus();
        if (modal.scrollIntoView) modal.scrollIntoView({behavior:'smooth',block:'center'});
    }
}
window.closeModal = function(id) {
    var modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}
// ====== TOÀN BỘ CRUD THỂ LOẠI & BÀI HÁT & EVENT DELEGATION ======

// Biến debounce cho tìm kiếm thể loại (phải khai báo global, chỉ khai báo 1 lần)
if (typeof window.genreSearchTimeout === 'undefined') {
    window.genreSearchTimeout = null;
}
if (typeof window.artistSearchTimeout === 'undefined') {
    window.artistSearchTimeout = null;
}
if (typeof window.albumSearchTimeout === 'undefined') {
    window.albumSearchTimeout = null;
}

// ====== TÌM KIẾM DỮ LIỆU ÂM NHẠC ======
// Hàm render danh sách bài hát (cần chỉnh lại selector cho đúng giao diện của bạn)
// image path normalization helper used across manage pages
function normalizeImgPath(imgPath, defaultImg='/static/images/default.png'){
    if(!imgPath) return defaultImg;
    imgPath = String(imgPath).trim();
    if(!imgPath || imgPath === 'None' || imgPath === 'null') return defaultImg;
    if(imgPath.startsWith('/static/')) return imgPath;
    if(imgPath.startsWith('static/')) return '/' + imgPath;
    if(imgPath.startsWith('/')) return '/static' + imgPath;
    return '/static/' + imgPath.replace(/^\/+/,'');
}

// Ensure song select options (artists, albums, genres) are populated.
async function fetchSongSelectOptions() {
    // If page already exposes loadOptions helper, prefer it (it may populate selects and do other setup)
    if (typeof loadOptions === 'function') {
        try { await loadOptions(); return; } catch(e) { console.warn('[manage_music] loadOptions() failed, falling back to manual fetch:', e); }
    }

    // Manual fetch fallback: fetch artists, albums, genres and populate selects
    try {
        // artists
        const artistsRes = await fetch('/admin/api/artist', { method: 'GET', headers: buildHeaders('application/json'), credentials: 'include' });
        const artists = artistsRes.ok ? await artistsRes.json() : [];
        const artistSelect = document.getElementById('song_artists');
        if (artistSelect) {
            artistSelect.innerHTML = '';
            artists.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.id;
                opt.textContent = a.name || ('Artist ' + a.id);
                artistSelect.appendChild(opt);
            });
        }

        // albums
        const albumsRes = await fetch('/admin/api/album', { method: 'GET', headers: buildHeaders('application/json'), credentials: 'include' });
        const albums = albumsRes.ok ? await albumsRes.json() : [];
        const albumSelect = document.getElementById('song_album');
        if (albumSelect) {
            albumSelect.innerHTML = '';
            const emptyOpt = document.createElement('option'); emptyOpt.value = ''; emptyOpt.textContent = '-- Không thuộc album nào --';
            albumSelect.appendChild(emptyOpt);
            albums.forEach(al => {
                const opt = document.createElement('option');
                opt.value = al.id; opt.textContent = al.title || ('Album ' + al.id);
                albumSelect.appendChild(opt);
            });
        }

        // genres
        const genresRes = await fetch('/admin/api/genre', { method: 'GET', headers: buildHeaders('application/json'), credentials: 'include' });
        const genres = genresRes.ok ? await genresRes.json() : [];
        const genreSelect = document.getElementById('song_genre');
        if (genreSelect) {
            genreSelect.innerHTML = '';
            genres.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g.id; opt.textContent = g.name || ('Genre ' + g.id);
                genreSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.warn('[manage_music] fetchSongSelectOptions failed:', err);
    }
}

function renderSongList(songs) {
    const container = document.getElementById('songs-container');
    if (!container) return;
    if (!songs || songs.length === 0) {
        container.innerHTML = '<p style="color:#888">Không tìm thấy bài hát phù hợp.</p>';
        return;
    }
    container.innerHTML = '';
    console.log('songs:', songs);
    songs.forEach(song => {
        const item = document.createElement('div');
        item.className = 'item-card';
        item.setAttribute('data-id', song.id);
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        item.style.background = 'rgba(255,255,255,0.18)';
        item.style.borderRadius = '8px';
        item.style.padding = '10px 16px';
        item.style.marginBottom = '10px';
        item.style.color = '#fff';
        const imgPath = normalizeImgPath(song.image_path, '/static/images/default.png');
        const canModify = !!(song.can_edit || song.can_delete);
        item.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="${imgPath}" alt="${song.title}" style="width:38px; height:38px; object-fit:cover; border-radius:8px;">
                <span style="font-size:17px;">${song.title}</span>
            </div>
            <div>
                ${canModify ? `
                <button type="button" class="edit-btn" data-song-id="${song.id}" style="background:transparent; border:none; color:#ffd700; font-size:18px; cursor:pointer;"><i class="fa fa-edit"></i></button>
                <button type="button" class="delete-btn" data-song-id="${song.id}" data-song-title="${song.title}" style="background:transparent; border:none; color:#ff4d4f; font-size:18px; cursor:pointer;"><i class="fa fa-trash"></i></button>
                `: ''}
            </div>
        `;
        container.appendChild(item);
    });
}

// ====== NGHỆ SĨ: Render và fetch ======
if (typeof window.allArtistsCache === 'undefined') {
    window.allArtistsCache = null;
}
async function searchArtistsRealtime(keyword) {
    const token = getToken();
    if (!keyword) {
        if (window.allArtistsCache) {
            renderArtistList(window.allArtistsCache);
        } else {
            await fetchAllArtists();
        }
        return;
    }
    try {
        const response = await fetch(`/admin/api/artist/search?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Không tìm thấy kết quả');
        const data = await response.json();
        let artistsArr = data.artists || [];
        renderArtistList(artistsArr);
    } catch (err) {
        renderArtistList([]);
    }
}

// ====== ALBUM: Render và fetch ======
if (typeof window.allAlbumsCache === 'undefined') {
    window.allAlbumsCache = null;
}
function renderAlbumList(albums) {
    const container = document.getElementById('albums-container');
    if (!container) return;
    if (!albums || albums.length === 0) {
        container.innerHTML = '<p style="color:#888">Không tìm thấy album phù hợp.</p>';
        return;
    }
    container.innerHTML = '';
    const defaultImg = '/static/images/default.png';
    albums.forEach(album => {
        const imgPath = normalizeImgPath(album.image_path || album.cover_image_path, defaultImg).replace(/\/static\/static\//g, '/static/');
        const item = document.createElement('div');
        item.className = 'item-card';
        item.setAttribute('data-id', album.id);
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        item.style.background = 'rgba(255,255,255,0.18)';
        item.style.borderRadius = '8px';
        item.style.padding = '10px 16px';
        item.style.marginBottom = '10px';
        item.style.color = '#fff';
        const canModify = !!(album.can_edit || album.can_delete);
        item.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="${imgPath}" alt="${album.title}" style="width:38px; height:38px; object-fit:cover; border-radius:8px;">
                <span style="font-size:17px;">${album.title}</span>
            </div>
            <div>
                ${canModify ? `
                <button type="button" class="edit-btn" data-album-id="${album.id}" style="background:transparent; border:none; color:#ffd700; font-size:18px; cursor:pointer;"><i class="fa fa-edit"></i></button>
                <button type="button" class="delete-btn" data-album-id="${album.id}" data-album-title="${album.title}" style="background:transparent; border:none; color:#ff4d4f; font-size:18px; cursor:pointer;"><i class="fa fa-trash"></i></button>
                `: ''}
            </div>
        `;
        container.appendChild(item);
    });
}
async function searchAlbumsRealtime(keyword) {
    const token = getToken();
    if (!keyword) {
        if (window.allAlbumsCache) {
            renderAlbumList(window.allAlbumsCache);
        } else {
            // Không có API fetchAllAlbums, chỉ clear list
            renderAlbumList([]);
        }
        return;
    }
    try {
        const response = await fetch(`/admin/api/album/search?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Không tìm thấy kết quả');
        const data = await response.json();
        let albumsArr = data.albums || [];
        renderAlbumList(albumsArr);
    } catch (err) {
        renderAlbumList([]);
    }
}
async function fetchAllArtists() {
    const token = getToken();
    try {
        console.log('[manage_music] fetchAllArtists called');
            const response = await fetch(`/admin/api/artist`, {
                method: 'GET',
                headers: buildHeaders('application/json'),
                credentials: 'include'
            });
        if (!response.ok) throw new Error('Không tìm thấy dữ liệu');
        const data = await response.json();
        let artistsArr = Array.isArray(data) ? data : (data.artists || []);
        console.log('API /admin/api/artist trả về (raw):', artistsArr);
        // Deduplicate theo id + name
        const seen = new Set();
        artistsArr = artistsArr.filter(a => {
            const key = (a.id || 'x') + '|' + (a.name || '').toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
        console.log('API /admin/api/artist sau khi lọc trùng:', artistsArr);
        window.allArtistsCache = artistsArr;
        renderArtistList(artistsArr);
    } catch (err) {
        renderArtistList([]);
    }
}

function renderArtistList(artists) {
    const container = document.getElementById('artists-container');
    if (!container) return;
    if (!artists || artists.length === 0) {
        container.innerHTML = '<p style="color:#888">Không tìm thấy nghệ sĩ phù hợp.</p>';
        return;
    }
    container.innerHTML = '';
    const defaultImg = '/static/images/default.png';
    // Deduplicate lần nữa phòng trường hợp truyền artists bên ngoài chưa lọc
    const seen = new Set();
    artists.forEach(artist => {
        const key = (artist.id || 'x') + '|' + (artist.name || '').toLowerCase();
        if (seen.has(key)) return;
        seen.add(key);
        console.log('artist.image_path:', artist.image_path, artist);
        const item = document.createElement('div');
        item.className = 'item-card';
        item.setAttribute('data-id', artist.id);
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        item.style.background = 'rgba(255,255,255,0.18)';
        item.style.borderRadius = '8px';
        item.style.padding = '10px 16px';
        item.style.marginBottom = '10px';
        item.style.color = '#fff';
    let imgPath = normalizeImgPath(artist.image_path, defaultImg);
    // Loại bỏ lặp /static/static/
    imgPath = imgPath.replace(/\/static\/static\//g, '/static/');
        const canModify = !!(artist.can_edit || artist.can_delete);
        item.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="${imgPath}" alt="${artist.name}" style="width:38px; height:38px; object-fit:cover; border-radius:8px;">
                <span style="font-size:17px;">${artist.name}</span>
            </div>
            <div>
                ${canModify ? `
                <button type="button" class="edit-btn" data-artist-id="${artist.id}" style="background:transparent; border:none; color:#ffd700; font-size:18px; cursor:pointer;"><i class="fa fa-edit"></i></button>
                <button type="button" class="delete-btn" data-artist-id="${artist.id}" data-artist-name="${artist.name}" style="background:transparent; border:none; color:#ff4d4f; font-size:18px; cursor:pointer;"><i class="fa fa-trash"></i></button>
                `: ''}
            </div>
        `;
        container.appendChild(item);
    });
}


// ====== TÌM KIẾM THỂ LOẠI REALTIME (AUTOCOMPLETE) ======
if (typeof window.allGenresCache === 'undefined') {
    window.allGenresCache = null;
}
async function fetchAllGenres() {
    const token = getToken();
    try {
        // Debug: auth and header state before fetch
        try {
            const cookieHas = (typeof document !== 'undefined') && (document.cookie.split('; ').find(row => row.startsWith('access_token=')));
            const localToken = (window.getToken && typeof window.getToken === 'function') ? window.getToken() : localStorage.getItem('access_token');
            const debugHeaders = buildHeaders('application/json');
            console.debug('[manage_music][debug] about to fetchAllGenres: cookieHas=', !!cookieHas, 'localToken=', !!localToken, 'headers=', debugHeaders);
        } catch (de) { console.debug('[manage_music][debug] pre-fetch debug failed', de); }

        const response = await fetch(`/admin/api/genre`, {
            method: 'GET',
            headers: buildHeaders('application/json'),
            credentials: 'include'
        });

        // Debug: response status and body for diagnosis
        try {
            const text = await response.clone().text();
            console.debug('[manage_music][debug] fetchAllGenres response status=', response.status, 'body=', text);
        } catch (de) { console.debug('[manage_music][debug] post-fetch debug failed', de); }

        if (!response.ok) {
            console.warn('[manage_music] fetchAllGenres got non-ok response:', response.status);
            throw new Error('Không tìm thấy dữ liệu');
        }
        const data = await response.json();
        let genresArr = Array.isArray(data) ? data : (data.genres || []);
        console.log('API /admin/api/genre trả về:', genresArr);
        window.allGenresCache = JSON.parse(JSON.stringify(genresArr)); // Lưu dữ liệu gốc
        renderGenreList(genresArr);
    } catch (err) {
        console.error('[manage_music] fetchAllGenres error:', err);
        renderGenreList([]);
    }
}
function renderGenreList(genres) {
    const container = document.getElementById('genres-container');
    if (!container) return;
    if (!genres || genres.length === 0) {
        container.innerHTML = '<p style="color:#888">Không tìm thấy thể loại phù hợp.</p>';
        return;
    }
    container.innerHTML = '';
    const defaultImg = '/static/images/default.png';
    genres.forEach(genre => {
        console.log('genre.image_path:', genre.image_path, genre);
        const item = document.createElement('div');
        item.className = 'item-card';
        item.setAttribute('data-id', genre.id);
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        item.style.background = 'rgba(255,255,255,0.18)';
        item.style.borderRadius = '8px';
        item.style.padding = '10px 16px';
        item.style.marginBottom = '10px';
        item.style.color = '#fff';
    let imgPath = normalizeImgPath(genre.image_path, defaultImg);
    // Loại bỏ lặp /static/static/
    imgPath = imgPath.replace(/\/static\/static\//g, '/static/');
        const canModify = !!(genre.can_edit || genre.can_delete);
        item.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="${imgPath}" alt="${genre.name}" style="width:38px; height:38px; object-fit:cover; border-radius:8px; background:#eee;">
                <span style="font-size:17px;">${genre.name}</span>
            </div>
            <div>
                ${canModify ? `
                <button type="button" class="edit-btn" data-genre-id="${genre.id}" style="background:transparent; border:none; color:#ffd700; font-size:18px; cursor:pointer;"><i class="fa fa-edit"></i></button>
                <button type="button" class="delete-btn" data-genre-id="${genre.id}" data-genre-name="${genre.name}" style="background:transparent; border:none; color:#ff4d4f; font-size:18px; cursor:pointer;"><i class="fa fa-trash"></i></button>
                `: ''}
            </div>
        `;
        container.appendChild(item);
    });
}

async function searchGenresRealtime(keyword) {
    const token = getToken();
    if (!keyword) {
        // Luôn dùng cache dữ liệu gốc nếu có
        if (window.allGenresCache) {
            renderGenreList(window.allGenresCache);
        } else {
            await fetchAllGenres();
        }
        return;
    }
    try {
        const response = await fetch(`/admin/api/genre/search?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Không tìm thấy kết quả');
        const data = await response.json();
        let genresArr = data.genres || [];
        renderGenreList(genresArr);
    } catch (err) {
        renderGenreList([]);
    }
}

if (typeof window.allSongsCache === 'undefined') {
    window.allSongsCache = null;
}
async function fetchAllSongs() {
    const token = getToken();
    try {
        const response = await fetch(`/admin/api/song`, {
            method: 'GET',
            headers: buildHeaders('application/json'),
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Không tìm thấy dữ liệu');
        const data = await response.json();
        let songsArr = Array.isArray(data) ? data : (data.songs || []);
        window.allSongsCache = JSON.parse(JSON.stringify(songsArr));
        renderSongList(songsArr);
    } catch (err) {
        renderSongList([]);
    }
}
async function searchSongs(keyword) {
    const token = getToken();
    if (!keyword) {
        if (window.allSongsCache) {
            renderSongList(window.allSongsCache);
        } else {
            await fetchAllSongs();
        }
        return;
    }
    try {
        const response = await fetch(`/admin/api/song/search?keyword=${encodeURIComponent(keyword)}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Không tìm thấy kết quả');
        const data = await response.json();
        renderSongList(data.songs || []);
    } catch (err) {
        renderSongList([]);
    }
}

// Gắn sự kiện cho ô input và nút tìm kiếm (chỉ chạy khi DOM đã sẵn sàng)
document.addEventListener('DOMContentLoaded', function() {
    // Load dữ liệu đầy đủ ban đầu
    fetchAllGenres();
    fetchAllSongs();
    fetchAllArtists();
    // Không có fetchAllAlbums, album chỉ search realtime
    // Tìm kiếm thể loại realtime
    const genreSearchInput = document.getElementById('search-genre-input');
    if (genreSearchInput) {
        genreSearchInput.addEventListener('input', function() {
            const keyword = genreSearchInput.value.trim();
            clearTimeout(genreSearchTimeout);
            genreSearchTimeout = setTimeout(() => {
                searchGenresRealtime(keyword);
            }, 200);
        });
    }
    // Tìm kiếm nghệ sĩ realtime
    const artistSearchInput = document.getElementById('search-artist-input');
    if (artistSearchInput) {
        artistSearchInput.addEventListener('input', function() {
            const keyword = artistSearchInput.value.trim();
            clearTimeout(window.artistSearchTimeout);
            window.artistSearchTimeout = setTimeout(() => {
                searchArtistsRealtime(keyword);
            }, 200);
        });
    }
    // Tìm kiếm album realtime
    const albumSearchInput = document.getElementById('search-album-input');
    if (albumSearchInput) {
        albumSearchInput.addEventListener('input', function() {
            const keyword = albumSearchInput.value.trim();
            clearTimeout(window.albumSearchTimeout);
            window.albumSearchTimeout = setTimeout(() => {
                searchAlbumsRealtime(keyword);
            }, 200);
        });
    }
    // Tìm kiếm bài hát realtime
    const searchInput = document.getElementById('search-song-input');
    const searchBtn = document.getElementById('search-song-btn');
    if (searchInput && searchBtn) {
        searchBtn.addEventListener('click', function() {
            const keyword = searchInput.value.trim();
            searchSongs(keyword);
        });
        searchInput.addEventListener('input', function() {
            const keyword = searchInput.value.trim();
            clearTimeout(window.songSearchTimeout);
            window.songSearchTimeout = setTimeout(() => {
                searchSongs(keyword);
            }, 200);
        });
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const keyword = searchInput.value.trim();
                searchSongs(keyword);
            }
        });
    }
});

// Helper function to get token
// Expose getToken globally if not already present (other scripts rely on it)
if (typeof window.getToken !== 'function') {
    window.getToken = function() { return localStorage.getItem('access_token'); };
}
// Quản lý các request đang xử lý để tránh gửi lặp
const inFlightOps = new Set();
function beginOp(key){ if(inFlightOps.has(key)) return false; inFlightOps.add(key); return true; }
function endOp(key){ inFlightOps.delete(key); }

function showAlert(message, type) {
    const alert = document.getElementById('alert');
    if (!alert) return;
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.display = 'block';
    setTimeout(() => {
        alert.style.display = 'none';
    }, 3000);
}

// Xóa thể loại
async function deleteGenre(id, name) {
    const opKey = 'del_genre_' + id;
    if(!beginOp(opKey)){ console.warn('[manage_music] deleteGenre ignored duplicate'); return; }
    try {
        if (!confirm(`Bạn có chắc chắn muốn xóa thể loại "${name}"?`)) return;
        const response = await fetch(`/admin/api/genre/${id}`, { method: 'DELETE', headers:{ 'Authorization': `Bearer ${getToken()}` }});
        let result = {};
        try { result = await response.json(); } catch(e){ console.warn('parse deleteGenre response fail'); }
        if (response.ok || response.status === 404) {
            showAlert('Đã xử lý xóa thể loại!', 'success');
            await fetchAllGenres();
        } else {
            showAlert(result.msg || 'Lỗi khi xóa thể loại', 'error');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'error');
    } finally { endOp(opKey); }
}

// Open Edit Genre Modal
async function openEditGenreModal(genreId) {
    console.log('[openEditGenreModal] Called with genreId:', genreId);
    const modal = document.getElementById('editGenreModal');
    console.log('[openEditGenreModal] Modal element:', modal);
    if (!modal) {
        console.error('editGenreModal element not found');
        alert('Không tìm thấy modal chỉnh sửa');
        return;
    }
    const token = getToken();
    try {
        const response = await fetch(`/admin/api/genre/${genreId}`, {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.msg || `HTTP ${response.status}`);
        }
        const genre = await response.json();
        
        // Set values
        const idField = document.getElementById('edit_genre_id');
        const nameField = document.getElementById('edit_genre_name');
        const colorField = document.getElementById('edit_genre_color');
        const imageField = document.getElementById('edit_genre_image_file');
        
        if (!idField || !nameField || !imageField) {
            throw new Error('Thiếu các trường input trong form');
        }
        
        idField.value = genre.id;
        nameField.value = genre.name || '';
        if (colorField) {
            colorField.value = genre.color_class || '';
        }
        // Bỏ qua preview ảnh nếu element không tồn tại
        const imagePreview = document.getElementById('edit-genre-image-preview');
        if (imagePreview) {
            const defaultImg = '/static/images/default.png';
            imagePreview.innerHTML = `<img src="${normalizeImgPath(genre.image_path, defaultImg)}" alt="${genre.name}" style="max-width: 200px; border-radius: 8px;">`;
        }
        imageField.value = '';
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading genre:', error);
        alert('Không thể tải thông tin thể loại: ' + error.message);
    }
}

// Handle Edit Genre Form Submit
if (document.getElementById('editGenreForm')) {
    document.getElementById('editGenreForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const genreId = document.getElementById('edit_genre_id').value;
        const name = document.getElementById('edit_genre_name').value;
        const colorClass = document.getElementById('edit_genre_color').value;
        const imageFile = document.getElementById('edit_genre_image_file').files[0];
        const formData = new FormData();
        formData.append('name', name);
        if (colorClass) formData.append('color_class', colorClass);
        if (imageFile) formData.append('image', imageFile);
        const token = getToken();
        try {
            const response = await fetch(`/admin/api/genre/${genreId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': 'Bearer ' + token
                },
                body: formData,
                credentials: 'include'
            });
            const data = await response.json();
            if (response.ok) {
                alert('Đã cập nhật thể loại thành công!');
                location.reload();
            } else {
                alert('Lỗi: ' + (data.msg || data.error || 'Không thể cập nhật'));
            }
        } catch (error) {
            alert('Lỗi kết nối');
        }
    });
}

// Xóa bài hát
function deleteSong(id, title){
    const opKey = 'del_song_' + id;
    if(!beginOp(opKey)){ console.warn('[manage_music] deleteSong ignored duplicate'); return; }
    if(!confirm('Xóa bài hát ' + title + ' ?')) { endOp(opKey); return; }
    const token = getToken();
    fetch('/admin/api/song/' + id, { method:'DELETE', headers:{ 'Authorization': 'Bearer ' + token, 'Content-Type':'application/json' }, credentials:'include' })
        .then(async r => { let data={}; try{ data=await r.json(); }catch{} return {r,data}; })
        .then(({r,data})=>{
            if(r.ok || r.status===404){ alert(data.msg || 'Đã xử lý xóa bài hát'); location.reload(); }
            else { alert('Không xóa được: ' + (data.error || data.msg || JSON.stringify(data))); }
        })
        .catch(err=>{ console.error(err); alert('Lỗi kết nối'); })
        .finally(()=> endOp(opKey));
}

// Xóa album (idempotent phía server)
function deleteAlbum(id, title){
    const opKey = 'del_album_' + id;
    if(!beginOp(opKey)){ console.warn('[manage_music] deleteAlbum ignored duplicate'); return; }
    if(!confirm('Xóa album "' + title + '" ?')) { endOp(opKey); return; }
    const token = getToken();
    fetch('/admin/api/album/' + id, { method:'DELETE', headers:{ 'Authorization': 'Bearer ' + token }, credentials:'include' })
        .then(async r => { let data={}; try{ data=await r.json(); }catch{} return {r,data}; })
        .then(({r,data}) => {
            if(r.ok || r.status===404){ alert(data.msg || 'Đã xử lý xóa album'); /* Nếu có cache albums thì cập nhật */
                if(window.allAlbumsCache){ window.allAlbumsCache = window.allAlbumsCache.filter(a => a.id !== id); renderAlbumList(window.allAlbumsCache); }
            } else {
                alert(data.msg || 'Không xóa được album');
            }
        })
        .catch(err => { console.error(err); alert('Lỗi kết nối'); })
        .finally(()=> endOp(opKey));
}

// SPA-aware loader: ensure admin manage-music page initializes when navigated via SPA
function ensureManageMusicLoaded() {
    try {
        // Check if current DOM contains manage music container
        const manageContainer = document.querySelector('.manage-music-container') || document.getElementById('manage-music-container');
        if (!manageContainer) return; // not on the manage-music page
        // Only run initial fetches once per page appearance
        if (manageContainer.dataset.managedLoaded === 'true') return;
        manageContainer.dataset.managedLoaded = 'true';
        console.log('[manage_music] SPA loader detected manage-music page, triggering initial fetches');
        // Trigger the same initial loaders as DOMContentLoaded path
        if (typeof fetchAllGenres === 'function') fetchAllGenres();
        if (typeof fetchAllSongs === 'function') fetchAllSongs();
        if (typeof fetchAllArtists === 'function') fetchAllArtists();
    } catch (err) {
        console.warn('[manage_music] ensureManageMusicLoaded error', err);
    }
}

// Ensure we attach SPA listeners only once
if (!window._adminManageMusicSPAInit) {
    window._adminManageMusicSPAInit = true;
    // SPA navigation event used by router when swapping page content
    window.addEventListener('spa-navigated', function() {
        setTimeout(ensureManageMusicLoaded, 30);
    });
    // browser navigation can also trigger popstate
    window.addEventListener('popstate', function() {
        setTimeout(ensureManageMusicLoaded, 30);
    });
    // Delegated click on the admin manage music link (works for normal clicks in SPA nav)
    document.addEventListener('click', function(e) {
        const a = e.target.closest && e.target.closest('#admin-manage-music-link');
        if (a) {
            // allow router to handle navigation then run loader
            setTimeout(ensureManageMusicLoaded, 50);
        }
    });
}

// Open Edit Song Modal
async function openEditSongModal(songId) {
    // Try several common modal IDs used across templates to be robust
    const modal = document.getElementById('song-modal') || document.getElementById('edit-song-modal') || document.getElementById('editSongModal') || document.querySelector('.song-modal');
    if (!modal) { console.warn('[manage_music] openEditSongModal: modal element not found (tried song-modal, edit-song-modal, editSongModal, .song-modal)'); alert('Lỗi: Không tìm thấy modal sửa bài hát'); return; }
    try {
        // Prefer cookie auth; buildHeaders will attach Authorization header only when no cookie token exists.
        const response = await fetch(`/admin/api/song/${songId}`, {
            method: 'GET',
            headers: buildHeaders('application/json'),
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to fetch song details: ' + response.status);
        const song = await response.json();

        // Ensure select options (artists, albums, genres) are loaded first
        try {
            await fetchSongSelectOptions();
        } catch (e) {
            console.warn('[manage_music] fetchSongSelectOptions failed:', e);
        }

        // Populate fields that exist in the shared song modal
        document.getElementById('song_id').value = song.id;
        document.getElementById('song_title').value = song.title || '';
        document.getElementById('song_album').value = song.album_id || '';
        document.getElementById('song_genre').value = song.genre_id || '';

        // Select artists in the multi-select
        const artistSelect = document.getElementById('song_artists');
        if (artistSelect && song.artists) {
            Array.from(artistSelect.options).forEach(opt => {
                opt.selected = song.artists.includes(parseInt(opt.value));
            });
            // Also show tags if helper exists
            try { if (typeof showEditArtistTags === 'function') showEditArtistTags(song.artists.map(a => a.name)); } catch(e){}
        }

        // Show image preview in the shared preview area
        const imagePreview = document.getElementById('song-image-preview');
        const defaultImg = '/static/images/default.png';
        if (imagePreview) {
            if (song.image_path) {
                imagePreview.innerHTML = `<img src="${normalizeImgPath(song.image_path, defaultImg)}" alt="${song.title}" style="max-width:120px;max-height:120px;border-radius:8px;">`;
            } else {
                imagePreview.innerHTML = '<span style="color:#aaa;">Chưa có ảnh</span>';
            }
        }

        // Clear file input (if present)
        const imageFileInput = document.getElementById('song_image_file');
        if (imageFileInput) imageFileInput.value = '';
        modal.style.display = 'block';
    } catch (error) {
        alert('Không thể tải thông tin bài hát: ' + error.message);
    }
}

// Expose shared implementation for other scripts that might fallback
try { window._sharedOpenEditSongModal = openEditSongModal; } catch(e) { /* ignore */ }

function showEditArtistTags(artistNames) {
    const tagsContainer = document.getElementById('edit-artist-tags');
    tagsContainer.innerHTML = '';
    artistNames.forEach(name => {
        const tag = document.createElement('span');
        tag.className = 'artist-tag valid';
        tag.innerHTML = `${name} <span class="tag-icon">✅</span>`;
        tagsContainer.appendChild(tag);
    });
}

// Event delegation for Edit/Delete buttons (thể loại & bài hát, nghệ sĩ, album)
document.addEventListener('DOMContentLoaded', function() {
    if (window._adminMusicDelegationInit) return; // tránh gắn nhiều lần
    window._adminMusicDelegationInit = true;
    document.body.addEventListener('click', function(e) {
        let target = e.target;
        if (target.tagName === 'I') target = target.parentElement;
        // Edit handlers
        if (target && target.classList && target.classList.contains('edit-btn')) {
            const songId = target.getAttribute('data-song-id');
            if (songId) { e.preventDefault(); e.stopPropagation(); openEditSongModal(parseInt(songId)); return; }
            const genreId = target.getAttribute('data-genre-id');
            if (genreId) { e.preventDefault(); e.stopPropagation(); openEditGenreModal(parseInt(genreId)); return; }
            const artistId = target.getAttribute('data-artist-id');
            if (artistId) { e.preventDefault(); e.stopPropagation(); openEditArtistModal(parseInt(artistId)); return; }
            const albumId = target.getAttribute('data-album-id');
            if (albumId) { e.preventDefault(); e.stopPropagation(); openEditAlbumModal(parseInt(albumId)); return; }
        }
        // Delete handlers
        if (target && target.classList && target.classList.contains('delete-btn')) {
            // Disable button ngay lập tức để tránh double click / bubble
            if (!target.dataset.processing) {
                target.dataset.processing = 'true';
                target.style.opacity = '0.5';
            } else {
                console.warn('[manage_music] Bỏ qua delete do đang xử lý');
                return;
            }
            const songId = target.getAttribute('data-song-id');
            const songTitle = target.getAttribute('data-song-title');
            if (songId) { e.preventDefault(); e.stopPropagation(); deleteSong(parseInt(songId), songTitle); return; }
            const genreId = target.getAttribute('data-genre-id');
            const genreName = target.getAttribute('data-genre-name');
            if (genreId) { e.preventDefault(); e.stopPropagation(); deleteGenre(parseInt(genreId), genreName); return; }
            const artistId = target.getAttribute('data-artist-id');
            const artistName = target.getAttribute('data-artist-name');
            if (artistId) { e.preventDefault(); e.stopPropagation(); deleteArtist(parseInt(artistId), artistName); return; }
            const albumId = target.getAttribute('data-album-id');
            const albumTitle = target.getAttribute('data-album-title');
            if (albumId) { e.preventDefault(); e.stopPropagation(); deleteAlbum(parseInt(albumId), albumTitle); return; }
            // Nếu không khớp gì thì restore
            target.dataset.processing = '';
            target.style.opacity = '';
        }
    });
});
// Quản lý modal sửa nghệ sĩ

async function openEditArtistModal(id) {
    // Lấy chi tiết nghệ sĩ từ API
    const token = localStorage.getItem('access_token');
    const res = await fetch(`/admin/api/artist/${id}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        credentials: 'include'
    });
    if (!res.ok) {
        alert('Không lấy được thông tin nghệ sĩ');
        return;
    }
    const data = await res.json();
    document.getElementById('edit_artist_id').value = data.id;
    document.getElementById('edit_artist_name').value = data.name;
    const preview = document.getElementById('edit-artist-image-preview');
    if (preview) {
        const defaultImg = '/static/images/default.png';
        preview.innerHTML = `<img src="${normalizeImgPath(data.image_path, defaultImg)}" alt="Ảnh nghệ sĩ" style="max-width:120px;max-height:120px;border-radius:8px;">`;
    }
    document.getElementById('edit_artist_image_file').value = '';
    document.getElementById('editArtistModal').style.display = 'block';
}

// Quản lý modal sửa album

async function openEditAlbumModal(id) {
    // Lấy chi tiết album từ API
    const token = localStorage.getItem('access_token');
    const res = await fetch(`/admin/api/album/${id}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        credentials: 'include'
    });
    if (!res.ok) {
        alert('Không lấy được thông tin album');
        return;
    }
    const data = await res.json();
    document.getElementById('edit_album_id').value = data.id;
    document.getElementById('edit_album_title').value = data.title;
    document.getElementById('edit_album_artist_id').value = data.artist_id || '';
    const preview = document.getElementById('edit-album-image-preview');
    if (preview) {
        const defaultImg = '/static/images/default.png';
        preview.innerHTML = `<img src="${normalizeImgPath(data.cover_image_path, defaultImg)}" alt="Ảnh bìa album" style="max-width:120px;max-height:120px;border-radius:8px;">`;
    }
    document.getElementById('edit_album_cover_file').value = '';
    document.getElementById('editAlbumModal').style.display = 'block';
}

// Đóng modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Đóng modal khi click ra ngoài
window.onclick = function(event) {
    ['editArtistModal','editAlbumModal'].forEach(function(id) {
        var modal = document.getElementById(id);
        if (modal && event.target === modal) modal.style.display = 'none';
    });
};

// Sửa nghệ sĩ
if (document.getElementById('editArtistForm')) {
    document.getElementById('editArtistForm').onsubmit = async function(e) {
        e.preventDefault();
        const id = document.getElementById('edit_artist_id').value;
        const name = document.getElementById('edit_artist_name').value;
        const imageFile = document.getElementById('edit_artist_image_file').files[0];
        const formData = new FormData();
        formData.append('name', name);
        if (imageFile) formData.append('image', imageFile);
        const token = localStorage.getItem('access_token_cookie');
        try {
            const res = await fetch(`/admin/api/artist/${id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
                credentials: 'include'
            });
            if (res.ok) {
                alert('Cập nhật nghệ sĩ thành công!');
                location.reload();
            } else {
                const data = await res.json();
                alert(data.msg || 'Lỗi cập nhật nghệ sĩ');
            }
        } catch (err) {
            alert('Lỗi kết nối server');
        }
    };
}

// Sửa album
if (document.getElementById('editAlbumForm')) {
    document.getElementById('editAlbumForm').onsubmit = async function(e) {
        e.preventDefault();
        const id = document.getElementById('edit_album_id').value;
        const title = document.getElementById('edit_album_title').value;
        const artistId = document.getElementById('edit_album_artist_id').value;
        const coverFile = document.getElementById('edit_album_cover_file').files[0];
        const formData = new FormData();
        formData.append('title', title);
        if (artistId) formData.append('artist_id', artistId);
        if (coverFile) formData.append('image', coverFile);
        const token = localStorage.getItem('access_token_cookie');
        try {
            const res = await fetch(`/admin/api/album/${id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
                credentials: 'include'
            });
            if (res.ok) {
                alert('Cập nhật album thành công!');
                location.reload();
            } else {
                const data = await res.json();
                alert(data.msg || 'Lỗi cập nhật album');
            }
        } catch (err) {
            alert('Lỗi kết nối server');
        }
    };
}

// Helper function to close popup modals
window.closePopupModal = function() {
    // Try to close any open modal
    const modals = document.querySelectorAll('.modal[style*="display: block"], .modal[style*="display:block"]');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
};

})(); // end scoped module IIFE
} // end else block for _adminMusicScriptOnce check
