from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from src.models import Artist, Album, Genre

# ...existing code...

from sqlalchemy import or_
## ...existing code...
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from src.models import Artist, Album, Genre

# ...existing code...
# ...existing code...




from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.admin.user_management import get_all_users, set_user_role, delete_user
from src.models.user import User
from src.extensions import db
from src.models.music import Song, Genre, Artist, Album
import random
from src.auth.routes import current_identity
from src.admin.save_uploaded_image import save_uploaded_image

from flask_jwt_extended import get_jwt_identity

# Hàm xác thực admin từ JWT
def check_admin():
    identity = get_jwt_identity()
    print(f"[DEBUG] JWT identity: {identity}")
    if not identity:
        print("[DEBUG] No identity in JWT")
        return None
    user = None
    # Nếu identity là dict, lấy id hoặc username
    if isinstance(identity, dict):
        user_id = identity.get('id')
        username = identity.get('username')
        if user_id:
            user = User.query.get(user_id)
            print(f"[DEBUG] User from id (dict): {user}")
        elif username:
            user = User.query.filter_by(username=username).first()
            print(f"[DEBUG] User from username (dict): {user}")
    else:
        # Nếu identity là số, tìm theo id, nếu là chuỗi, tìm theo username
        try:
            user_id = int(identity)
            user = User.query.get(user_id)
            print(f"[DEBUG] User from id: {user}")
        except (ValueError, TypeError):
            user = User.query.filter_by(username=identity).first()
            print(f"[DEBUG] User from username: {user}")
    if not user:
        print("[DEBUG] No user found for identity")
        return None
    if user.role != 'admin':
        print(f"[DEBUG] User {user.username} is not admin, role={user.role}")
        return None
    print(f"[DEBUG] User {user.username} is admin")
    return user

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from src.admin.user_management import get_all_users, set_user_role, delete_user
from src.models.user import User
from src.extensions import db
from src.models.music import Song, Genre, Artist, Album
import random
from src.auth.routes import current_identity
from src.admin.save_uploaded_image import save_uploaded_image


from src.models.music import Ad

admin_bp = Blueprint('admin', __name__,url_prefix="/admin")

# --- API QUẢN LÝ QUẢNG CÁO ---
@admin_bp.route('/api/ads', methods=['GET'])
@jwt_required()
def get_ads():
    admin = check_admin()
    if not admin:
        return jsonify({'msg': 'Chỉ admin mới được truy cập'}), 403
    ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return jsonify([
        {
            'id': ad.id,
            'title': ad.title,
            'image_url': ad.image_url,
            'link': ad.link,
            'active': ad.active,
            'created_at': str(ad.created_at),
            'updated_at': str(ad.updated_at)
        } for ad in ads
    ]), 200

@admin_bp.route('/api/ads', methods=['POST'])
@jwt_required()
def create_ad():
    admin = check_admin()
    if not admin:
        return jsonify({'msg': 'Chỉ admin mới được truy cập'}), 403
    data = request.get_json() or {}
    ad = Ad(
        title=data.get('title', ''),
        image_url=data.get('image_url', ''),
        link=data.get('link', ''),
        active=bool(data.get('active', True))
    )
    db.session.add(ad)
    db.session.commit()
    return jsonify({'msg': 'Đã tạo quảng cáo', 'id': ad.id}), 201

@admin_bp.route('/api/ads/<int:ad_id>', methods=['PUT'])
@jwt_required()
def update_ad(ad_id):
    admin = check_admin()
    if not admin:
        return jsonify({'msg': 'Chỉ admin mới được truy cập'}), 403
    ad = Ad.query.get(ad_id)
    if not ad:
        return jsonify({'msg': 'Không tìm thấy quảng cáo'}), 404
    data = request.get_json() or {}
    ad.title = data.get('title', ad.title)
    ad.image_url = data.get('image_url', ad.image_url)
    ad.link = data.get('link', ad.link)
    ad.active = bool(data.get('active', ad.active))
    db.session.commit()
    return jsonify({'msg': 'Đã cập nhật quảng cáo'}), 200

@admin_bp.route('/api/ads/<int:ad_id>', methods=['DELETE'])
@jwt_required()
def delete_ad(ad_id):
    admin = check_admin()
    if not admin:
        return jsonify({'msg': 'Chỉ admin mới được truy cập'}), 403
    ad = Ad.query.get(ad_id)
    if not ad:
        return jsonify({'msg': 'Không tìm thấy quảng cáo'}), 404
    db.session.delete(ad)
    db.session.commit()
    return jsonify({'msg': 'Đã xóa quảng cáo'}), 200

# --- API upload ảnh bài hát ---
import os
from werkzeug.utils import secure_filename

@admin_bp.route('/api/upload/song-image', methods=['POST'])
@jwt_required()
def upload_song_image():
    if 'image' not in request.files:
        return jsonify({'msg': 'Không có file ảnh'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'msg': 'Tên file rỗng'}), 400
    filename = secure_filename(file.filename)
    save_dir = os.path.join('static', 'images', 'songs')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    file.save(save_path)
    image_path = f'images/songs/{filename}'
    return jsonify({'image_path': image_path}), 200

