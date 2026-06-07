from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db, User, bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# --- Pages ---
@auth_bp.route('/register-page')
def register_page():
    return render_template('register.html')

@auth_bp.route('/login-page')
def login_page():
    return render_template('login.html')

# --- API: register ---
@auth_bp.route('/register', methods=['POST'])
def register():
    # TODO: implement registration logic
    return jsonify({'msg': 'Chức năng đăng ký chưa được triển khai.'}), 501

# --- API: login ---
@auth_bp.route("/login", methods=["POST"])
def login():
    # TODO: implement login logic (validate credentials, create token)
    return jsonify({'msg': 'Chức năng đăng nhập chưa được triển khai.'}), 501

# --- API: logout ---
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'msg': 'Đã đăng xuất'}), 200

# --- API: me ---
@auth_bp.route('/me')
@jwt_required()
def me():
    # TODO: return current user info
    identity = get_jwt_identity()
    if not identity:
        return jsonify({'msg': 'Không có thông tin người dùng.'}), 401
    # minimal safe response
    return jsonify({'user': identity}), 200

# --- PAGE: Hồ sơ người dùng ---
@auth_bp.route('/profile')
@jwt_required()
def profile_page():
    identity = get_jwt_identity()
    if not identity:
        return render_template('login.html', msg="Vui lòng đăng nhập trước.")
    
    user = User.query.get(identity['id'])
    if not user:
        return render_template('login.html', msg="Không tìm thấy người dùng.")

    return render_template('profile.html', user=user)
