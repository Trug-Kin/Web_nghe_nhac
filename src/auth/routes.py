# File: src/auth/routes.py

from flask import Blueprint, request, jsonify, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from src.extensions import db
from src.models.user import User
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    set_access_cookies, 
    unset_jwt_cookies
)
from src.jwt_helper import current_identity
import os
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# --- Trang ---
@auth_bp.route('/register-page')
def register_page():
    return render_template('register.html')


@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')

@auth_bp.route('/profile')
@jwt_required(optional=True)
def profile_page():
    """Trang hồ sơ người dùng: nếu chưa đăng nhập -> chuyển tới trang login."""
    try:
        identity = current_identity()
        if not identity or not identity.get('id'):
            # Chưa có JWT -> hiển thị trang login
            return render_template('login.html'), 401
        
        user = User.query.get(identity.get('id'))
        if not user:
            return jsonify({'error': 'Không tìm thấy người dùng'}), 404
        
        return render_template('profile.html', user=user)
    except Exception as e:
        # JWT không hợp lệ hoặc expired
        return render_template('login.html'), 401

# --- API: Đăng ký ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    username = data.get('username') or email

    if not email or not password:
        return jsonify({'msg': 'Thiếu thông tin email hoặc password!'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'msg': 'Email đã được sử dụng!'}), 409

    hashed = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': 'Đăng ký thành công!'}), 201


# --- API: Đăng nhập ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not password or not (email or username):
        return jsonify({'msg': 'Thiếu email/username hoặc password!'}), 400

    user = User.query.filter_by(email=email).first() if email else User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'msg': 'Email/Username hoặc mật khẩu không đúng!'}), 401


    # Create token with string subject (user id) and include id/role as additional claims
    additional_claims = {'id': user.id, 'role': user.role, 'username': user.username}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

    resp = jsonify({
        'msg': 'Đăng nhập thành công!',
        'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role},
        'access_token': access_token
    })
    
    # MANUAL cookie setting to bypass HttpOnly issue
    from datetime import datetime, timedelta
    expires = datetime.utcnow() + timedelta(days=7)
    resp.set_cookie(
        'access_token',
        value=access_token,
        max_age=7*24*60*60,  # 7 days in seconds
        expires=expires,
        path='/',
        domain=None,
        secure=False,
        httponly=False,  # CRITICAL: Allow JavaScript to read
        samesite='Lax'
    )
    
    # Debug: Print cookie headers
    print(f"[LOGIN DEBUG] Setting cookie for user {user.username}")
    print(f"[LOGIN DEBUG] Manual cookie with HttpOnly=False")
    print(f"[LOGIN DEBUG] Response headers: {resp.headers}")
    
    return resp, 200


# --- API: Đăng xuất ---
@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'msg': 'Đã đăng xuất'})
    unset_jwt_cookies(resp)  # ✅ Xóa cookie JWT
    return resp, 200


# --- API: Lấy thông tin người dùng ---
@auth_bp.route('/me')
@jwt_required()
def me():
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không tìm thấy người dùng'}), 401

    user = User.query.get(identity.get('id'))
    if not user:
        return jsonify({'msg': 'Người dùng không tồn tại'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'avatar_url': user.avatar or 'images/default.jpg'
    }), 200


# --- API: Upload Avatar ---
@auth_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload và cập nhật avatar cho user hiện tại"""
    try:
        identity = current_identity()
        if not identity or not identity.get('id'):
            return jsonify({'success': False, 'msg': 'Chưa đăng nhập!'}), 401
        
        user = User.query.get(identity.get('id'))
        if not user:
            return jsonify({'success': False, 'msg': 'Không tìm thấy người dùng!'}), 404
        
        # Check if file is in request
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'msg': 'Không có file được upload!'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'msg': 'Chưa chọn file!'}), 400
        
        # Validate file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        filename = file.filename.lower()
        if not any(filename.endswith('.' + ext) for ext in allowed_extensions):
            return jsonify({'success': False, 'msg': 'Chỉ chấp nhận file ảnh (png, jpg, jpeg, gif, webp)!'}), 400
        
        # Create avatars directory if not exists (now in static/images/avatars)
        upload_folder = os.path.join('static', 'images', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = filename.split('.')[-1]
        safe_filename = f"avatar_{user.id}_{timestamp}.{ext}"

        # Save file
        filepath = os.path.join(upload_folder, safe_filename)
        file.save(filepath)

        # Update user avatar in database (always use images/avatars/...)
        avatar_url = f"images/avatars/{safe_filename}"
        user.avatar = avatar_url
        db.session.commit()

        return jsonify({
            'success': True,
            'msg': 'Cập nhật avatar thành công!',
            'avatar_url': avatar_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'msg': f'Lỗi: {str(e)}'}), 500


# --- API: Đổi tên đăng nhập (username) ---
@auth_bp.route('/update-username', methods=['PUT','POST'])
@jwt_required()
def update_username():
    data = request.get_json() or {}
    new_username = (data.get('username') or '').strip()
    if not new_username:
        return jsonify({'success': False, 'msg': 'Thiếu username mới'}), 400
    if len(new_username) < 3:
        return jsonify({'success': False, 'msg': 'Username tối thiểu 3 ký tự'}), 400
    if len(new_username) > 50:
        return jsonify({'success': False, 'msg': 'Username tối đa 50 ký tự'}), 400
    # Kiểm tra trùng
    if User.query.filter_by(username=new_username).first():
        return jsonify({'success': False, 'msg': 'Username đã tồn tại'}), 409
    identity = current_identity()
    if not identity or not identity.get('id'):
        return jsonify({'success': False, 'msg': 'Chưa đăng nhập'}), 401
    user = User.query.get(identity.get('id'))
    if not user:
        return jsonify({'success': False, 'msg': 'Không tìm thấy người dùng'}), 404
    old_username = user.username
    user.username = new_username
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'msg': f'Lỗi lưu DB: {e}'}), 500
    # Cấp token mới để phản ánh username thay đổi
    claims = {'id': user.id, 'role': user.role, 'username': user.username}
    access_token = create_access_token(identity=str(user.id), additional_claims=claims)
    resp = jsonify({'success': True, 'msg': 'Đổi username thành công', 'old_username': old_username, 'new_username': new_username, 'access_token': access_token})
    set_access_cookies(resp, access_token)
    return resp, 200

# --- API: Kiểm tra username có thể dùng (uniqueness check) ---
@auth_bp.route('/check-username', methods=['GET'])
def check_username():
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({'available': False, 'msg': 'Thiếu username'}), 400
    if len(username) < 3:
        return jsonify({'available': False, 'msg': 'Quá ngắn (<3)'}), 200
    if len(username) > 50:
        return jsonify({'available': False, 'msg': 'Quá dài (>50)'}), 200
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'available': not exists, 'msg': 'OK' if not exists else 'Đã tồn tại'}), 200


