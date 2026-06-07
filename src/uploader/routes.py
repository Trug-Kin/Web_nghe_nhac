from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.music import Song
from src.models.user import User
from src.decorators import uploader_or_admin_required
from flask_jwt_extended import get_jwt_identity

uploader_bp = Blueprint('uploader', __name__, url_prefix='/uploader')



@uploader_bp.route('/api/song', methods=['POST'])
@uploader_or_admin_required()
def create_song():
    import os
    from werkzeug.utils import secure_filename
    from src.jwt_helper import current_identity
    # use shared helper to save uploaded files under static/
    from src.admin.save_uploaded_image import save_uploaded_image
    identity = current_identity()
    user_id = identity.get('id')
    title = request.form.get('title')
    artist_id = request.form.get('artist_id')
    genre_id = request.form.get('genre_id')
    # Xử lý file mp3 upload
    mp3_file = request.files.get('mp3')
    mp3_path = None
    if mp3_file:
        # Save mp3 using the shared helper so returned path is normalized relative to static/
        mp3_path = save_uploaded_image(mp3_file, 'music')

    # normalize numeric fields
    try:
        artist_id = int(artist_id) if artist_id not in [None, ''] else None
    except Exception:
        artist_id = None
    try:
        genre_id = int(genre_id) if genre_id not in [None, ''] else None
    except Exception:
        genre_id = None

    # Validate required fields
    if not title:
        return jsonify({'msg': 'Thiếu tiêu đề bài hát (title)'}), 400
    if not mp3_path:
        return jsonify({'msg': 'Thiếu file mp3 hoặc mp3 không hợp lệ'}), 400
    if genre_id is None:
        return jsonify({'msg': 'Thiếu thể loại (genre_id)'}), 400

    s = Song(title=title, mp3_path=mp3_path, artist_id=artist_id, genre_id=genre_id, uploader_id=user_id)
    db.session.add(s)
    db.session.commit()
    return jsonify({'id': s.id, 'msg': 'Created'}), 201


@uploader_bp.route('/api/song/<int:id>', methods=['PUT','DELETE'])
@uploader_or_admin_required()
def modify_song(id):
    identity = get_jwt_identity()
    user_id = identity.get('id')
    s = Song.query.get(id)
    if not s:
        return jsonify({'msg': 'Song not found'}), 404

    # only uploader or admin may modify; uploader_or_admin_required already checked role but ensure ownership for non-admin
    if identity.get('role') != 'admin' and s.uploader_id != user_id:
        return jsonify({'msg': 'Không có quyền sửa bài hát này'}), 403

    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return jsonify({'msg': 'Deleted'}), 200

    data = request.get_json() or {}
    s.title = data.get('title', s.title)
    s.mp3_path = data.get('mp3_path', s.mp3_path)
    s.artist_id = data.get('artist_id', s.artist_id)
    s.genre_id = data.get('genre_id', s.genre_id)
    db.session.commit()
    return jsonify({'msg': 'Updated'}), 200
