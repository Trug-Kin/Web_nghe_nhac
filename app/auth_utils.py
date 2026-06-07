from functools import wraps
# ✅ Cần import thêm request, redirect, và url_for
from flask import session, jsonify, g, request, redirect, url_for


def authenticate_user(f):
    """
    Middleware kiểm tra user_id trong session.
    - Nếu là yêu cầu API (bắt đầu bằng /api/), trả về JSON 401.
    - Nếu là yêu cầu Trang (HTML), chuyển hướng về trang đăng nhập.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id') 
        
        if user_id is None:
            # ------------------------------------------------
            # ✅ LOGIC MỚI: Phân biệt API và HTML Page
            # ------------------------------------------------
            
            # Kiểm tra nếu đường dẫn bắt đầu bằng '/api/'
            # (Hoặc kiểm tra header 'Accept: application/json' nếu cần chi tiết hơn)
            if request.path.startswith('/api/'):
                # Yêu cầu API: Trả về JSON 401
                return jsonify({
                    "success": False, 
                    "message": "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."
                }), 401 
            else:
                # Yêu cầu Trang HTML (ví dụ: /profile): Chuyển hướng
                # Lưu ý: 'auth.login_page' là tên endpoint của route đăng nhập của bạn.
                return redirect(url_for('auth.login_page')) 

        # Gán user_id vào đối tượng 'g'
        g.user_id = user_id
        
        # Tùy chọn: Tải User object để sử dụng dễ dàng hơn trong các routes khác
        # from app.models import User # Phải đảm bảo User Model đã được import
        # g.user = User.query.get(user_id)
        
        return f(*args, **kwargs)
    return decorated_function