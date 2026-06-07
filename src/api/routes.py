from flask import Blueprint, jsonify, request
from src.extensions import db
from src.models.music import Genre, Artist, Song, Album, Playlist, ListeningHistory, Ad
from src.models.song_rank_stats import SongRankStats
from src.models.user import User

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ... (giữ nguyên các route và logic khác ở đây)

# Thêm endpoint like-status SAU khi api_bp đã được khởi tạo
from flask_jwt_extended import jwt_required
from src.jwt_helper import current_identity

@api_bp.route('/song/<int:song_id>/like-status', methods=['GET'])
@jwt_required(optional=True)
def get_song_like_status(song_id):
    """Trả về trạng thái like và số lượng like cho bài hát với user hiện tại."""
    from src.models.music import Song, Like
    song = Song.query.get_or_404(song_id)
    user = current_identity()
    like_count = Like.query.filter_by(song_id=song_id).count()
    liked = False
    if user and user.get('id'):
        liked = Like.query.filter_by(song_id=song_id, user_id=user['id']).first() is not None
    return jsonify({
        'liked': liked,
        'like_count': like_count
    })
from flask import Blueprint, jsonify, request
from src.extensions import db
from src.models.music import Genre, Artist, Song, Album, Playlist, ListeningHistory
from src.models.song_rank_stats import SongRankStats
from src.models.user import User
from sqlalchemy import func
import datetime as dt


# === NGHỆ SĨ ĐANG NỔI (TRENDING ARTISTS) ===
# Đặt sau khi api_bp đã được khởi tạo

from flask_jwt_extended import jwt_required
from src.jwt_helper import current_identity
from src.decorators import admin_required, uploader_or_admin_required # ✅ Import "người gác cổng"
from src.models.user import User

api_bp = Blueprint('api', __name__, url_prefix='/api')


def serialize_song(song):
    # Đảm bảo trả về đầy đủ thông tin, tránh lỗi khi liên kết bị thiếu
    artist_name = None
    try:
        if hasattr(song, 'artist_name') and song.artist_name:
            artist_name = song.artist_name
        elif song.artist:
            artist_name = song.artist.name
    except Exception:
        artist_name = None
    album_title = None
    try:
        if song.album:
            album_title = song.album.title
    except Exception:
        album_title = None
    genre_name = None
    try:
        if song.genre:
            genre_name = song.genre.name
    except Exception:
        genre_name = None
    return {
        'id': song.id,
        'title': song.title,
        'mp3_path': song.mp3_path,
        'mp3_url': getattr(song, 'mp3_url', song.mp3_path),
        'artist_name': artist_name,
        'genre_name': genre_name,
        'artist_id': song.artist_id,
        'album_id': song.album_id,
        'album_title': album_title
    }
# --- API Quảng cáo ---
@api_bp.route('/ads', methods=['GET'])
def get_ads():
    ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return jsonify([
        {
            'id': ad.id,
            'title': ad.title,
            'image_url': ad.image_url,
            'link': ad.link,
            'mp3_path': ad.mp3_path,
            'active': ad.active
        } for ad in ads
    ])

@api_bp.route('/ads', methods=['POST'])
@admin_required()
def create_ad():
    # Xử lý nhận form, lưu file, tạo Ad mới
    # ... (code xử lý upload và lưu vào DB)
    return jsonify(msg='Thêm quảng cáo thành công'), 201

# ...existing code...

