from flask import Blueprint, request, jsonify
from app import db
from app.models import Playlist
from flask_jwt_extended import jwt_required, get_jwt_identity

playlist_bp = Blueprint('playlist', __name__, url_prefix='/api')  # ⚠️ bạn quên dòng này

@playlist_bp.route('/playlists', methods=['POST'])
@jwt_required()  # ✅ Xác thực bằng JWT trong cookie
def create_playlist():
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return jsonify({"success": False, "message": "Tên playlist là bắt buộc."}), 400

        owner_id = get_jwt_identity()  # ✅ Lấy user_id từ JWT (do bạn set khi login)
        if not owner_id:
            return jsonify({"success": False, "message": "Không xác định được người dùng."}), 401

        # If client didn't provide a cover, use the site's default playlist image
        cover = data.get('cover_image_path') if isinstance(data, dict) else None
        if not cover:
            cover = 'images/playlist_image.png'
        new_playlist = Playlist(name=name, description=description, owner_id=owner_id, cover_image_path=cover)
        db.session.add(new_playlist)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Playlist được tạo thành công!",
            "playlistId": new_playlist.id,
            "name": new_playlist.name
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"🔥 Lỗi khi tạo playlist: {e}")
        return jsonify({"success": False, "message": "Lỗi hệ thống khi tạo playlist."}), 500
