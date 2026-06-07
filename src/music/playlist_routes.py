from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from src.jwt_helper import current_identity
from src.extensions import db
from src.models.music import Playlist, Song, ListeningHistory, Like
from sqlalchemy import func
from sqlalchemy import or_

playlist_bp = Blueprint('playlist_api', __name__, url_prefix='/api/playlists')


# 🌐 Lấy danh sách playlist công khai (không cần đăng nhập)
@playlist_bp.route('/public', methods=['GET'])
def public_playlists():
    """Get all public playlists for homepage display"""
    playlists = Playlist.query.filter_by(is_public=True).order_by(Playlist.created_at.desc()).limit(12).all()
    out = []
    for p in playlists:
        # Get image from last song or use default
        image_path = 'images/playlist_image.png'
        if p.songs and p.songs.count() > 0:
            last_song = list(p.songs.all())[-1]
            if getattr(last_song, 'image_path', None):
                image_path = last_song.image_path
            elif last_song.album and getattr(last_song.album, 'cover_image_path', None):
                image_path = last_song.album.cover_image_path
        
        out.append({
            'id': p.id,
            'name': p.name,
            'username': p.owner.username if p.owner else 'Người dùng',
            'song_count': p.songs.count() if hasattr(p.songs, 'count') else len(p.songs),
            'image_path': image_path
        })
    return jsonify(out), 200


# 🧾 Lấy danh sách playlist của người dùng hiện tại
@playlist_bp.route('/', methods=['GET'])
@jwt_required()
def list_playlists():
    identity = current_identity()
    user_id = identity.get('id')
    # Only show playlists owned by the requesting user
    playlists = Playlist.query.filter_by(user_id=user_id).all()
    out = [
        {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'song_count': p.songs.count() if hasattr(p.songs, 'count') else len(p.songs),
            'user_id': p.user_id,
            'owner_username': p.owner.username if p.owner else None,
            'is_public': getattr(p, 'is_public', False),
            'image_path': getattr(p, 'cover_image_path', None),
            'created_at': getattr(p, 'created_at', None)
        } for p in playlists
    ]
    return jsonify(out), 200

# 🔎 Tìm bài hát (dùng để thêm vào playlist) – yêu cầu đăng nhập
@playlist_bp.route('/search_songs')
@jwt_required()
def search_songs():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'songs': []})
    # Giới hạn số lượng để tránh trả về quá nhiều
    query = Song.query.filter(or_(Song.title.ilike(f"%{q}%"), getattr(Song, 'artist_name', Song.title).ilike(f"%{q}%")))
    songs = query.limit(30).all()
    out = []
    for s in songs:
        out.append({
            'id': s.id,
            'title': s.title,
            'artist_name': s.artist.name if getattr(s, 'artist', None) else getattr(s, 'artist_name', None),
            'mp3_path': getattr(s, 'mp3_path', None)
        })
    return jsonify({'songs': out})


# 🆕 Tạo playlist (user, uploader, admin đều được phép)
@playlist_bp.route('/', methods=['POST'])
@jwt_required()
def create_playlist():
    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')

    if role not in ['user', 'uploader', 'admin']:
        return jsonify({'msg': 'Không có quyền tạo playlist!'}), 403

    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    initial_song_ids = data.get('song_ids') or []

    if not name:
        return jsonify({'msg': 'Thiếu tên playlist!'}), 400

    # Determine cover image: prefer explicit value from client, otherwise use default
    cover = data.get('cover_image_path') or 'images/playlist_image.png'
    playlist = Playlist(name=name, description=description, user_id=user_id, cover_image_path=cover)
    db.session.add(playlist)
    # Optional batch add songs
    added_songs = []
    if initial_song_ids and isinstance(initial_song_ids, list):
        for sid in initial_song_ids:
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                continue
            song = Song.query.get(sid_int)
            if song and song not in playlist.songs:
                playlist.songs.append(song)
                added_songs.append(sid_int)
    db.session.commit()

    return jsonify({'id': playlist.id, 'name': playlist.name, 'added_song_ids': added_songs, 'msg': 'Playlist đã được tạo thành công!'}), 201


# 🔍 Xem chi tiết playlist
@playlist_bp.route('/<int:id>', methods=['GET'])
def get_playlist(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404
    
    # Check if user is owner or playlist is public
    is_owner = False
    try:
        verify_jwt_in_request(optional=True)
        identity = current_identity()
        if identity and identity.get('id') == playlist.user_id:
            is_owner = True
    except Exception:
        identity = None

    # Allow access if: owner OR playlist is public
    if not is_owner and not getattr(playlist, 'is_public', False):
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404

    # Get songs
    song_list = playlist.songs.all() if hasattr(playlist.songs, 'all') else list(playlist.songs)

    # Compute listen counts from ListeningHistory for songs in this playlist
    song_ids = [s.id for s in song_list]
    listen_counts = {}
    if song_ids:
        counts = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in counts}

    # Also compute like counts for songs
    like_counts = {}
    if song_ids:
        like_rows = db.session.query(Like.song_id, func.count(Like.id)).filter(Like.song_id.in_(song_ids)).group_by(Like.song_id).all()
        like_counts = {sid: c for sid, c in like_rows}

    songs = [
        {
            'id': s.id,
            'title': s.title,
            'mp3_path': s.mp3_path,
            'mp3_url': getattr(s, 'mp3_url', s.mp3_path),
            'artist_id': s.artist_id,
            'artist_name': s.artist_name,
            'genre_id': getattr(s, 'genre_id', None),
            'genre_name': (s.genre.name if getattr(s, 'genre', None) else None),
            'album_id': getattr(s, 'album_id', None),
            'album_title': (s.album.title if getattr(s, 'album', None) else None),
            'image_path': s.image_path or None,
            'album_image_path': s.image_path or (s.album.cover_image_path if s.album else None),
            'listen_count': int(listen_counts.get(s.id, 0)),
            'like_count': int(like_counts.get(s.id, 0))
        } for s in song_list
    ]

    return jsonify({
        'id': playlist.id,
        'name': playlist.name,
        'description': playlist.description,
        'songs': songs,
        'created_at': getattr(playlist, 'created_at', None)
    }), 200