# --- API lấy danh sách nghệ sĩ, album, thể loại cho form bài hát ---
@admin_bp.route('/api/artist', methods=['GET'])
@jwt_required()
def get_artists():
    identity = current_identity()
    current_user_id = identity.get('id') if identity else None
    current_role = (identity.get('role') or '').lower() if identity else ''
    is_admin = current_role == 'admin'
    artists = Artist.query.all()
    def normalize_img(img):
        if img in [None, "None", ""]:
            return None
        if img.startswith("/static/"):
            return img[len("/static/"):]
        return img
    return jsonify([
        {
            'id': a.id,
            'name': a.name,
            'image_path': normalize_img(a.image_path),
            'uploader_id': getattr(a, 'uploader_id', None),
            'can_edit': bool(is_admin or (getattr(a, 'uploader_id', None) == current_user_id)),
            'can_delete': bool(is_admin or (getattr(a, 'uploader_id', None) == current_user_id))
        } for a in artists
    ]), 200

@admin_bp.route('/api/album', methods=['GET'])
@jwt_required()
def get_albums():
    identity = current_identity()
    current_user_id = identity.get('id') if identity else None
    current_role = (identity.get('role') or '').lower() if identity else ''
    is_admin = current_role == 'admin'
    albums = Album.query.all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'uploader_id': getattr(a, 'uploader_id', None),
            'can_edit': bool(is_admin or (getattr(a, 'uploader_id', None) == current_user_id)),
            'can_delete': bool(is_admin or (getattr(a, 'uploader_id', None) == current_user_id))
        } for a in albums
    ]), 200

@admin_bp.route('/api/genre', methods=['GET'])
@jwt_required()
def get_genres():
    identity = current_identity()
    current_user_id = identity.get('id') if identity else None
    current_role = (identity.get('role') or '').lower() if identity else ''
    is_admin = current_role == 'admin'
    genres = Genre.query.all()
    def normalize_img(img):
        if img in [None, "None", ""]:
            return None
        if img.startswith("/static/"):
            return img[len("/static/"):]
        return img
    return jsonify([
        {
            'id': g.id,
            'name': g.name,
            'image_path': normalize_img(g.image_path),
            'color_class': g.color_class,
            'uploader_id': getattr(g, 'uploader_id', None),
            'can_edit': bool(is_admin or (getattr(g, 'uploader_id', None) == current_user_id)),
            'can_delete': bool(is_admin or (getattr(g, 'uploader_id', None) == current_user_id))
        } for g in genres
    ]), 200

# --- API quản lý bài hát ---
from src.models.music import Song, Artist, Album, Genre
from src.extensions import db

# Lấy danh sách bài hát
@admin_bp.route('/api/song', methods=['GET'])
@jwt_required()
def get_songs():
    """Return list of songs with ownership info.
    Uploaders only see can_edit/can_delete=True for their own songs; admin for all.
    """
    identity = current_identity()
    current_user_id = identity.get('id') if identity else None
    current_role = (identity.get('role') or '').lower() if identity else ''
    is_admin = current_role == 'admin'
    songs = Song.query.all()
    result = []
    for song in songs:
        artists = [a.name for a in song.artists] if hasattr(song, 'artists') else []
        owner_id = getattr(song, 'uploader_id', None)
        is_owner = owner_id is not None and owner_id == current_user_id
        result.append({
            'id': song.id,
            'title': song.title,
            'album_id': song.album_id,
            'genre_id': song.genre_id,
            'artists': artists,
            'image_path': getattr(song, 'image_path', None),
            'uploader_id': owner_id,
            'can_edit': bool(is_admin or is_owner),
            'can_delete': bool(is_admin or is_owner)
        })
    return jsonify(result), 200

# Lấy chi tiết bài hát
@admin_bp.route('/api/song/<int:id>', methods=['GET'])
@jwt_required()
def get_song(id):
    song = Song.query.get(id)
    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại'}), 404
    artists = [a.id for a in song.artists] if hasattr(song, 'artists') else []
    return jsonify({
        'id': song.id,
        'title': song.title,
        'album_id': song.album_id,
        'genre_id': song.genre_id,
        'artists': artists,
        'image_path': getattr(song, 'image_path', None)
    }), 200

