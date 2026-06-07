"""
Routes xử lý like và comment cho bài hát
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from src.extensions import db
from src.models.user import User
from src.models.music import Song, Like, Comment
from datetime import datetime

interactions_bp = Blueprint('interactions', __name__)

# ==================== LIKE ENDPOINTS ====================

@interactions_bp.route('/api/song/<int:song_id>/like', methods=['POST'])
@jwt_required()
def like_song(song_id):
    """Like một bài hát (hoặc unlike nếu đã like)."""
    try:
        # Lấy claims từ JWT token
        claims = get_jwt()
        user_id = claims.get('id')
        
        if not user_id:
            return jsonify({'msg': 'Token không hợp lệ'}), 401
    except Exception as e:
        return jsonify({'msg': f'Lỗi xác thực: {str(e)}'}), 401
    
    # Kiểm tra bài hát tồn tại
    song = Song.query.get(song_id)
    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại'}), 404
    
    # Kiểm tra đã like chưa
    existing_like = Like.query.filter_by(user_id=user_id, song_id=song_id).first()
    
    if existing_like:
        # Đã like → Unlike (toggle)
        db.session.delete(existing_like)
        db.session.commit()
        
        # Đếm lại số like
        like_count = Like.query.filter_by(song_id=song_id).count()
        
        return jsonify({
            'msg': 'Đã bỏ thích',
            'liked': False,
            'like_count': like_count
        })
    else:
        # Chưa like → Thêm like
        new_like = Like(user_id=user_id, song_id=song_id)
        db.session.add(new_like)
        db.session.commit()
        
        # Đếm lại số like
        like_count = Like.query.filter_by(song_id=song_id).count()
        
        return jsonify({
            'msg': 'Đã thích',
            'liked': True,
            'like_count': like_count
        })

@interactions_bp.route('/api/song/<int:song_id>/likes', methods=['GET'])
def get_song_likes(song_id):
    """Lấy thông tin like của bài hát."""
    # Đếm số like
    like_count = Like.query.filter_by(song_id=song_id).count()
    
    # Kiểm tra user hiện tại đã like chưa (nếu đăng nhập)
    liked = False
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        if claims:
            user_id = claims.get('id')
            if user_id:
                liked = Like.query.filter_by(user_id=user_id, song_id=song_id).first() is not None
    except:
        pass
    
    return jsonify({
        'song_id': song_id,
        'like_count': like_count,
        'liked': liked
    })

@interactions_bp.route('/api/user/liked-songs/count', methods=['GET'])
@jwt_required(optional=True)
def get_user_liked_songs_count():
    """Lấy số lượng bài hát user đã like."""
    try:
        claims = get_jwt()
        user_id = claims.get('id') if claims else None
        
        if not user_id:
            return jsonify({'count': 0})
        
        count = Like.query.filter_by(user_id=user_id).count()
        return jsonify({'count': count})
    except:
        return jsonify({'count': 0})

# ==================== COMMENT ENDPOINTS ====================

@interactions_bp.route('/api/song/<int:song_id>/comments', methods=['GET'])
def get_song_comments(song_id):
    """Lấy danh sách bình luận của bài hát."""
    # Kiểm tra bài hát tồn tại
    song = Song.query.get(song_id)
    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại'}), 404
    
    # Lấy comments, sắp xếp mới nhất trước
    comments = (Comment.query
                .filter_by(song_id=song_id)
                .order_by(Comment.created_at.desc())
                .limit(100)  # Giới hạn 100 comment gần nhất
                .all())
    
    comments_data = []
    for comment in comments:
        user = User.query.get(comment.user_id)
        # Nếu user có avatar, trả về, không thì trả về ảnh mặc định
        avatar_url = user.avatar if (user and hasattr(user, 'avatar') and user.avatar) else 'images/default.jpg'
        
        comments_data.append({
            'id': comment.id,
            'user_id': comment.user_id,
            'username': user.username if user else 'Unknown',
            'avatar_url': avatar_url,
            'content': comment.content,
            'created_at': comment.created_at.isoformat() if comment.created_at else None
        })
    
    return jsonify({
        'song_id': song_id,
        'comments': comments_data,
        'count': len(comments_data)
    })

@interactions_bp.route('/api/song/<int:song_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(song_id):
    """Thêm bình luận mới."""
    try:
        claims = get_jwt()
        user_id = claims.get('id')
        
        if not user_id:
            return jsonify({'msg': 'Token không hợp lệ'}), 401
    except Exception as e:
        return jsonify({'msg': f'Lỗi xác thực: {str(e)}'}), 401
    
    # Kiểm tra bài hát tồn tại
    song = Song.query.get(song_id)
    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại'}), 404
    
    # Lấy nội dung comment
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'msg': 'Nội dung bình luận không được rỗng'}), 400
    
    if len(content) > 1000:
        return jsonify({'msg': 'Bình luận quá dài (tối đa 1000 ký tự)'}), 400
    
    # Tạo comment mới
    new_comment = Comment(
        user_id=user_id,
        song_id=song_id,
        content=content
    )
    db.session.add(new_comment)
    db.session.commit()
    
    # Lấy thông tin user
    user = User.query.get(user_id)
    
    return jsonify({
        'msg': 'Đã thêm bình luận',
        'comment': {
            'id': new_comment.id,
            'user_id': user_id,
            'username': user.username if user else 'Unknown',
            'content': content,
            'created_at': new_comment.created_at.isoformat() if new_comment.created_at else None
        }
    }), 201

@interactions_bp.route('/api/comment/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Xóa bình luận (chỉ chủ comment hoặc admin)."""
    try:
        claims = get_jwt()
        user_id = claims.get('id')
        role = claims.get('role')
        
        if not user_id:
            return jsonify({'msg': 'Token không hợp lệ'}), 401
    except Exception as e:
        return jsonify({'msg': f'Lỗi xác thực: {str(e)}'}), 401
    
    # Tìm comment
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'msg': 'Bình luận không tồn tại'}), 404
    
    # Kiểm tra quyền: chỉ chủ comment hoặc admin mới xóa được
    if comment.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Bạn không có quyền xóa bình luận này'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'msg': 'Đã xóa bình luận'})
