from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request
from src.jwt_helper import current_identity
from src.models.user import User
from src.extensions import db
from src.models import bcrypt


def admin_required():
    """
    Decorator: Chỉ cho phép user có role 'admin'.
    Kiểm tra token JWT, lấy identity rồi truy vấn DB để xác định quyền.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            identity = current_identity()
            if not identity or not isinstance(identity, dict):
                return jsonify(msg="Token không hợp lệ."), 401

            user_id = identity.get("id")
            user = User.query.get(user_id)

            if not user or user.role != "admin":
                return jsonify(msg="Yêu cầu quyền Admin!"), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def uploader_or_admin_required():
    """
    Decorator: Cho phép user có role 'uploader' hoặc 'admin'.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            identity = current_identity()
            if not identity or not isinstance(identity, dict):
                return jsonify(msg="Token không hợp lệ."), 401

            user_id = identity.get('id')
            user = User.query.get(user_id)

            if not user or user.role not in ["admin", "uploader"]:
                return jsonify(msg="Yêu cầu quyền Uploader hoặc Admin!"), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