# Thêm bài hát
@admin_bp.route('/api/song', methods=['POST'])
@jwt_required()
def add_song():
    try:
        identity = current_identity()
        if not identity:
            return jsonify({'msg': 'Không có quyền'}), 403
        user_id = identity.get('id')
        user_role = (identity.get('role') or '').lower()
        if user_role not in ['admin', 'uploader']:
            return jsonify({'msg': 'Không có quyền'}), 403
        # Hỗ trợ multipart/form-data (FormData) hoặc JSON
        if request.content_type and request.content_type.startswith('multipart/'):
            # Lấy dữ liệu từ form
            title = request.form.get('title')
            album_id = request.form.get('album_id') or None
            genre_id = request.form.get('genre_id') or None
            artists_raw = request.form.get('artists', '[]')
            try:
                import json
                artist_ids = json.loads(artists_raw) if isinstance(artists_raw, str) else artists_raw
            except Exception:
                artist_ids = []

            # Lưu file ảnh và mp3 nếu có (dùng helper chung)
            from src.admin.save_uploaded_image import save_uploaded_image
            image_path = None
            mp3_path = None
            if 'image' in request.files:
                image_file = request.files['image']
                image_path = save_uploaded_image(image_file, 'images/songs')
            if 'mp3' in request.files:
                mp3_file = request.files['mp3']
                mp3_path = save_uploaded_image(mp3_file, 'music')
        else:
            data = request.get_json() or {}
            title = data.get('title')
            album_id = data.get('album_id')
            genre_id = data.get('genre_id')
            artist_ids = data.get('artists', [])
            image_path = data.get('image_path')
            mp3_path = data.get('mp3_path') if data.get('mp3_path') else None

        # Validate minimal required fields and normalize artist ids
        if not mp3_path:
            return jsonify({'msg': 'Thiếu file mp3 hoặc mp3_path'}), 400
        try:
            artist_ids = [int(a) for a in artist_ids] if artist_ids else []
        except Exception:
            artist_ids = []

        # ensure genre_id is an int or None
        try:
            genre_id = int(genre_id) if genre_id not in [None, ''] else None
        except Exception:
            genre_id = None

        song = Song(title=title, album_id=album_id, genre_id=genre_id, image_path=image_path, mp3_path=mp3_path, uploader_id=user_id)
        db.session.add(song)
        db.session.commit()
        # Liên kết nhiều nghệ sĩ
        if hasattr(song, 'artists') and artist_ids:
            for artist_id in artist_ids:
                try:
                    aid = int(artist_id)
                except Exception:
                    continue
                artist = Artist.query.get(aid)
                if artist:
                    song.artists.append(artist)
            db.session.commit()
        return jsonify({'msg': 'Thêm bài hát thành công', 'id': song.id}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'msg': 'Lỗi khi lưu bài hát: ' + str(e)}), 500

# Sửa bài hát
@admin_bp.route('/api/song/<int:id>', methods=['PUT'])
@jwt_required()
def update_song(id):
    try:
        song = Song.query.get(id)
        if not song:
            return jsonify({'msg': 'Bài hát không tồn tại'}), 404
        identity = current_identity()
        if not identity:
            return jsonify({'msg': 'Không có quyền'}), 403
        user_id = identity.get('id')
        user_role = (identity.get('role') or '').lower()
        is_admin = user_role == 'admin'
        is_owner = getattr(song, 'uploader_id', None) == user_id
        if not (is_admin or is_owner):
            return jsonify({'msg': 'Bạn không có quyền sửa bài hát này'}), 403

        # Hỗ trợ multipart/form-data để cập nhật ảnh hoặc mp3
        if request.content_type and request.content_type.startswith('multipart/'):
            title = request.form.get('title', song.title)
            album_id = request.form.get('album_id') or song.album_id
            genre_id = request.form.get('genre_id') or song.genre_id
            artists_raw = request.form.get('artists', '[]')
            try:
                import json
                artist_ids = json.loads(artists_raw) if isinstance(artists_raw, str) else artists_raw
            except Exception:
                artist_ids = []

            # Lưu file nếu có
            if 'image' in request.files:
                image_file = request.files['image']
                saved = save_uploaded_image(image_file, 'images/songs')
                if saved and saved.startswith('static/'):
                    song.image_path = saved[len('static/'):]
                else:
                    song.image_path = saved
            if 'mp3' in request.files:
                mp3_file = request.files['mp3']
                mp3_saved = save_uploaded_image(mp3_file, 'music')
                if mp3_saved and mp3_saved.startswith('static/'):
                    song.mp3_path = mp3_saved[len('static/'):]
                else:
                    song.mp3_path = mp3_saved
        else:
            data = request.get_json() or {}
            title = data.get('title', song.title)
            album_id = data.get('album_id', song.album_id)
            genre_id = data.get('genre_id', song.genre_id)
            artist_ids = data.get('artists', [])

        song.title = title
        song.album_id = album_id
        song.genre_id = genre_id

        # Cập nhật nghệ sĩ
        if hasattr(song, 'artists'):
            # Some relationship configurations (e.g. lazy='dynamic') return a query-like
            # object that doesn't implement clear(). Attempt clear(), otherwise remove one-by-one.
            try:
                # preferred when artists is a collection
                song.artists.clear()
            except Exception:
                try:
                    for _a in list(song.artists):
                        song.artists.remove(_a)
                except Exception:
                    # last resort: set to empty list (works for normal collection-based relationships)
                    try:
                        song.artists = []
                    except Exception:
                        pass
            for artist_id in artist_ids:
                try:
                    aid = int(artist_id)
                except Exception:
                    continue
                artist = Artist.query.get(aid)
                if artist:
                    song.artists.append(artist)
        db.session.commit()
        return jsonify({'msg': 'Cập nhật bài hát thành công'}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'msg': 'Lỗi khi lưu bài hát: ' + str(e)}), 500