# ✏️ Sửa hoặc xóa playlist (chỉ chủ sở hữu hoặc admin)
@playlist_bp.route('/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_playlist(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404

    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')

    if playlist.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Không có quyền sửa/xóa playlist này!'}), 403

    if request.method == 'DELETE':
        db.session.delete(playlist)
        db.session.commit()
        return jsonify({'msg': 'Đã xóa playlist!'}), 200

    data = request.get_json() or {}
    if 'name' in data:
        playlist.name = data.get('name', playlist.name)
    if 'description' in data:
        playlist.description = data.get('description', playlist.description)
    if 'is_public' in data:
        playlist.is_public = bool(data.get('is_public', False))
    db.session.commit()

    return jsonify({
        'msg': 'Đã cập nhật playlist!', 
        'playlist': {
            'id': playlist.id, 
            'name': playlist.name, 
            'is_public': getattr(playlist, 'is_public', False)
        }
    }), 200


# ➕ Thêm bài hát vào playlist (chủ sở hữu hoặc admin)
@playlist_bp.route('/<int:id>/add_song', methods=['POST'])
@jwt_required()
def add_song_to_playlist(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404

    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')

    if playlist.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Không có quyền chỉnh sửa playlist này!'}), 403

    data = request.get_json() or {}
    song_id = data.get('song_id')
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại!'}), 404

    if song in playlist.songs:
        return jsonify({'msg': 'Bài hát đã có trong playlist!'}), 400

    playlist.songs.append(song)
    db.session.commit()
    return jsonify({'msg': 'Đã thêm bài hát vào playlist!'}), 200

# ➕ Bulk add songs
@playlist_bp.route('/<int:id>/add_songs', methods=['POST'])
@jwt_required()
def bulk_add_songs(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404
    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')
    if playlist.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Không có quyền chỉnh sửa playlist này!'}), 403
    data = request.get_json() or {}
    ids = data.get('song_ids') or []
    if not isinstance(ids, list):
        return jsonify({'msg': 'song_ids phải là danh sách'}), 400
    added = []
    skipped = []
    for sid in ids:
        try:
            sid_int = int(sid)
        except (TypeError, ValueError):
            skipped.append(sid)
            continue
        song = Song.query.get(sid_int)
        if not song:
            skipped.append(sid_int)
            continue
        if song in playlist.songs:
            skipped.append(sid_int)
            continue
        playlist.songs.append(song)
        added.append(sid_int)
    db.session.commit()
    return jsonify({'msg': f'Đã thêm {len(added)} bài', 'added_ids': added, 'skipped': skipped}), 200


# ➖ Xóa bài hát khỏi playlist (chủ sở hữu hoặc admin)
@playlist_bp.route('/<int:id>/remove_song', methods=['POST'])
@jwt_required()
def remove_song_from_playlist(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404

    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')

    if playlist.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Không có quyền chỉnh sửa playlist này!'}), 403

    data = request.get_json() or {}
    song_id = data.get('song_id')
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại!'}), 404

    if song not in playlist.songs:
        return jsonify({'msg': 'Bài hát không có trong playlist!'}), 400

    playlist.songs.remove(song)
    db.session.commit()
    return jsonify({'msg': 'Đã xóa bài hát khỏi playlist!'}), 200

# ➖ Bulk remove songs
@playlist_bp.route('/<int:id>/remove_songs', methods=['POST'])
@jwt_required()
def bulk_remove_songs(id):
    playlist = Playlist.query.get(id)
    if not playlist:
        return jsonify({'msg': 'Playlist không tồn tại!'}), 404
    identity = current_identity()
    user_id = identity.get('id')
    role = identity.get('role')
    if playlist.user_id != user_id and role != 'admin':
        return jsonify({'msg': 'Không có quyền chỉnh sửa playlist này!'}), 403
    data = request.get_json() or {}
    ids = data.get('song_ids') or []
    if not isinstance(ids, list):
        return jsonify({'msg': 'song_ids phải là danh sách'}), 400
    removed = []
    for sid in ids:
        try:
            sid_int = int(sid)
        except (TypeError, ValueError):
            continue
        song = Song.query.get(sid_int)
        if song and song in playlist.songs:
            playlist.songs.remove(song)
            removed.append(sid_int)
    db.session.commit()
    return jsonify({'msg': f'Đã xóa {len(removed)} bài', 'removed_ids': removed}), 200