# === NGHỆ SĨ ĐANG NỔI (TRENDING ARTISTS) ===
@api_bp.route('/trending-artists')
def trending_artists():
    try:
        now = dt.datetime.now()
        week = int(now.strftime('%U'))
        prev_week = week - 1 if week > 0 else 52
        month = now.month
        year = now.year
        prev_month = month - 1 if month > 1 else 12
        prev_month_year = year if month > 1 else year - 1

        # Lấy tất cả nghệ sĩ
        artists = Artist.query.all()
        trending = []
        for artist in artists:
            # --- Lượt nghe tuần này và tuần trước ---
            song_ids = [s.id for s in artist.songs]
            if not song_ids:
                continue  # Bỏ qua nghệ sĩ chưa có bài hát
            week_plays = db.session.query(func.sum(SongRankStats.week_plays)).filter(SongRankStats.song_id.in_(song_ids), SongRankStats.week==week, SongRankStats.year==year).scalar() or 0
            prev_week_plays = db.session.query(func.sum(SongRankStats.week_plays)).filter(SongRankStats.song_id.in_(song_ids), SongRankStats.week==prev_week, SongRankStats.year==year).scalar() or 0
            week_growth = week_plays - prev_week_plays

            # --- Lượt follow mới (tuần này) ---
            follower_count = artist.followers.count()
            # Giả sử không có bảng log follow/unfollow, chỉ lấy tổng số hiện tại

            # --- Số lần được thêm vào playlist (tổng số playlist chứa bài của artist) ---
            playlist_count = db.session.query(Playlist).join(Playlist.songs).filter(Song.id.in_(song_ids)).distinct().count()

            # --- Số lượt tìm kiếm (giả sử chưa có bảng log search, bỏ qua hoặc random demo) ---
            search_count = 0  # Nếu có bảng log search thì lấy ở đây

            # --- Thời gian debut (ưu tiên nghệ sĩ mới) ---
            # Giả sử không có trường debut, dùng id nhỏ là cũ, id lớn là mới
            debut_score = 1.0 / (artist.id or 1)

            # --- Tính điểm tổng hợp ---
            score = (
                week_growth * 2 +  # tăng trưởng lượt nghe (ưu tiên)
                follower_count * 1.5 +
                playlist_count * 1.2 +
                search_count * 1.0 +
                debut_score * 100  # nghệ sĩ mới nổi
            )
            trending.append({
                'id': artist.id,
                'name': artist.name,
                'image_path': artist.image_path,
                'score': round(score, 2),
                'week_plays': week_plays,
                'prev_week_plays': prev_week_plays,
                'week_growth': week_growth,
                'follower_count': follower_count,
                'playlist_count': playlist_count,
                'search_count': search_count,
                'debut_score': round(debut_score, 3)
            })
        # Sắp xếp theo điểm giảm dần, lấy top 10
        trending.sort(key=lambda x: x['score'], reverse=True)
        return jsonify(trending[:10])
    except Exception as e:
        import traceback
        print("[TRENDING ARTISTS ERROR]", e)
        traceback.print_exc()
        return jsonify([]), 200
from flask_jwt_extended import jwt_required
from src.jwt_helper import current_identity
from src.decorators import admin_required, uploader_or_admin_required # ✅ Import "người gác cổng"
from src.models.user import User

api_bp = Blueprint('api', __name__, url_prefix='/api')



# --- Hàm hỗ trợ chuyển đổi Model object thành Dictionary ---
def serialize_song(song):
    return {
        'id': song.id,
        'title': song.title,
        'mp3_path': song.mp3_path,
        'mp3_url': getattr(song, 'mp3_url', song.mp3_path),
        'artist_name': song.artist.name if song.artist else None,
        'genre_name': song.genre.name if song.genre else None,
        'artist_id': song.artist_id,
        'album_id': song.album_id,
        'album_title': song.album.title if song.album else None
    }

def serialize_artist(artist):
    # Trả về đúng image_path từ DB, không tự động chuyển None/"None" thành default ở backend
    # Đảm bảo image_path không có /static/ ở đầu, chỉ trả về đường dẫn con bên trong static
    img = artist.image_path
    if img in [None, "None", ""]:
        img = None
    elif img.startswith("/static/"):
        img = img[len("/static/"):]
    return {
        'id': artist.id,
        'name': artist.name,
        'image_path': img
    }

def serialize_genre(genre):
    # Trả về đúng image_path từ DB, không tự động chuyển None/"None" thành default ở backend
    img = genre.image_path
    if img in [None, "None", ""]:
        img = None
    elif img.startswith("/static/"):
        img = img[len("/static/"):]
    return {
        'id': genre.id,
        'name': genre.name,
        'image_path': img,
        'color_class': genre.color_class
    }

# --- Các API Endpoint ---

@api_bp.route('/genres')
def get_genres():
    """Trả về danh sách tất cả các thể loại."""
    genres = Genre.query.all()
    return jsonify([serialize_genre(g) for g in genres])