# Xóa bài hát
@admin_bp.route('/api/song/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_song(id):
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    user_id = identity.get('id')
    user_role = (identity.get('role') or '').lower()
    song = Song.query.get(id)
    if not song:
        return jsonify({'msg': 'Đã xóa hoặc không tồn tại'}), 200
    is_admin = user_role == 'admin'
    is_owner = getattr(song, 'uploader_id', None) == user_id
    if not (is_admin or is_owner):
        return jsonify({'msg': 'Bạn không có quyền xóa bài hát này'}), 403
    # Dọn dẹp thủ công bằng cách xóa từng đối tượng để chắc chắn trigger quan hệ đúng
    from src.models.music import Like, Comment, ListeningHistory, playlist_songs
    from src.models.song_rank_stats import SongRankStats
    # Xóa likes thông qua relationship nếu có
    if hasattr(song, 'likes'):
        for like in list(song.likes):
            db.session.delete(like)
    else:
        Like.query.filter_by(song_id=id).delete(synchronize_session=False)
    # Xóa comments
    if hasattr(song, 'comments'):
        for comment in list(song.comments):
            db.session.delete(comment)
    else:
        Comment.query.filter_by(song_id=id).delete(synchronize_session=False)
    # Xóa listening history
    ListeningHistory.query.filter_by(song_id=id).delete(synchronize_session=False)
    # Xóa playlist_songs qua câu lệnh thuần
    db.session.execute(playlist_songs.delete().where(playlist_songs.c.song_id == id))
    # Xóa bảng thống kê BXH liên quan
    SongRankStats.query.filter_by(song_id=id).delete(synchronize_session=False)
    # Xóa liên kết many-to-many song_artists
    if hasattr(song, 'artists') and song.artists is not None:
        for artist in list(song.artists):
            song.artists.remove(artist)
    # Sau khi dọn dẹp hết phụ thuộc, xóa bài hát
    db.session.delete(song)
    db.session.commit()
    return jsonify({'msg': 'Đã xóa bài hát'}), 200

# Route GET cho nghệ sĩ
@admin_bp.route('/api/artist/<int:id>', methods=['GET'])
@jwt_required()
def get_artist(id):
    artist = Artist.query.get(id)
    if not artist:
        return jsonify({'msg': 'Nghệ sĩ không tồn tại'}), 404
    return jsonify({
        'id': artist.id,
        'name': artist.name,
        'image_path': artist.image_path,
        'uploader_id': artist.uploader_id
    }), 200

# Route GET cho album
@admin_bp.route('/api/album/<int:id>', methods=['GET'])
@jwt_required()
def get_album(id):
    album = Album.query.get(id)
    if not album:
        return jsonify({'msg': 'Album không tồn tại'}), 404
    return jsonify({
        'id': album.id,
        'title': album.title,
        'artist_id': album.artist_id,
        'cover_image_path': album.cover_image_path,
        'uploader_id': album.uploader_id
    }), 200

# Route GET cho thể loại

@admin_bp.route('/api/users')
@jwt_required()
def api_list_users():
    users = get_all_users()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role
        } for u in users
    ])

@admin_bp.route('/users')
@jwt_required()
def manage_users_page():
    return render_template('manage_users.html')


@admin_bp.route('/api/users/<int:user_id>/role', methods=['POST'])
@jwt_required()
def api_set_user_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    user = User.query.get(user_id)
    if not user:
        print(f"[SetRole] User id {user_id} không tồn tại")
        return jsonify({'msg': 'User không tồn tại'}), 404
    print(f"[SetRole] User id {user_id} role trước: {user.role}")
    user.role = new_role
    db.session.commit()
    db.session.refresh(user)
    print(f"[SetRole] User id {user_id} role sau: {user.role}")
    return jsonify({'msg': 'Đã cập nhật role', 'role': user.role}), 200

# Route quản lý dữ liệu âm nhạc
@admin_bp.route('/music-data')
@jwt_required(optional=True)
def manage_music_data():
    # Lấy user từ JWT (nếu có)
    identity = current_identity()
    user = None
    if identity and identity.get('id'):
        user = User.query.get(identity.get('id'))
    # Lấy dữ liệu từ database
    artists = Artist.query.all()
    albums = Album.query.all()
    songs = Song.query.all()
    genres = Genre.query.all()
    return render_template(
        'manage_music_data.html',
        current_user=user,
        artists=artists,
        albums=albums,
        genres=genres
    )

@admin_bp.route('/')
def dashboard():
    artists = Artist.query.all()
    genres = Genre.query.all()
    songs = Song.query.all()
    return render_template('dashboard.html', artists=artists, genres=genres, songs=songs)

@admin_bp.route('/edit-song')
@jwt_required()
def edit_song_page():
    """Trang sửa bài hát"""
    identity = current_identity()
    if not identity:
        return redirect(url_for('auth.login_page'))
    user = User.query.get(identity.get('id'))
    if not user or (user.role or '').lower() not in ['admin', 'uploader']:
        flash('Bạn không có quyền sửa bài hát', 'error')
        return redirect(url_for('admin.dashboard'))
    return render_template('edit_song.html')

@admin_bp.route('/add_data', methods=['GET', 'POST'])
def add_data():
    genres = Genre.query.all()
    artists = Artist.query.all()

    if request.method == 'POST':
        data_type = request.form.get('data_type')

        try:
            if data_type == 'genre':
                name = request.form['genre_name']
                image_path = request.form['genre_image_path']
                color_class = request.form['genre_color_class']
                new_genre = Genre(name=name, image_path=image_path, color_class=color_class)
                db.session.add(new_genre)
                flash(f"Thêm thể loại '{name}' thành công!", "success")

            elif data_type == 'artist':
                name = request.form['artist_name']
                image_path = request.form['artist_image_path']
                new_artist = Artist(name=name, image_path=image_path)
                db.session.add(new_artist)
                flash(f"Thêm nghệ sĩ '{name}' thành công!", "success")

            elif data_type == 'song':
                title = request.form['song_title']
                mp3_path = request.form['song_mp3_path']
                artist_id = request.form['song_artist_id']
                genre_id = request.form['song_genre_id']
                new_song = Song(title=title, mp3_path=mp3_path, artist_id=artist_id, genre_id=genre_id)
                db.session.add(new_song)
                flash(f"Thêm bài hát '{title}' thành công!", "success")
            
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi thêm dữ liệu: {e}", "error")
        
        return redirect(url_for('admin.add_data'))

    return render_template('add_data.html', genres=genres, artists=artists)


