// Chức năng tìm kiếm toàn cục
(function() {
    const searchInput = document.getElementById('global-search-input');
    const resultsDropdown = document.getElementById('search-results');
    
    if (!searchInput || !resultsDropdown) return;

    let debounceTimer = null;
    let currentQuery = '';

    // Debounce search để tránh spam API
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (debounceTimer) clearTimeout(debounceTimer);
        
        if (query.length < 2) {
            hideResults();
            return;
        }
        
        debounceTimer = setTimeout(() => {
            performSearch(query);
        }, 300);
    });

    // Ẩn kết quả khi click bên ngoài
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
            hideResults();
        }
    });

    // Hiện lại kết quả khi focus vào input (nếu đã có kết quả)
    searchInput.addEventListener('focus', function() {
        if (resultsDropdown.innerHTML && currentQuery === searchInput.value.trim()) {
            resultsDropdown.style.display = 'block';
        }
    });

    function performSearch(query) {
        currentQuery = query;
        
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                displayResults(data);
            })
            .catch(err => {
                console.error('Search error:', err);
                hideResults();
            });
    }

    function displayResults(data) {
        const { songs, artists, albums, genres, users } = data;
        
        // Kiểm tra có kết quả không
        const totalResults = songs.length + artists.length + albums.length + genres.length + (users ? users.length : 0);
        if (totalResults === 0) {
            resultsDropdown.innerHTML = '<div class="search-empty">Không tìm thấy kết quả</div>';
            resultsDropdown.style.display = 'block';
            return;
        }

        let html = '';

        // Bài hát
        if (songs.length > 0) {
            html += '<div class="search-category"><div class="search-category-title">🎵 Bài hát</div>';
            songs.forEach(song => {
                const imagePath = song.mp3_path ? song.mp3_path.replace('.mp3', '.jpg') : '/static/images/default-song.jpg';
                html += `
                    <div class="search-item" data-type="song" data-id="${song.id}" data-mp3="${song.mp3_path || ''}" data-title="${escapeHtml(song.title)}" data-artist="${escapeHtml(song.artist_name)}">
                        <div class="search-item-content">
                            <div class="search-item-title">${escapeHtml(song.title)}</div>
                            <div class="search-item-subtitle">${escapeHtml(song.artist_name || 'Unknown')}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Nghệ sĩ
        if (artists.length > 0) {
            html += '<div class="search-category"><div class="search-category-title">👤 Nghệ sĩ</div>';
            artists.forEach(artist => {
                html += `
                    <div class="search-item" data-type="artist" data-id="${artist.id}">
                        <div class="search-item-content">
                            <div class="search-item-title">${escapeHtml(artist.name)}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Album
        if (albums.length > 0) {
            html += '<div class="search-category"><div class="search-category-title">💿 Album</div>';
            albums.forEach(album => {
                html += `
                    <div class="search-item" data-type="album" data-id="${album.id}">
                        <div class="search-item-content">
                            <div class="search-item-title">${escapeHtml(album.title)}</div>
                            <div class="search-item-subtitle">${escapeHtml(album.artist_name || 'Unknown')}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Thể loại
        if (genres.length > 0) {
            html += '<div class="search-category"><div class="search-category-title">🎸 Thể loại</div>';
            genres.forEach(genre => {
                html += `
                    <div class="search-item" data-type="genre" data-id="${genre.id}">
                        <div class="search-item-content">
                            <div class="search-item-title">${escapeHtml(genre.name)}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Người dùng
        if (users && users.length > 0) {
            html += '<div class="search-category"><div class="search-category-title">👥 Người dùng</div>';
            users.forEach(user => {
                const avatarPath = user.avatar ? `/static/${user.avatar}` : '/static/images/default.jpg';
                html += `
                    <div class="search-item" data-type="user" data-id="${user.id}">
                        <img src="${avatarPath}" alt="${escapeHtml(user.username)}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;margin-right:12px;">
                        <div class="search-item-content">
                            <div class="search-item-title">${escapeHtml(user.username)}</div>
                            <div class="search-item-subtitle">${user.role === 'admin' ? 'Quản trị viên' : user.role === 'uploader' ? 'Người tải lên' : 'Người dùng'}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        resultsDropdown.innerHTML = html;
        resultsDropdown.style.display = 'block';

        // Gắn sự kiện click
        bindResultClicks();
    }

    function bindResultClicks() {
        const items = resultsDropdown.querySelectorAll('.search-item');
        items.forEach(item => {
            item.addEventListener('click', function() {
                const type = this.dataset.type;
                const id = this.dataset.id;

                if (type === 'song') {
                    // Chuyển sang trang chi tiết bài hát
                    window.location.href = `/song/${id}`;
                } else if (type === 'artist') {
                    window.location.href = `/artist/${id}`;
                } else if (type === 'album') {
                    window.location.href = `/album/${id}`;
                } else if (type === 'genre') {
                    window.location.href = `/genre/${id}`;
                } else if (type === 'user') {
                    window.location.href = `/user/${id}`;
                }

                hideResults();
                searchInput.value = '';
            });
        });
    }

    function hideResults() {
        resultsDropdown.style.display = 'none';
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