@api_bp.route('/artists')
def get_artists():
    """Trả về danh sách tất cả các nghệ sĩ."""
    artists = Artist.query.all()
    return jsonify([serialize_artist(a) for a in artists])

@api_bp.route('/artist/<int:id>')
def get_artist_detail(id):
    """Trả về thông tin chi tiết của một nghệ sĩ và các bài hát của họ."""
    artist = Artist.query.get_or_404(id)
    song_list = list(artist.songs)
    song_ids = [s.id for s in song_list]
    listen_counts = {}
    if song_ids:
        counts = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in counts}
    songs = []
    for s in song_list:
        d = serialize_song(s)
        d['listen_count'] = int(listen_counts.get(s.id, 0))
        songs.append(d)
    return jsonify({
        'id': artist.id,
        'name': artist.name,
        'image_path': artist.image_path,
        'songs': songs
    })

@api_bp.route('/genre/<int:id>')
def get_genre_detail(id):
    """Trả về thông tin chi tiết của một thể loại và các bài hát của nó."""
    genre = Genre.query.get_or_404(id)
    song_list = list(genre.songs)
    song_ids = [s.id for s in song_list]
    listen_counts = {}
    if song_ids:
        counts = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in counts}
    songs = []
    for s in song_list:
        d = serialize_song(s)
        d['listen_count'] = int(listen_counts.get(s.id, 0))
        songs.append(d)
    return jsonify({
        'id': genre.id,
        'name': genre.name,
        'image_path': genre.image_path,
        'color_class': genre.color_class,
        'songs': songs
    })

@api_bp.route('/songs')
def get_songs():
    """Trả về danh sách tất cả các bài hát."""
    songs = list(Song.query.all())
    song_ids = [s.id for s in songs]
    listen_counts = {}
    if song_ids:
        counts = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in counts}
    out = []
    for s in songs:
        d = serialize_song(s)
        d['listen_count'] = int(listen_counts.get(s.id, 0))
        out.append(d)
    return jsonify(out)


@api_bp.route('/songs/search')
def search_songs():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Song.query.filter(Song.title.ilike(f"%{q}%")).all()
    return jsonify([serialize_song(s) for s in results])

@api_bp.route('/song/<int:id>')
def get_song_detail(id):
    """Trả về thông tin chi tiết của một bài hát."""
    song = Song.query.get_or_404(id)
    total = db.session.query(func.count()).select_from(ListeningHistory).filter_by(song_id=song.id).scalar() or 0
    d = serialize_song(song)
    d['listen_count'] = int(total)
    return jsonify(d)

@api_bp.route('/album/<int:id>')
def get_album_detail(id):
    album = Album.query.get_or_404(id)
    song_list = list(album.songs)
    song_ids = [s.id for s in song_list]
    listen_counts = {}
    if song_ids:
        counts = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in counts}
    songs = []
    for s in song_list:
        d = serialize_song(s)
        d['listen_count'] = int(listen_counts.get(s.id, 0))
        songs.append(d)
    return jsonify({
        'id': album.id,
        'name': album.title, # Trả về key 'name' cho thống nhất
        'image_path': album.cover_image_path if album.cover_image_path not in [None, "None", ""] else None,
        # Thêm tên nghệ sĩ của album
        'artist_name': album.artist.name if album.artist else 'Nhiều nghệ sĩ',
        'songs': songs
    })


@api_bp.route('/albums')
def get_albums():
    albums = Album.query.all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'artist_id': a.artist_id,
            'artist_name': a.artist.name if a.artist else None,
            'release_year': a.release_year,
            'cover_image_path': a.cover_image_path if a.cover_image_path not in [None, "None", ""] else None
        } for a in albums
    ])


@api_bp.route('/albums/search')
def search_albums():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Album.query.filter(Album.title.ilike(f"%{q}%")).all()
    return jsonify([
        {
            'id': a.id,
            'title': a.title,
            'artist_id': a.artist_id,
            'artist_name': a.artist.name if a.artist else None,
            'release_year': a.release_year,
            'cover_image_path': a.cover_image_path if a.cover_image_path not in [None, "None", ""] else None
        } for a in results
    ])

