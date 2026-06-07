from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from src.jwt_helper import current_identity
from src.extensions import db
from src.models.user import User

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/users')


# 🔍 Tìm kiếm người dùng
@user_api_bp.route('/search', methods=['GET'])
def search_users():
    """Search users by username (no authentication required)"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([]), 200
    
    users = User.query.filter(User.username.ilike(f'%{query}%')).limit(20).all()
    
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar': u.avatar if hasattr(u, 'avatar') else 'images/default.jpg',
        'role': u.role
    } for u in users]), 200


# 📊 Lấy thông tin follow của user
@user_api_bp.route('/<int:user_id>/follow-info', methods=['GET'])
def get_follow_info(user_id):
    """Get follower/following counts and check if current user follows this user"""
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'msg': 'User not found'}), 404
    
    follower_count = target_user.followers.count()
    following_count = target_user.following.count()
    
    is_following = False
    try:
        verify_jwt_in_request(optional=True)
        identity = current_identity()
        if identity and identity.get('id'):
            current_user = User.query.get(identity.get('id'))
            if current_user and target_user in current_user.following:
                is_following = True
    except Exception:
        pass
    
    return jsonify({
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following
    }), 200


# ➕ Follow/Unfollow user
@user_api_bp.route('/<int:user_id>/follow', methods=['POST'])
@jwt_required()
def toggle_follow(user_id):
    """Follow or unfollow a user"""
    identity = current_identity()
    current_user_id = identity.get('id')
    
    if current_user_id == user_id:
        return jsonify({'msg': 'Không thể follow chính mình'}), 400
    
    current_user = User.query.get(current_user_id)
    target_user = User.query.get(user_id)
    
    if not target_user:
        return jsonify({'msg': 'User not found'}), 404
    
    if target_user in current_user.following:
        # Unfollow
        current_user.following.remove(target_user)
        db.session.commit()
        return jsonify({'msg': 'unfollowed', 'is_following': False}), 200
    else:
        # Follow
        current_user.following.append(target_user)
        db.session.commit()
        return jsonify({'msg': 'followed', 'is_following': True}), 200


# 👥 Lấy danh sách người mà user đang follow
@user_api_bp.route('/<int:user_id>/following', methods=['GET'])
def get_following(user_id):
    """Get list of users that this user is following"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    following_users = user.following.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar': u.avatar if hasattr(u, 'avatar') and u.avatar else 'images/default.jpg'
    } for u in following_users]), 200


# 👥 Lấy danh sách followers của user
@user_api_bp.route('/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """Get list of users following this user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    follower_users = user.followers.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar': u.avatar if hasattr(u, 'avatar') and u.avatar else 'images/default.jpg'
    } for u in follower_users]), 200
