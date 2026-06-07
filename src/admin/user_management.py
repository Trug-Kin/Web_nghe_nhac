from src.models.user import User



def get_all_users():
    return User.query.order_by(User.id).all()


def set_user_role(user_id, role):
    user = User.query.get(user_id)
    if not user:
        return False
    user.role = role
    db.session.commit()
    return True


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False
    db.session.delete(user)
    db.session.commit()
    return True
from flask import Blueprint, render_template, jsonify, request, abort
from src.models.user import User
from flask_login import login_required, current_user
from functools import wraps
from src.extensions import db

admin_users = Blueprint('admin_users', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if not current_user.role or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_users.route('/manage-users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@admin_users.route('/update-user-role', methods=['POST'])
@login_required
@admin_required
def update_user_role():
    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    
    if not user_id or not new_role:
        return jsonify({"error": "Missing parameters"}), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Prevent changing super admin role
    if user.role == 'admin' and user.email == 'phammidoan123@gmail.comphamm':
        return jsonify({"error": "Cannot change super admin role"}), 403
    
    user.role = new_role.lower()
    db.session.commit()
    
    return jsonify({"success": True, "message": "Role updated successfully"})