# === API CHO UPLOADER & ADMIN ===

@api_bp.route('/songs', methods=['POST'])
@uploader_or_admin_required() # Chỉ uploader hoặc admin được vào
def upload_song():
    identity = current_identity()
    uploader_id = identity.get('id')
    # ... (Code xử lý upload file và lấy dữ liệu từ request.form) ...
    # new_song = Song(..., uploader_id=uploader_id)
    # db.session.add(new_song)
    # db.session.commit()
    return jsonify(msg="Upload thành công!"), 201

@api_bp.route('/song/<int:song_id>', methods=['DELETE'])
@jwt_required() # Bất cứ ai đăng nhập cũng có thể thử xóa, nhưng logic bên trong sẽ kiểm tra
def delete_song(song_id):
    identity = current_identity()
    song = Song.query.get(song_id)
    # Idempotent: nếu không còn => coi như đã xóa (tránh lỗi khi double request)
    if not song:
        return jsonify(msg="Đã xóa bài hát hoặc không tồn tại"), 200
    # Logic kiểm tra quyền: Phải là admin hoặc là người đã upload bài hát này
    if identity.get('role') == 'admin' or song.uploader_id == identity.get('id'):
        db.session.delete(song)
        db.session.commit()
        return jsonify(msg="Xóa bài hát thành công"), 200
    return jsonify(msg="Bạn không có quyền xóa bài hát này"), 403

# === API CHO USER (LISTENER) ===

@api_bp.route('/playlists', methods=['POST'])
@jwt_required()
def create_playlist():
    identity = current_identity()
    user_id = identity.get('id')
    data = request.get_json()
    # Use provided cover_image_path when present, otherwise fallback to default
    cover = None
    if data:
        cover = data.get('cover_image_path')
    if not cover:
        cover = 'images/playlist_image.png'
    new_playlist = Playlist(name=data['name'], user_id=user_id, cover_image_path=cover)
    db.session.add(new_playlist)
    db.session.commit()
    return jsonify(msg=f"Đã tạo playlist '{data['name']}'"), 201


@api_bp.route('/playlists/<int:playlist_id>', methods=['PUT'])
@jwt_required()
def update_playlist(playlist_id):
    """Update playlist info (name, description, is_public)"""
    identity = current_identity()
    user_id = identity.get('id')
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Only owner can update playlist
    if playlist.user_id != user_id:
        return jsonify(msg="Bạn không có quyền cập nhật playlist này"), 403
    
    data = request.get_json() or {}
    if 'name' in data:
        playlist.name = data['name']
    if 'description' in data:
        playlist.description = data['description']
    if 'is_public' in data:
        playlist.is_public = bool(data['is_public'])
    
    db.session.commit()
    return jsonify(msg='Cập nhật playlist thành công', playlist={'id': playlist.id, 'name': playlist.name, 'is_public': playlist.is_public}), 200


# Đã có route /api/history/log trong history_bp (listening_history_routes.py), không định nghĩa trùng ở đây.



@api_bp.route('/song/<int:song_id>', methods=['PUT'])
@uploader_or_admin_required()
def update_song(song_id):
    song = Song.query.get_or_404(song_id)
    identity = current_identity()
    # Only admin or uploader (owner) can update
    if identity.get('role') != 'admin' and getattr(song, 'uploader_id', None) != identity.get('id'):
        return jsonify(msg="Bạn không có quyền cập nhật bài hát này"), 403

    data = request.get_json() or {}
    for field in ('title', 'mp3_path', 'artist_id', 'genre_id', 'album_id'):
        if field in data:
            setattr(song, field, data[field])

    db.session.commit()
    return jsonify(msg="Cập nhật bài hát thành công", song=serialize_song(song)), 200


@api_bp.route('/artist/<int:artist_id>', methods=['PUT'])
@admin_required()
def update_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    data = request.get_json() or {}
    if 'name' in data:
        artist.name = data['name']
    if 'image_path' in data:
        artist.image_path = data['image_path']
    db.session.commit()
    return jsonify(msg='Cập nhật nghệ sĩ thành công', artist=serialize_artist(artist)), 200


