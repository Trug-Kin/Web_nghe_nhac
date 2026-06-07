// Xử lý tương tác like và comment
(function() {
    'use strict';

    // ==================== LIKE FUNCTIONALITY ====================
    
    /**
     * Toggle like/unlike cho bài hát
     */
    window.toggleLike = async function(songId, buttonElement) {
        console.log('[toggleLike] Called with songId:', songId);
        
    const token = localStorage.getItem('access_token');
        console.log('[toggleLike] Token:', token ? 'exists' : 'missing');
        
        if (!token) {
            showToast('Vui lòng đăng nhập để thích bài hát', 'warning');
            return;
        }

        try {
            console.log('[toggleLike] Sending POST to /api/song/' + songId + '/like');
            const response = await fetch(`/api/song/${songId}/like`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('[toggleLike] Response status:', response.status);
            const data = await response.json();
            console.log('[toggleLike] Response data:', data);

            if (response.ok) {
                // Cập nhật UI
                updateLikeButton(buttonElement, data.liked, data.like_count);
                showToast(data.msg, 'success');
            } else {
                showToast(data.msg || 'Có lỗi xảy ra', 'error');
            }
        } catch (error) {
            console.error('[toggleLike] Error:', error);
            showToast('Không thể kết nối server', 'error');
        }
    };

    /**
     * Cập nhật trạng thái nút like
     */
    function updateLikeButton(button, liked, count) {
        const icon = button.querySelector('.like-icon');
        const countSpan = button.querySelector('.like-count');

        if (liked) {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
            icon.style.color = '#ff4081';
        } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
            icon.style.color = '#999';
        }

        if (countSpan) {
            countSpan.textContent = count;
        }
    }

    /**
     * Load like status cho bài hát
     */
    window.loadLikeStatus = async function(songId, containerElement) {
        try {
            const response = await fetch(`/api/song/${songId}/likes`);
            const data = await response.json();

            if (response.ok) {
                const button = containerElement.querySelector('.like-button');
                if (button) {
                    updateLikeButton(button, data.liked, data.like_count);
                }
            }
        } catch (error) {
            console.error('Error loading like status:', error);
        }
    };

    // ==================== COMMENT FUNCTIONALITY ====================

    /**
     * Load comments cho bài hát
     */
    window.loadComments = async function(songId, containerElement) {
        try {
            const response = await fetch(`/api/song/${songId}/comments`);
            const data = await response.json();

            if (response.ok) {
                renderComments(data.comments, containerElement, songId);
            } else {
                containerElement.innerHTML = '<p class="error-msg">Không thể tải bình luận</p>';
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            containerElement.innerHTML = '<p class="error-msg">Lỗi kết nối server</p>';
        }
    };

    /**
     * Render danh sách comments
     */
    function renderComments(comments, container, songId) {
        if (!comments || comments.length === 0) {
            container.innerHTML = '<p class="no-comments">Chưa có bình luận nào. Hãy là người đầu tiên!</p>';
            return;
        }

        let html = '<div class="comments-list">';
        comments.forEach(comment => {
            const currentUserId = getCurrentUserId();
            const isOwner = currentUserId && currentUserId === comment.user_id;
            const canDelete = isOwner || isAdmin();
            // Dùng avatar nếu có, fallback ảnh mặc định
            const avatarUrl = comment.avatar_url || 'images/default.jpg';
            const fullAvatarUrl = '/static/' + avatarUrl.replace(/^\/+/,'');
            html += `
                <div class="comment-item" data-comment-id="${comment.id}">
                    <div class="comment-header" style="display:flex;align-items:center;gap:10px;">
                        <img class="comment-avatar" src="${fullAvatarUrl}" alt="avatar" style="width:32px;height:32px;border-radius:50%;object-fit:cover;">
                        <span class="comment-user">${escapeHtml(comment.username)}</span>
                        <span class="comment-time" style="margin-left:auto;">${formatCommentTime(comment.created_at)}</span>
                        ${canDelete ? `
                            <button class="comment-delete-btn" onclick="deleteComment(${comment.id}, ${songId})" title="Xóa bình luận">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                    <div class="comment-content">${escapeHtml(comment.content)}</div>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    /**
     * Thêm comment mới
     */
    window.addComment = async function(songId, content, formElement, commentsContainer) {
    const token = localStorage.getItem('access_token');
        if (!token) {
            showToast('Vui lòng đăng nhập để bình luận', 'warning');
            return;
        }

        if (!content.trim()) {
            showToast('Nội dung bình luận không được rỗng', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/song/${songId}/comments`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content.trim() })
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Đã thêm bình luận', 'success');
                // Reset form
                if (formElement) {
                    formElement.reset();
                }
                // Reload comments
                if (commentsContainer) {
                    await loadComments(songId, commentsContainer);
                }
            } else {
                showToast(data.msg || 'Không thể thêm bình luận', 'error');
            }
        } catch (error) {
            console.error('Error adding comment:', error);
            showToast('Lỗi kết nối server', 'error');
        }
    };

    /**
     * Xóa comment
     */
    window.deleteComment = async function(commentId, songId) {
        if (!confirm('Bạn có chắc muốn xóa bình luận này?')) {
            return;
        }

    const token = localStorage.getItem('access_token');
        if (!token) {
            showToast('Vui lòng đăng nhập', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/comment/${commentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Đã xóa bình luận', 'success');
                // Reload comments
                const commentsContainer = document.querySelector(`[data-song-id="${songId}"] .comments-container`);
                if (commentsContainer) {
                    await loadComments(songId, commentsContainer);
                }
            } else {
                showToast(data.msg || 'Không thể xóa bình luận', 'error');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            showToast('Lỗi kết nối server', 'error');
        }
    };

    // ==================== HELPER FUNCTIONS ====================

    function getCurrentUserId() {
    const token = localStorage.getItem('access_token');
        if (!token) return null;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub?.id || null;
        } catch {
            return null;
        }
    }

    function isAdmin() {
    const token = localStorage.getItem('access_token');
        if (!token) return false;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            // Kiểm tra role từ claims (không phải sub.role)
            return payload.role === 'admin' || payload.role === 'Admin';
        } catch (e) {
            console.error('Error parsing token for admin check:', e);
            return false;
        }
    }

    function formatCommentTime(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Dưới 1 phút
        if (diff < 60000) {
            return 'Vừa xong';
        }
        // Dưới 1 giờ
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes} phút trước`;
        }
        // Dưới 1 ngày
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours} giờ trước`;
        }
        // Dưới 1 tuần
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days} ngày trước`;
        }
        // Hiển thị ngày tháng
        return date.toLocaleDateString('vi-VN');
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showToast(message, type = 'info') {
        // Tạo toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#ff9800'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

})();
