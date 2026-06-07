from flask import Blueprint, render_template, g, redirect, url_for
from app.auth_utils import authenticate_user # Middleware xác thực
from app.models import User # Model User

auth_bp = Blueprint('auth', __name__) 
# ... các routes đăng nhập, đăng ký khác ...

@auth_bp.route('/profile', methods=['GET'])
@authenticate_user # 👈 Bắt buộc phải đăng nhập để truy cập
def profile_page():
    # g.user_id được gán bởi middleware authenticate_user
    user_id = g.user_id 
    
    # 1. Truy vấn thông tin người dùng từ Database
    user = User.query.get(user_id)
    
    if user is None:
        # Nếu có lỗi xảy ra (user_id trong session nhưng user không tồn tại), đẩy về trang đăng nhập
        return redirect(url_for('auth.login_page'))
    
    # 2. Truy vấn dữ liệu liên quan (Lịch sử nghe, Thống kê, v.v. - Tùy chọn)
    # Ví dụ: Lấy danh sách playlists
    # playlists = user.playlists.all() 
    
    # 3. Render trang HTML và truyền dữ liệu
    return render_template(
        'profile.html', 
        user=user, 
        # playlists=playlists 
    )

# Lưu ý: Đảm bảo bạn đã đăng ký auth_bp trong create_app() của bạn.