@api_bp.route('/artist/<int:artist_id>', methods=['DELETE'])
@admin_required()
def delete_artist(artist_id):
    # Idempotent delete: nếu không tìm thấy vẫn trả về 200 để tránh lỗi double request
    artist = Artist.query.get(artist_id)
    if not artist:
        return jsonify(msg='Đã xóa nghệ sĩ hoặc không tồn tại'), 200
    from src.models.music import Song, song_artists
    # Xóa liên kết many-to-many trước
    m2m_songs = artist.songs.all() if hasattr(artist.songs, 'all') else list(artist.songs)
    for song in m2m_songs:
        # Nếu nghệ sĩ là nghệ sĩ chính và KHÔNG còn nghệ sĩ nào khác, xóa luôn bài hát
        other_artists = [a for a in song.artists if a.id != artist.id]
        if song.artist_id == artist.id and len(other_artists) == 0:
            db.session.delete(song)
        else:
            # Xóa liên kết many-to-many giữa bài hát và nghệ sĩ này
            song.artists.remove(artist)
    # Xóa các bài hát mà nghệ sĩ là chính và không có nghệ sĩ phụ (trường hợp không nằm trong m2m)
    main_songs = Song.query.filter_by(artist_id=artist.id).all()
    for song in main_songs:
        if song not in m2m_songs:
            db.session.delete(song)
    # Xóa tất cả album của nghệ sĩ này
    for album in artist.albums:
        db.session.delete(album)
    db.session.delete(artist)
    db.session.commit()
    return jsonify(msg='Đã xóa nghệ sĩ, các bài hát chỉ thuộc nghệ sĩ này và album liên quan'), 200


@api_bp.route('/album/<int:album_id>', methods=['PUT'])
@admin_required()
def update_album(album_id):
    album = Album.query.get_or_404(album_id)
    data = request.get_json() or {}
    for field in ('title', 'artist_id', 'release_year', 'cover_image_path'):
        if field in data:
            setattr(album, field, data[field])
    db.session.commit()
    return jsonify(msg='Cập nhật album thành công', album={'id': album.id, 'title': album.title}), 200


@api_bp.route('/album/<int:album_id>', methods=['DELETE'])
@admin_required()
def delete_album(album_id):
    # Idempotent delete: nếu album không tồn tại coi như đã xóa
    album = Album.query.get(album_id)
    if not album:
        return jsonify(msg='Đã xóa album hoặc không tồn tại'), 200
    if album.songs:
        return jsonify(msg='Không thể xóa album đang có bài hát'), 400
    db.session.delete(album)
    db.session.commit()
    return jsonify(msg='Đã xóa album'), 200


# === CRUD cho Genre (admin) ===
@api_bp.route('/genres', methods=['POST'])
@admin_required()
def create_genre():
    name = request.form.get('name')
    if not name:
        return jsonify(msg='Tên thể loại bắt buộc'), 400
    color_class = request.form.get('color_class')
    image_path = None
    image = request.files.get('image')
    if image and image.filename:
        import os
        from werkzeug.utils import secure_filename
        filename = secure_filename(image.filename)
        img_folder = os.path.join('static', 'images', 'genres')
        os.makedirs(img_folder, exist_ok=True)
        save_path = os.path.join(img_folder, filename)
        image.save(save_path)
        image_path = f'images/genres/{filename}'
    # Kiểm tra trùng tên (case-insensitive)
    existing = Genre.query.filter(db.func.lower(Genre.name) == name.lower()).first()
    if existing:
        return jsonify(msg='Thể loại đã tồn tại', id=existing.id), 200
    genre = Genre(name=name, image_path=image_path, color_class=color_class)
    db.session.add(genre)
    db.session.commit()
    return jsonify(msg='Tạo thể loại thành công', id=genre.id), 201


@api_bp.route('/genre/<int:genre_id>', methods=['PUT'])
@admin_required()
def update_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    data = request.get_json() or {}
    if 'name' in data:
        genre.name = data['name']
    if 'image_path' in data:
        genre.image_path = data['image_path']
    if 'color_class' in data:
        genre.color_class = data['color_class']
    db.session.commit()
    return jsonify(msg='Cập nhật thể loại thành công', genre={'id': genre.id, 'name': genre.name}), 200