# -------------------------------ss
# Admin API (JSON) - protected
# -------------------------------



@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    # Dùng JWT + check_admin để thống nhất xác thực
    admin_user = check_admin()
    print(f"[DEBUG] Admin user: {admin_user}")
    if not admin_user:
        print("[DEBUG] Không có quyền admin khi xóa user")
        return jsonify({'msg': 'Không có quyền'}), 403

    user = User.query.get(user_id)
    print(f"[DEBUG] User cần xóa: {user}")
    if not user:
        print("[DEBUG] User không tồn tại")
        return jsonify({'msg': 'User không tồn tại'}), 404

    # Không cho phép xóa super admin và chính mình
    if user.id == 1:
        print("[DEBUG] Không thể xóa Super Admin")
        return jsonify({'msg': 'Không thể xóa Super Admin'}), 400
    if user.id == admin_user.id:
        print("[DEBUG] Không thể tự xóa tài khoản đang đăng nhập")
        return jsonify({'msg': 'Không thể tự xóa tài khoản đang đăng nhập'}), 400

    try:
        print(f"[DeleteUser] Xóa user id {user.id}, username: {user.username}, role: {user.role}")
        db.session.delete(user)
        db.session.commit()
        print(f"[DeleteUser] Đã xóa user id {user.id}")
        return jsonify({'msg': 'Đã xóa user'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[DeleteUser] Lỗi server khi xóa: {e}")
        return jsonify({'msg': 'Lỗi server khi xóa', 'detail': str(e)}), 500


# CRUD for Genre/Artist/Album/Song (support file upload)
@admin_bp.route('/api/genre', methods=['POST'])
@jwt_required()
def create_genre():
    # Admin hoặc uploader được thêm thể loại
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    user_id = identity.get('id')
    user_role = (identity.get('role') or '').lower()
    if user_role not in ['admin','uploader']:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    # Accept form-data instead of JSON
    name = request.form.get('name')
    if not name:
        return jsonify({'msg': 'Thiếu tên'}), 400
    
    # Handle image upload
    image_file = request.files.get('image')
    image_path = save_uploaded_image(image_file, 'images/genres') if image_file else None
    
    # Random color class từ danh sách các gradient
    color_options = [
        'blue-gradient', 'purple-gradient', 'green-gradient', 
        'red-gradient', 'orange-gradient', 'pink-gradient',
        'yellow-gradient', 'teal-gradient', 'indigo-gradient'
    ]
    color_class = random.choice(color_options)
    
    g = Genre(name=name, image_path=image_path, color_class=color_class, uploader_id=user_id)
    db.session.add(g)
    db.session.commit()
    return jsonify({'msg': 'Đã tạo thể loại thành công', 'id': g.id}), 201


@admin_bp.route('/api/genre/<int:id>', methods=['GET', 'PUT','DELETE'])
@jwt_required()
def modify_genre(id):
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    user_id = identity.get('id')
    user_role = (identity.get('role') or '').lower()
    is_admin = user_role == 'admin'
    
    g = Genre.query.get(id)
    if not g:
        return jsonify({'msg': 'Thể loại không tồn tại'}), 404
    
    # Kiểm tra quyền sở hữu hoặc admin
    is_owner = hasattr(g, 'uploader_id') and g.uploader_id == user_id
    if request.method in ['PUT','DELETE'] and not (is_admin or is_owner):
        return jsonify({'msg': 'Không có quyền sửa/xóa thể loại này'}), 403
    # GET: Lấy thông tin chi tiết thể loại
    if request.method == 'GET':
        return jsonify({
            'id': g.id,
            'name': g.name,
            'image_path': g.image_path,
            'color_class': g.color_class
        }), 200
    
    if request.method == 'DELETE':
        db.session.delete(g)
        db.session.commit()
        return jsonify({'msg':'Đã xóa thể loại'}),200
    
    # PUT: Cập nhật thông tin thể loại
    # Hỗ trợ cả JSON và form-data (với file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Form-data với file upload
        if request.form.get('name'):
            g.name = request.form.get('name')
        if request.form.get('color_class'):
            g.color_class = request.form.get('color_class')
        
        # Upload ảnh mới nếu có
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_path = save_uploaded_image(image_file, 'images/genres')
            if image_path:
                g.image_path = image_path
    else:
        # JSON
        data = request.get_json() or {}
        g.name = data.get('name', g.name)
        g.image_path = data.get('image_path', g.image_path)
        g.color_class = data.get('color_class', g.color_class)
    
    db.session.commit()
    return jsonify({'msg':'Đã cập nhật'}),200


@admin_bp.route('/api/artist', methods=['POST'])
@jwt_required()
def create_artist():
    # Admin hoặc uploader có thể thêm nghệ sĩ
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user or (user.role or '').lower() not in ['admin', 'uploader']:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    # Accept form-data
    name = request.form.get('name')
    if not name:
        return jsonify({'msg':'Thiếu tên nghệ sĩ'}),400
    
    # Handle image upload
    image_file = request.files.get('image')
    image_path = save_uploaded_image(image_file, 'images/artists') if image_file else None
    
    a = Artist(name=name, image_path=image_path, uploader_id=user_id)
    db.session.add(a)
    db.session.commit()
    return jsonify({'id': a.id, 'msg':'Đã tạo nghệ sĩ thành công'}),201


@admin_bp.route('/api/artist/<int:id>', methods=['PUT','DELETE'])
@jwt_required()
def modify_artist(id):
    # Admin hoặc uploader (chỉ xóa nghệ sĩ của mình) có thể xóa
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    a = Artist.query.get(id)
    if not a:
        return jsonify({'msg':'Nghệ sĩ không tồn tại'}),404
    
    # Kiểm tra quyền: Admin xóa được tất cả, uploader chỉ xóa được nghệ sĩ của mình
    is_admin = (user.role or '').lower() == 'admin'
    is_owner = hasattr(a, 'uploader_id') and a.uploader_id == user_id
    
    if not is_admin and not is_owner:
        return jsonify({'msg': 'Bạn không có quyền xóa nghệ sĩ này'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(a)
        db.session.commit()
        return jsonify({'msg':'Đã xóa nghệ sĩ'}),200
    # Hỗ trợ cập nhật qua form-data (có thể có file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        if request.form.get('name'):
            a.name = request.form.get('name')
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_path = save_uploaded_image(image_file, 'images/artists')
            if image_path:
                a.image_path = image_path
    else:
        data = request.get_json() or {}
        a.name = data.get('name', a.name)
        a.image_path = data.get('image_path', a.image_path)
    db.session.commit()
    return jsonify({'msg':'Đã cập nhật'}),200


@admin_bp.route('/api/song', methods=['POST'])
@admin_bp.route('/api/songs', methods=['POST'])  # Support both /song and /songs
@jwt_required()
def create_song():
    # Admin hoặc uploader có thể thêm bài hát
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user or (user.role or '').lower() not in ['admin', 'uploader']:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    # Accept form-data with file upload
    title = request.form.get('title')
    if not title:
        return jsonify({'msg':'Thiếu tiêu đề'}),400
    
    # Handle MP3 file upload
    mp3_file = request.files.get('mp3')
    if not mp3_file:
        return jsonify({'msg':'Thiếu file MP3'}),400
    
    # Save MP3 file to static/music
    mp3_saved = save_uploaded_image(mp3_file, 'music')
    if not mp3_saved:
        return jsonify({'msg':'Lỗi lưu file MP3'}),500
    # strip leading static/
    mp3_path = mp3_saved[len('static/'): ] if mp3_saved.startswith('static/') else mp3_saved

    # Handle optional image file upload (save to static/images/songs)
    image_file = request.files.get('image')
    image_path = None
    if image_file and image_file.filename:
        saved_img = save_uploaded_image(image_file, 'images/songs')
        image_path = saved_img[len('static/'): ] if saved_img and saved_img.startswith('static/') else saved_img
    
    artist_id = request.form.get('artist_id')
    artist_ids = request.form.get('artist_ids')  # Chấp nhận nhiều artist IDs (comma-separated)
    album_id = request.form.get('album_id')
    genre_id = request.form.get('genre_id')
    
    s = Song(
        title=title,
        mp3_path=mp3_path,
        image_path=image_path,
        artist_id=int(artist_id) if artist_id else None,  # Nghệ sĩ chính
        genre_id=int(genre_id) if genre_id else None,
        album_id=int(album_id) if album_id else None,
        uploader_id=user_id
    )
    db.session.add(s)
    db.session.flush()  # Lấy ID trước khi commit
    
    # Thêm các nghệ sĩ vào many-to-many relationship
    if artist_ids:
        # artist_ids có thể là "1,2,3" hoặc array từ JSON
        if isinstance(artist_ids, str):
            artist_id_list = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
        else:
            artist_id_list = artist_ids
        
        from src.models.music import Artist



        for aid in artist_id_list:
            artist = Artist.query.get(aid)


            s.artists.append(artist)
    


    if not identity:

        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    s = Song.query.get(id)
    if not s:
        return jsonify({'msg':'Bài hát không tồn tại'}),404
    
    # GET: Lấy thông tin chi tiết bài hát (để hiển thị trong form sửa)
    if request.method == 'GET':
        return jsonify({
            'id': s.id,
            'title': s.title,
            'mp3_path': s.mp3_path,
            'image_path': s.image_path,
            'artist_id': s.artist_id,
            'artist_name': s.artist_name,
            'artists': [{'id': a.id, 'name': a.name} for a in s.artists.all()],
            'album_id': s.album_id,
            'album_title': s.album.title if s.album else None,
            'genre_id': s.genre_id,
            'genre_name': s.genre.name if s.genre else None,
            'uploader_id': s.uploader_id,
            'created_at': s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at else None
        }), 200
    
    # Kiểm tra quyền: Admin xóa được tất cả, uploader chỉ xóa được bài hát của mình
    is_admin = (user.role or '').lower() == 'admin'
    is_owner = hasattr(s, 'uploader_id') and s.uploader_id == user_id
    
    if not is_admin and not is_owner:
        return jsonify({'msg': 'Bạn không có quyền sửa/xóa bài hát này'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return jsonify({'msg':'Đã xóa bài hát'}),200
    
    # PUT: Cập nhật thông tin bài hát
    # Hỗ trợ cả JSON và form-data (với file upload)
    
    print(f"[DEBUG] PUT request for song {id}")
    print(f"[DEBUG] Content-Type: {request.content_type}")
    print(f"[DEBUG] Files: {request.files}")
    print(f"[DEBUG] Form: {request.form}")
    
    # Nếu có form-data (file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Cập nhật tên bài hát
        if request.form.get('title'):
            s.title = request.form.get('title')

        # Cập nhật MP3 nếu có upload file mới
        mp3_file = request.files.get('mp3')
        if mp3_file and mp3_file.filename:
            mp3_saved = save_uploaded_image(mp3_file, 'music')
            if mp3_saved:
                new_mp3 = mp3_saved[len('static/'): ] if mp3_saved.startswith('static/') else mp3_saved
                s.mp3_path = new_mp3
                print(f"[DEBUG] Updated mp3_path: {new_mp3}")

        # Cập nhật ảnh bài hát nếu có upload
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_saved = save_uploaded_image(image_file, 'images/songs')
            if image_saved:
                new_img = image_saved[len('static/'): ] if image_saved.startswith('static/') else image_saved
                s.image_path = new_img
                print(f"[DEBUG] Updated image_path: {new_img}")
        
        # Cập nhật artist_id, album_id, genre_id
        if request.form.get('artist_id'):
            s.artist_id = int(request.form.get('artist_id'))
        if request.form.get('album_id'):
            s.album_id = int(request.form.get('album_id'))
        if request.form.get('genre_id'):
            s.genre_id = int(request.form.get('genre_id'))
        
        # Cập nhật danh sách nghệ sĩ (many-to-many)
        artist_ids = request.form.get('artist_ids')
        if artist_ids:
            # Xóa tất cả nghệ sĩ hiện tại
            current_artists = list(s.artists.all())
            for artist in current_artists:
                s.artists.remove(artist)
            
            # Thêm nghệ sĩ mới
            if isinstance(artist_ids, str):
                artist_id_list = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
            else:
                artist_id_list = artist_ids
            
            from src.models.music import Artist
            for aid in artist_id_list:
                artist = Artist.query.get(aid)
                if artist:
                    s.artists.append(artist)
    
    else:
        # JSON request
        data = request.get_json() or {}
        
        # Cập nhật các trường cơ bản
        if 'title' in data:
            s.title = data['title']
        if 'mp3_path' in data:
            s.mp3_path = data['mp3_path']
        if 'image_path' in data:
            s.image_path = data['image_path']
        if 'artist_id' in data:
            s.artist_id = data['artist_id']
        if 'genre_id' in data:
            s.genre_id = data['genre_id']
        if 'album_id' in data:
            s.album_id = data['album_id']
        
        # Cập nhật danh sách nghệ sĩ
        if 'artist_ids' in data:
            artist_ids = data['artist_ids']
            
            # Xóa tất cả nghệ sĩ hiện tại
            current_artists = list(s.artists.all())
            for artist in current_artists:
                s.artists.remove(artist)
            
            # Thêm nghệ sĩ mới
            if isinstance(artist_ids, str):
                artist_id_list = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
            else:
                artist_id_list = artist_ids
            
            from src.models.music import Artist
            for aid in artist_id_list:
                artist = Artist.query.get(aid)
                if artist:
                    s.artists.append(artist)
    
    db.session.commit()
    
    # Trả về thông tin bài hát đã cập nhật
    return jsonify({
        'msg': 'Đã cập nhật bài hát',
        'song': {
            'id': s.id,
            'title': s.title,
            'mp3_path': s.mp3_path,
            'image_path': s.image_path,
            'artist_id': s.artist_id,
            'artist_name': s.artist_name,
            'artists': [{'id': a.id, 'name': a.name} for a in s.artists.all()],
            'album_id': s.album_id,
            'genre_id': s.genre_id
        }
    }), 200


@admin_bp.route('/api/album', methods=['POST'])
@jwt_required()
def create_album():
    # Admin hoặc uploader có thể tạo album
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user or (user.role or '').lower() not in ['admin', 'uploader']:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    # Accept form-data
    title = request.form.get('title')
    artist_id = request.form.get('artist_id')
    if not title:
        return jsonify({'msg':'Thiếu tên album'}),400
    
    # Handle image upload
    image_file = request.files.get('image')
    cover_image_path = save_uploaded_image(image_file, 'images/albums') if image_file else None
    
    al = Album(
        title=title,
        artist_id=int(artist_id) if artist_id else None,
        cover_image_path=cover_image_path,
        uploader_id=user_id
    )
    db.session.add(al)
    db.session.commit()
    return jsonify({'id': al.id, 'msg':'Đã tạo album thành công'}),201


@admin_bp.route('/api/album/<int:id>', methods=['PUT','DELETE'])
@jwt_required()
def modify_album(id):
    identity = current_identity()
    if not identity:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    user_id = identity.get('id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Không có quyền'}), 403
    
    al = Album.query.get(id)
    if not al:
        return jsonify({'msg':'Album không tồn tại'}),404
    
    # Kiểm tra quyền: Admin xóa được tất cả, uploader chỉ xóa được album của mình
    is_admin = (user.role or '').lower() == 'admin'
    is_owner = hasattr(al, 'uploader_id') and al.uploader_id == user_id
    
    if not is_admin and not is_owner:
        return jsonify({'msg': 'Bạn không có quyền xóa album này'}), 403
    
    if request.method == 'DELETE':
        db.session.delete(al)
        db.session.commit()
        return jsonify({'msg':'Đã xóa album'}),200
    
    # Hỗ trợ cập nhật qua form-data (có thể có file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        if request.form.get('title'):
            al.title = request.form.get('title')
        if request.form.get('artist_id'):
            al.artist_id = int(request.form.get('artist_id'))
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            cover_image_path = save_uploaded_image(image_file, 'images/albums')
            if cover_image_path:
                al.cover_image_path = cover_image_path
    else:
        data = request.get_json() or {}
        al.title = data.get('title', al.title)
        if 'artist_id' in data:
            al.artist_id = data['artist_id']
        if 'cover_image_path' in data:
            al.cover_image_path = data['cover_image_path']
    db.session.commit()
    return jsonify({'msg':'Đã cập nhật'}),200

# --- API tìm kiếm thể loại realtime (autocomplete) ---
@admin_bp.route('/api/genre/search', methods=['GET'])
@jwt_required()
def search_genre():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify(genres=[])
    genres = Genre.query.filter(Genre.name.ilike(f'%{keyword}%')).all()
    result = [
        {
            'id': g.id,
            'name': g.name,
            'color_class': getattr(g, 'color_class', None),
            'image_path': getattr(g, 'image_path', None)
        }
        for g in genres
    ]
    return jsonify(genres=result)

# --- API tìm kiếm bài hát realtime (autocomplete) ---
@admin_bp.route('/api/song/search', methods=['GET'])
@jwt_required()
def search_song():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify(songs=[])
    songs = Song.query.filter(Song.title.ilike(f'%{keyword}%')).all()
    result = [
        {
            'id': s.id,
            'title': s.title,
            'image_path': getattr(s, 'image_path', None)
        }
        for s in songs
    ]
    return jsonify(songs=result)

# --- API tìm kiếm nghệ sĩ realtime (autocomplete) ---
@admin_bp.route('/api/artist/search', methods=['GET'])
@jwt_required()
def search_artist():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify(artists=[])
    artists = Artist.query.filter(Artist.name.ilike(f'%{keyword}%')).all()
    result = [
        {
            'id': a.id,
            'name': a.name,
            'image_path': getattr(a, 'image_path', None)
        }
        for a in artists
    ]
    return jsonify(artists=result)

# --- API tìm kiếm album realtime (autocomplete) ---
@admin_bp.route('/api/album/search', methods=['GET'])
@jwt_required()
def search_album():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify(albums=[])
    albums = Album.query.filter(Album.title.ilike(f'%{keyword}%')).all()
    result = [
        {
            'id': al.id,
            'title': al.title,
            'image_path': getattr(al, 'cover_image_path', None)
        }
        for al in albums
    ]
    return jsonify(albums=result)

@admin_bp.route('/ads/manage', methods=['GET', 'POST'])
@jwt_required()
def ads_manage():
    admin = check_admin()
    if not admin:
        return render_template('admin/no_permission.html'), 403
    from src.models.music import Ad
    from src.extensions import db
    import os
    msg = None
    if request.method == 'POST':
        title = request.form.get('title')
        link = request.form.get('link')
        active = bool(int(request.form.get('active', 1)))
        image_file = request.files.get('image')
        mp3_file = request.files.get('mp3')
        mp4_file = request.files.get('mp4')
        image_url = mp3_path = mp4_path = None
        # Lưu file ảnh
        if image_file and image_file.filename:
            img_name = 'ad_' + image_file.filename
            img_path = os.path.join('static', 'images', 'ads', img_name)
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            image_file.save(img_path)
            image_url = f'images/ads/{img_name}'
        # Lưu file mp3
        if mp3_file and mp3_file.filename:
            mp3_name = 'ad_' + mp3_file.filename
            mp3_path_full = os.path.join('static', 'ads', mp3_name)
            os.makedirs(os.path.dirname(mp3_path_full), exist_ok=True)
            mp3_file.save(mp3_path_full)
            mp3_path = f'ads/{mp3_name}'
        # Lưu file mp4
        if mp4_file and mp4_file.filename:
            mp4_name = 'ad_' + mp4_file.filename
            mp4_path_full = os.path.join('static', 'ads', mp4_name)
            os.makedirs(os.path.dirname(mp4_path_full), exist_ok=True)
            mp4_file.save(mp4_path_full)
            mp4_path = f'ads/{mp4_name}'
        ad = Ad(title=title, link=link, image_url=image_url, mp3_path=mp3_path, mp4_path=mp4_path, active=active)
        db.session.add(ad)
        db.session.commit()
        msg = 'Đã thêm quảng cáo!'
    ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return render_template('admin/ads_manage.html', ads=ads, msg=msg)