@api_bp.route('/genre/<int:genre_id>', methods=['DELETE'])
@admin_required()
def delete_genre(genre_id):
    # Idempotent delete: nếu không tồn tại trả về 200
    genre = Genre.query.get(genre_id)
    if not genre:
        return jsonify(msg='Đã xóa thể loại hoặc không tồn tại'), 200
    if genre.songs:
        return jsonify(msg='Không thể xóa thể loại đang có bài hát'), 400
    db.session.delete(genre)
    db.session.commit()
    return jsonify(msg='Đã xóa thể loại'), 200


# === Tạo Artist / Album (admin) ===
@api_bp.route('/artists', methods=['POST'])
@admin_required()
def create_artist():
    name = request.form.get('name')
    if not name:
        return jsonify(msg='Tên nghệ sĩ bắt buộc'), 400
    # Kiểm tra trùng tên nghệ sĩ (case-insensitive)
    existing = Artist.query.filter(db.func.lower(Artist.name) == name.lower()).first()
    if existing:
        return jsonify(msg='Nghệ sĩ đã tồn tại', id=existing.id), 200
    image_path = None
    image = request.files.get('image')
    if image and image.filename:
        import os
        from werkzeug.utils import secure_filename
        filename = secure_filename(image.filename)
        img_folder = os.path.join('static', 'images', 'artists')
        os.makedirs(img_folder, exist_ok=True)
        save_path = os.path.join(img_folder, filename)
        image.save(save_path)
        image_path = f'images/artists/{filename}'
    artist = Artist(name=name, image_path=image_path)
    db.session.add(artist)
    db.session.commit()
    return jsonify(msg='Tạo nghệ sĩ thành công', id=artist.id), 201


@api_bp.route('/albums', methods=['POST'])
@admin_required()
def create_album():
    title = request.form.get('title')
    artist_id = request.form.get('artist_id')
    if not title or not artist_id:
        return jsonify(msg='title và artist_id là bắt buộc'), 400
    # Kiểm tra trùng album theo title + artist (case-insensitive)
    existing = Album.query.filter(db.func.lower(Album.title) == title.lower(), Album.artist_id == artist_id).first()
    if existing:
        return jsonify(msg='Album đã tồn tại cho nghệ sĩ này', id=existing.id), 200

    # Xử lý file ảnh
    cover_image_path = None
    image = request.files.get('image')
    if image and image.filename:
        import os
        from werkzeug.utils import secure_filename
        filename = secure_filename(image.filename)
        # Đảm bảo thư mục lưu ảnh tồn tại
        img_folder = os.path.join('static', 'images', 'albums')
        os.makedirs(img_folder, exist_ok=True)
        save_path = os.path.join(img_folder, filename)
        image.save(save_path)
        cover_image_path = f'images/albums/{filename}'

    album = Album(
        title=title,
        artist_id=artist_id,
        release_year=request.form.get('release_year'),
        cover_image_path=cover_image_path
    )
    db.session.add(album)
    db.session.commit()
    return jsonify(msg='Tạo album thành công', id=album.id), 201

# === FOLLOW/UNFOLLOW ARTIST ===

@api_bp.route('/artist/<int:artist_id>/follow-info')
@jwt_required(optional=True)
def artist_follow_info(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    follower_count = artist.followers.count()
    is_following = False
    identity = current_identity()
    if identity:
        user = User.query.get(identity.get('id'))
        if user and artist in user.followed_artists:
            is_following = True
    return jsonify({
        'follower_count': follower_count,
        'is_following': is_following
    })

@api_bp.route('/artist/<int:artist_id>/follow', methods=['POST'])
@jwt_required()
def follow_or_unfollow_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    identity = current_identity()
    user = User.query.get(identity.get('id'))
    if not user:
        return jsonify(msg='User not found'), 404
    if artist in user.followed_artists:
        user.followed_artists.remove(artist)
        db.session.commit()
        return jsonify(msg='Unfollowed'), 200
    else:
        user.followed_artists.append(artist)
        db.session.commit()
        return jsonify(msg='Followed'), 200