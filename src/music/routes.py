
from flask import Blueprint, render_template, abort, jsonify, request
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
from src.jwt_helper import current_identity
from src.models.music import Genre, Artist, Album, Playlist, Song, ListeningHistory, Like, user_artist_followers, ArtistStats, SearchEvent
from src.models.song_rank_stats import SongRankStats
from src.extensions import db  # Use the same SQLAlchemy instance as models to avoid session mismatch
from sqlalchemy import func
from src.models import User
import datetime as dt
from config import TRENDING_CACHE_TTL

_TRENDING_CACHE = {'data': None, 'generated_at': None}

music_bp = Blueprint('music', __name__)

# Helper: compute trending artists (shared by page + API)
def compute_trending_artists(limit=5, days=7):
    """Return a non-empty list of trending artists (never [] if artists exist).

    Priority order:
    1. Cached (within TTL)
    2. Precomputed ArtistStats (updated <2 days)
    3. Real-time aggregate (plays + followers)
    4. Fallback newest artists (minimal metrics)
    """
    # 1. Cache
    if _TRENDING_CACHE['data'] and _TRENDING_CACHE['generated_at']:
        now_check = dt.datetime.utcnow()
        # Invalidate cache if date rolled over (reset mỗi 0h00 hằng ngày)
        if _TRENDING_CACHE['generated_at'].date() != now_check.date():
            _TRENDING_CACHE['data'] = None
            _TRENDING_CACHE['generated_at'] = None
        else:
            age = (now_check - _TRENDING_CACHE['generated_at']).total_seconds()
            if age < TRENDING_CACHE_TTL:
                return _TRENDING_CACHE['data'], _TRENDING_CACHE['generated_at']

    recent_cut = dt.datetime.utcnow() - dt.timedelta(days=2)
    now = dt.datetime.utcnow()

    # 2. ArtistStats (precomputed)
    try:
        stats_rows = (ArtistStats.query
                      .filter(ArtistStats.updated_at >= recent_cut)
                      .order_by(ArtistStats.moving_avg_score.desc(), ArtistStats.rising_score.desc())
                      .limit(limit).all())
    except Exception:
        stats_rows = []  # table maybe missing -> skip
    if stats_rows:
        data = [{
            'id': r.artist_id,
            'name': r.artist.name if r.artist else '',
            'image_path': r.artist.image_path if r.artist else None,
            'plays_7d': r.streams_current,
            'follower_count': r.followers_new,
            'score': round(r.rising_score, 2),
            'smooth_score': round(r.moving_avg_score, 2),
            'growth_rate_pct': round(r.growth_rate * 100, 1)
        } for r in stats_rows]
        badge_now = dt.datetime.utcnow()
        for d, r in zip(data, stats_rows):
            if r.first_seen_in_top_at and (badge_now - r.first_seen_in_top_at).days <= 2:
                d['badge_new'] = True
            if d['growth_rate_pct'] >= 150:
                d['badge_growth'] = True
        _TRENDING_CACHE['data'] = data  # cache only non-empty
        _TRENDING_CACHE['generated_at'] = now
        return data, now

    # 3. Real-time aggregate
    start = now - dt.timedelta(days=days)
    try:
        plays_subq = (
            db.session.query(
                Song.artist_id.label('artist_id'),
                func.count(ListeningHistory.id).label('plays_7d')
            )
            .join(ListeningHistory, ListeningHistory.song_id == Song.id)
            .filter(ListeningHistory.listened_at >= start)
            .filter(Song.artist_id.isnot(None))
            .group_by(Song.artist_id)
            .subquery()
        )
        follower_counts = (
            db.session.query(
                Artist.id.label('artist_id'),
                func.count(user_artist_followers.c.user_id).label('follower_count')
            )
            .outerjoin(user_artist_followers, user_artist_followers.c.artist_id == Artist.id)
            .group_by(Artist.id)
            .subquery()
        )
        q = (
            db.session.query(
                Artist,
                func.coalesce(plays_subq.c.plays_7d, 0).label('plays_7d'),
                func.coalesce(follower_counts.c.follower_count, 0).label('follower_count'),
                (func.coalesce(plays_subq.c.plays_7d, 0) + func.coalesce(follower_counts.c.follower_count, 0) * 2).label('score')
            )
            .outerjoin(plays_subq, plays_subq.c.artist_id == Artist.id)
            .outerjoin(follower_counts, follower_counts.c.artist_id == Artist.id)
            .order_by(db.text('score DESC'))
            .limit(limit)
        )
        rows = q.all()
        if rows:
            data = [{
                'id': artist.id,
                'name': artist.name,
                'image_path': artist.image_path,
                'plays_7d': int(plays_7d),
                'follower_count': int(follower_count),
                'score': int(score)
            } for artist, plays_7d, follower_count, score in rows]
            _TRENDING_CACHE['data'] = data
            _TRENDING_CACHE['generated_at'] = now
            return data, now
    except Exception:
        # fall through to newest artists fallback
        pass

    # 4. Newest artists fallback (guarantee non-empty if any artists exist)
    newest = Artist.query.order_by(Artist.id.desc()).limit(limit).all()
    if newest:
        data = [{
            'id': a.id,
            'name': a.name,
            'image_path': a.image_path,
            'plays_7d': 0,
            'follower_count': a.followers.count() if hasattr(a, 'followers') else 0,
            'score': (a.followers.count() * 2) if hasattr(a, 'followers') else 0,
            'fallback': 'newest'
        } for a in newest]
        # Do NOT cache fallback newest list (it is a last resort and will be retried soon)
        return data, now

    # If absolutely no artists exist, return empty list
    return [], now

# ============= API: Nghệ sĩ đang nổi (Trending Artists) =============
# Tiêu chí: plays_7d (lượt nghe 7 ngày gần nhất) + follower_count * 2 tạo thành score.
# Lấy top 8 nghệ sĩ. Nếu thiếu data, fallback nghệ sĩ mới nhất.
@music_bp.route('/api/artists/trending')
def api_trending_artists():
    data, now = compute_trending_artists(limit=8, days=7)
    return jsonify({'artists': data, 'generated_at': now.isoformat(), 'range_days': 7})

# ============= API: QUEUE (Danh sách chờ với Autoplay) =============
@music_bp.route('/api/queue')
@jwt_required(optional=True)
def api_queue():
    """Return current queue: now playing + next tracks + autoplay suggestions.
    When near end of context, automatically suggest similar songs to continue playing.
    """
    current_song_id = request.args.get('current_song_id', type=int)
    context_type = request.args.get('context_type', '')  # 'playlist', 'album', 'genre', or 'artist'
    context_id = request.args.get('context_id', type=int)
    current_index = request.args.get('current_index', type=int, default=0)
    total_in_context = request.args.get('total_in_context', type=int, default=0)
    
    result = {'now_playing': None, 'next_in_queue': [], 'autoplay_songs': []}
    
    # Get now playing track details
    if current_song_id:
        song = Song.query.get(current_song_id)
        if song:
            result['now_playing'] = {
                'id': song.id,
                'title': song.title,
                'artist_name': song.artist_name,
                'mp3_path': song.mp3_path,
                'image_path': song.image_path
            }
    
    # Get next tracks from context and collect all context songs for exclusion
    context_songs = []
    if context_type and context_id:
        if context_type == 'playlist':
            playlist = Playlist.query.get(context_id)
            if playlist:
                all_songs = [ps.song for ps in playlist.playlist_songs]
                next_songs = all_songs[current_index + 1:current_index + 21]
                result['next_in_queue'] = [{
                    'id': s.id,
                    'title': s.title,
                    'artist_name': s.artist_name,
                    'mp3_path': s.mp3_path,
                    'image_path': s.image_path
                } for s in next_songs if s]
                context_songs = all_songs
        elif context_type == 'album':
            album = Album.query.get(context_id)
            if album:
                all_songs = sorted(album.songs, key=lambda x: x.id)
                next_songs = all_songs[current_index + 1:current_index + 21]
                result['next_in_queue'] = [{
                    'id': s.id,
                    'title': s.title,
                    'artist_name': s.artist_name,
                    'mp3_path': s.mp3_path,
                    'image_path': s.image_path
                } for s in next_songs]
                context_songs = all_songs
        elif context_type == 'genre':
            genre = Genre.query.get(context_id)
            if genre:
                all_songs = list(genre.songs)
                next_songs = all_songs[current_index + 1:current_index + 21] if current_index < len(all_songs) else []
                result['next_in_queue'] = [{
                    'id': s.id,
                    'title': s.title,
                    'artist_name': s.artist_name,
                    'mp3_path': s.mp3_path,
                    'image_path': s.image_path
                } for s in next_songs]
                context_songs = all_songs
        elif context_type == 'artist':
            artist = Artist.query.get(context_id)
            if artist:
                all_songs = list(artist.songs)
                next_songs = all_songs[current_index + 1:current_index + 21] if current_index < len(all_songs) else []
                result['next_in_queue'] = [{
                    'id': s.id,
                    'title': s.title,
                    'artist_name': s.artist_name,
                    'mp3_path': s.mp3_path,
                    'image_path': s.image_path
                } for s in next_songs]
                context_songs = all_songs
    
    # Add autoplay suggestions if near end of context (last 5 songs or less remaining)
    remaining = total_in_context - current_index - 1
    if remaining <= 5 and context_type in ['genre', 'artist', 'album']:
        # Get IDs to exclude (already in context)
        exclude_ids = [s.id for s in context_songs] if context_songs else []
        if current_song_id:
            exclude_ids.append(current_song_id)
        
        # Get recommended songs based on context with smart fallback
        autoplay = []
        
        if context_type == 'genre' and context_id:
            # For genre: get more songs from same genre
            play_counts = db.session.query(
                SongRankStats.song_id,
                func.sum(SongRankStats.all_plays).label('total_plays')
            ).group_by(SongRankStats.song_id).subquery()
            
            autoplay = Song.query.outerjoin(
                play_counts, Song.id == play_counts.c.song_id
            ).filter(
                Song.genre_id == context_id,
                ~Song.id.in_(exclude_ids) if exclude_ids else True
            ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15).all()
            
        elif context_type == 'artist' and context_id:
            # For artist: first try same artist
            play_counts = db.session.query(
                SongRankStats.song_id,
                func.sum(SongRankStats.all_plays).label('total_plays')
            ).group_by(SongRankStats.song_id).subquery()
            
            autoplay = Song.query.outerjoin(
                play_counts, Song.id == play_counts.c.song_id
            ).filter(
                Song.artist_id == context_id,
                ~Song.id.in_(exclude_ids) if exclude_ids else True
            ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15).all()
            
            # If not enough songs from artist, get songs from same genre as current song
            if len(autoplay) < 10:
                current_song = Song.query.get(current_song_id) if current_song_id else None
                if current_song and current_song.genre_id:
                    # Get songs from same genre, different artist
                    play_counts = db.session.query(
                        SongRankStats.song_id,
                        func.sum(SongRankStats.all_plays).label('total_plays')
                    ).group_by(SongRankStats.song_id).subquery()
                    
                    genre_songs = Song.query.outerjoin(
                        play_counts, Song.id == play_counts.c.song_id
                    ).filter(
                        Song.genre_id == current_song.genre_id,
                        Song.artist_id != context_id,
                        ~Song.id.in_(exclude_ids + [s.id for s in autoplay]) if exclude_ids or autoplay else True
                    ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15 - len(autoplay)).all()
                    autoplay.extend(genre_songs)
                    
        elif context_type == 'album' and context_id:
            album = Album.query.get(context_id)
            if album:
                # First try: other albums from same artist
                if album.artist_id:
                    play_counts = db.session.query(
                        SongRankStats.song_id,
                        func.sum(SongRankStats.all_plays).label('total_plays')
                    ).group_by(SongRankStats.song_id).subquery()
                    
                    autoplay = Song.query.outerjoin(
                        play_counts, Song.id == play_counts.c.song_id
                    ).filter(
                        Song.artist_id == album.artist_id,
                        Song.album_id != context_id,
                        ~Song.id.in_(exclude_ids) if exclude_ids else True
                    ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15).all()
                
                # If not enough, get songs from same genre as current song
                if len(autoplay) < 10:
                    current_song = Song.query.get(current_song_id) if current_song_id else None
                    if current_song and current_song.genre_id:
                        play_counts = db.session.query(
                            SongRankStats.song_id,
                            func.sum(SongRankStats.all_plays).label('total_plays')
                        ).group_by(SongRankStats.song_id).subquery()
                        
                        genre_songs = Song.query.outerjoin(
                            play_counts, Song.id == play_counts.c.song_id
                        ).filter(
                            Song.genre_id == current_song.genre_id,
                            Song.album_id != context_id,
                            ~Song.id.in_(exclude_ids + [s.id for s in autoplay]) if exclude_ids or autoplay else True
                        ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15 - len(autoplay)).all()
                        autoplay.extend(genre_songs)
        
        # Fallback to popular songs if not enough
        if len(autoplay) < 10:
            play_counts = db.session.query(
                SongRankStats.song_id,
                func.sum(SongRankStats.all_plays).label('total_plays')
            ).group_by(SongRankStats.song_id).subquery()
            
            more = Song.query.outerjoin(
                play_counts, Song.id == play_counts.c.song_id
            ).filter(
                ~Song.id.in_(exclude_ids + [s.id for s in autoplay]) if exclude_ids or autoplay else True
            ).order_by(func.coalesce(play_counts.c.total_plays, 0).desc()).limit(15 - len(autoplay)).all()
            autoplay.extend(more)
        
        result['autoplay_songs'] = [{
            'id': s.id,
            'title': s.title,
            'artist_name': s.artist_name,
            'mp3_path': s.mp3_path,
            'image_path': s.image_path,
            'is_autoplay': True
        } for s in autoplay]
    
    return jsonify(result)

# ============= API FOLLOW NGHỆ SĨ =============
@music_bp.route('/api/artist/<int:id>/follow-info')
@jwt_required(optional=True)
def api_artist_follow_info(id):
    artist = Artist.query.get(id)
    if not artist:
        return jsonify({'msg': 'Artist not found'}), 404
    follower_count = artist.followers.count()
    user_id = get_jwt_identity()
    is_following = False
    if user_id:
        user = User.query.get(user_id)
        if user and artist in user.followed_artists:
            is_following = True
    return jsonify({
        'follower_count': follower_count,
        'is_following': is_following
    })

@music_bp.route('/api/artist/<int:id>/follow', methods=['POST'])
@jwt_required()
def api_artist_follow(id):
    artist = Artist.query.get(id)
    if not artist:
        return jsonify({'msg': 'Artist not found'}), 404
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 401
    if artist in user.followed_artists:
        # Unfollow
        user.followed_artists.remove(artist)
        db.session.commit()
        return jsonify({'msg': 'unfollowed'})
    else:
        # Follow
        user.followed_artists.append(artist)
        db.session.commit()
        return jsonify({'msg': 'followed'})

# ============= Trang tất cả nghệ sĩ xếp hạng theo lượt nghe =============
@music_bp.route('/artists')
@jwt_required(optional=True)
def all_artists_page():
    """Page showing artists that the current user follows"""
    identity = current_identity()
    
    # If not logged in, redirect to login
    if not identity or not identity.get('id'):
        return render_template('login.html'), 401
    
    user = User.query.get(identity.get('id'))
    if not user:
        return render_template('login.html'), 401
    
    # Get followed artists with their stats
    followed_artists = user.followed_artists.all()
    
    # Get play counts for followed artists
    artist_stats = []
    for artist in followed_artists:
        # Count total plays for this artist's songs
        plays = (db.session.query(func.count(ListeningHistory.id))
                .join(Song, Song.id == ListeningHistory.song_id)
                .filter(Song.artist_id == artist.id)
                .scalar() or 0)
        
        artist_stats.append({
            'artist': artist,
            'plays': plays
        })
    
    # Sort by plays descending
    artist_stats.sort(key=lambda x: x['plays'], reverse=True)
    
    # Add position numbers
    ranking_artists = []
    for idx, stats in enumerate(artist_stats, start=1):
        ranking_artists.append({
            'position': idx,
            'artist': stats['artist'],
            'plays': stats['plays']
        })
    
    return render_template('artists.html', ranking_artists=ranking_artists)


@music_bp.route('/')
def home():
    all_genres = Genre.query.all()
    all_artists = Artist.query.all()
    all_albums = Album.query.all()
    trending_artists, trending_generated_at = compute_trending_artists()
    # Get public playlists for homepage
    public_playlists = Playlist.query.filter_by(is_public=True).order_by(Playlist.created_at.desc()).limit(12).all()
    return render_template(
        'main.html',
        genres=all_genres,
        artists=all_artists,
        albums=all_albums,
        trending_artists=trending_artists,
        trending_generated_at=trending_generated_at,
        public_playlists=public_playlists
    )

@music_bp.route('/api/home')
def home_api():
    """Return homepage data (genres, artists, albums) for SPA navigation."""
    all_genres = Genre.query.all()
    all_artists = Artist.query.all()
    all_albums = Album.query.all()
    trending_artists, trending_generated_at = compute_trending_artists()
    # Recommended artists (For You): nếu có user -> dựa trên lịch sử nghe 30 ngày, fallback top plays chung.
    recommended = []
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None
    if user_id:
        # Top artists by listens for this user last 30 days
        start_user = dt.datetime.utcnow() - dt.timedelta(days=30)
        user_rows = (
            db.session.query(Artist.id, func.count(ListeningHistory.id).label('plays'))
            .join(Song, Song.artist_id == Artist.id)
            .join(ListeningHistory, ListeningHistory.song_id == Song.id)
            .filter(ListeningHistory.user_id == user_id)
            .filter(ListeningHistory.listened_at >= start_user)
            .group_by(Artist.id)
            .order_by(func.count(ListeningHistory.id).desc())
            .limit(12)
            .all()
        )
        artist_map = {a.id: a for a in Artist.query.filter(Artist.id.in_([r.id for r in user_rows])).all()}
        for r in user_rows:
            a = artist_map.get(r.id)
            if a:
                recommended.append({'id': a.id, 'name': a.name, 'image_path': a.image_path})
    if not recommended:
        # Fallback: top artists overall by total listens
        global_rows = (
            db.session.query(Artist.id, func.count(ListeningHistory.id).label('plays'))
            .join(Song, Song.artist_id == Artist.id)
            .join(ListeningHistory, ListeningHistory.song_id == Song.id)
            .group_by(Artist.id)
            .order_by(func.count(ListeningHistory.id).desc())
            .limit(12)
            .all()
        )
        artist_map2 = {a.id: a for a in Artist.query.filter(Artist.id.in_([r.id for r in global_rows])).all()}
        for r in global_rows:
            a = artist_map2.get(r.id)
            if a:
                recommended.append({'id': a.id, 'name': a.name, 'image_path': a.image_path})
    
    genres_data = [{
        'id': g.id,
        'name': g.name,
        'image_path': g.image_path,
        'color_class': getattr(g, 'color_class', 'default-color')
    } for g in all_genres]
    
    artists_data = [{
        'id': a.id,
        'name': a.name,
        'image_path': a.image_path
    } for a in all_artists]
    
    albums_data = [{
        'id': al.id,
        'title': al.title,
        'artist_name': al.artist.name if al.artist else '',
        'cover_image_path': al.cover_image_path
    } for al in all_albums]
    
    return jsonify({
        'genres': genres_data,
        'artists': artists_data,
        'albums': albums_data,
        'trending_artists': trending_artists,
        'trending_generated_at': trending_generated_at.isoformat() if trending_generated_at else None,
        'recommended_artists': recommended
    })

@music_bp.route('/api/search')
def search():
    """Tìm kiếm bài hát, nghệ sĩ, album, thể loại, người dùng theo từ khóa."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'songs': [], 'artists': [], 'albums': [], 'genres': [], 'users': []})
    
    search_pattern = f"%{query}%"
    
    # Tìm bài hát
    songs = Song.query.filter(Song.title.ilike(search_pattern)).limit(10).all()
    songs_data = [{
        'id': s.id,
        'title': s.title,
        'artist_name': s.artist_name,  # Sử dụng property mới (trả về tất cả nghệ sĩ)
        'mp3_path': s.mp3_path,
        'image_path': s.image_path,  # Ảnh riêng của bài hát
        'album_image_path': s.album.cover_image_path if s.album else None  # Ảnh album
    } for s in songs]

    
    # Tìm nghệ sĩ
    artists = Artist.query.filter(Artist.name.ilike(search_pattern)).limit(8).all()
    artists_data = [{
        'id': a.id,
        'name': a.name,
        'image_path': a.image_path
    } for a in artists]
    
    # Tìm album
    albums = Album.query.filter(Album.title.ilike(search_pattern)).limit(8).all()
    albums_data = [{
        'id': al.id,
        'title': al.title,
        'artist_name': al.artist.name if al.artist else '',
        'cover_image_path': al.cover_image_path
    } for al in albums]
    
    # Tìm thể loại
    genres = Genre.query.filter(Genre.name.ilike(search_pattern)).limit(6).all()
    genres_data = [{
        'id': g.id,
        'name': g.name,
        'image_path': g.image_path
    } for g in genres]
    
    # Tìm người dùng
    users = User.query.filter(User.username.ilike(search_pattern)).limit(8).all()
    users_data = [{
        'id': u.id,
        'username': u.username,
        'avatar': u.avatar if hasattr(u, 'avatar') else 'images/default.jpg',
        'role': u.role
    } for u in users]
    
    # Log search events for artists (distinct artist ids) for rising stats
    try:
        artist_ids = [a['id'] for a in artists_data][:5]  # limit to first 5 matches
        for aid in artist_ids:
            ev = SearchEvent(artist_id=aid, query=query, user_id=None)
            db.session.add(ev)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({
        'songs': songs_data,
        'artists': artists_data,
        'albums': albums_data,
        'genres': genres_data,
        'users': users_data
    })

@music_bp.route('/api/artists')
def get_all_artists():
    """Lấy danh sách tất cả nghệ sĩ (cho autocomplete)"""
    artists = Artist.query.order_by(Artist.name).all()
    return jsonify([
        {'id': a.id, 'name': a.name}
        for a in artists
    ])

@music_bp.route('/song/<int:id>')
def song_detail_page(id):
    """Trang chi tiết bài hát với like và comment."""
    song = Song.query.get(id)
    if not song:
        abort(404)
    return render_template('song_detail.html', song=song)

@music_bp.route('/playlists', endpoint='my_playlists_page')
def my_playlists():
    """Render page showing current user's playlists.

    We allow optional JWT so that if the cookie is missing but the SPA
    later fetches data via API, at least page renders with empty list.
    If JWT is present (cookie or Authorization header), we show playlists.
    """
    user = None
    try:
        # optional verifies cookie/header token; won't raise if absent
        verify_jwt_in_request(optional=True)
        identity = current_identity()
        if identity and identity.get('id'):
            user = User.query.get(identity.get('id'))
    except Exception:
        user = None
    pls = user.playlists if user else []
    return render_template('playlists.html', playlists=pls)


@music_bp.route('/playlist/<int:id>')
def playlist_page(id):
    p = Playlist.query.get(id)
    if not p:
        abort(404)
    
    # Check if user is owner or playlist is public
    can_manage = False
    current_user = None
    try:
        verify_jwt_in_request(optional=True)
        identity = current_identity()
        if identity:
            current_user = User.query.get(identity.get('id'))
            can_manage = (identity.get('id') == p.user_id)
    except Exception:
        pass
    
    # If not owner and not public, deny access
    if not can_manage and not p.is_public:
        abort(404)

    # Prepare initial listen and like counts for server-side render.
    # Use a concrete list of songs to compute counts and attach attributes
    song_list = p.songs.all() if hasattr(p.songs, 'all') else list(p.songs)
    song_ids = [s.id for s in song_list]
    listen_counts = {}
    like_counts = {}
    if song_ids:
        listen_rows = db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()
        listen_counts = {sid: c for sid, c in listen_rows}
        like_rows = db.session.query(Like.song_id, func.count(Like.id)).filter(Like.song_id.in_(song_ids)).group_by(Like.song_id).all()
        like_counts = {sid: c for sid, c in like_rows}

    # Attach initial counts onto song objects in the concrete list for use in template
    for s in song_list:
        try:
            s.initial_listen_count = int(listen_counts.get(s.id, 0))
        except Exception:
            s.initial_listen_count = 0
        try:
            s.initial_like_count = int(like_counts.get(s.id, 0))
        except Exception:
            s.initial_like_count = 0

    return render_template('playlist.html', playlist=p, current_user=current_user, can_manage=can_manage)

@music_bp.route('/artist/<int:id>')
def artist_page(id):
    return render_template('artist_detail.html', artist_id=id)

@music_bp.route('/genre/<int:id>')
def genre_page(id):
    genre = Genre.query.get(id)
    if not genre:
        abort(404)
    return render_template('genre_detail.html', genre_id=id, genre=genre)

@music_bp.route('/album/<int:id>')
def album_page(id):
    return render_template('album_detail.html', album_id=id)

@music_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    """User profile page showing their public playlists"""
    user = User.query.get_or_404(user_id)
    
    # Get current user if logged in
    current_user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = current_identity()
        if identity:
            current_user_id = identity.get('id')
    except Exception:
        pass
    
    # Get user's public playlists
    public_playlists = Playlist.query.filter_by(user_id=user_id, is_public=True).order_by(Playlist.created_at.desc()).all()
    return render_template('user_profile.html', profile_user=user, public_playlists=public_playlists, current_user_id=current_user_id)


@music_bp.route('/following')
@jwt_required(optional=True)
def following_page():
    """Page showing users that current user is following"""
    identity = current_identity()
    if not identity or not identity.get('id'):
        return render_template('login.html'), 401
    return render_template('following.html')


@music_bp.route('/followers')
@jwt_required(optional=True)
def followers_page():
    """Page showing users following the current user"""
    identity = current_identity()
    if not identity or not identity.get('id'):
        return render_template('login.html'), 401
    return render_template('followers.html')


# Old simple history route - REMOVED (replaced with JWT-protected version below)

@music_bp.route('/bxh')
def ranking_page():
    """Trang bảng xếp hạng (BXH) bài hát theo lượt nghe.

    Logic:
    - Dùng bảng listening_history để đếm số lượt nghe mỗi bài hát.
    - Đồng thời tổng hợp lượt nghe cho Nghệ sĩ và Album.
    - Hỗ trợ lọc theo: all (tất cả), week (tuần), month (tháng)
    - Nếu chưa có dữ liệu nghe: hiển thị danh sách bài hát / nghệ sĩ / album mới nhất làm fallback.
    - Giới hạn top 50 bài hát, top 30 nghệ sĩ, top 30 album.
    """
    from datetime import datetime, timedelta
    
    # Lấy tham số filter từ query string (mặc định: all)
    time_filter = request.args.get('filter', 'all')
    now = dt.datetime.now()
    week = int(now.strftime('%U'))
    month = now.month
    year = now.year
    ranking = []
    if time_filter == 'week':
        # BXH tuần lấy từ bảng song_rank_stats, giới hạn 10 bài hát
        stats = SongRankStats.query.filter_by(week=week, month=month, year=year).order_by(SongRankStats.week_plays.desc()).limit(10).all()
        song_map = {s.id: s for s in Song.query.filter(Song.id.in_([st.song_id for st in stats])).all()}
        for idx, st in enumerate(stats, start=1):
            song = song_map.get(st.song_id)
            if song:
                ranking.append({'position': idx, 'song': song, 'plays': st.week_plays})
    elif time_filter == 'month':
        # BXH tháng lấy từ bảng song_rank_stats, giới hạn 10 bài hát
        stats = SongRankStats.query.filter_by(month=month, year=year).order_by(SongRankStats.month_plays.desc()).limit(10).all()
        song_map = {s.id: s for s in Song.query.filter(Song.id.in_([st.song_id for st in stats])).all()}
        for idx, st in enumerate(stats, start=1):
            song = song_map.get(st.song_id)
            if song:
                ranking.append({'position': idx, 'song': song, 'plays': st.month_plays})
    else:
        # BXH tất cả lấy từ bảng listening_history như cũ, giới hạn 10 bài hát
        query = ListeningHistory.query
        play_counts = (
            query
            .with_entities(ListeningHistory.song_id, func.count(ListeningHistory.id).label('plays'))
            .group_by(ListeningHistory.song_id)
            .order_by(func.count(ListeningHistory.id).desc())
            .limit(10)
            .all()
        )
        song_map = {s.id: s for s in Song.query.filter(Song.id.in_([pc.song_id for pc in play_counts])).all()}
        for idx, pc in enumerate(play_counts, start=1):
            song = song_map.get(pc.song_id)
            if song:
                ranking.append({'position': idx, 'song': song, 'plays': pc.plays})
    # ============= Nghệ sĩ =============

    # ============= BXH Nghệ sĩ & Album =============
    ranking_artists = []
    ranking_albums = []
    if time_filter == 'all':
        # BXH nghệ sĩ và album chỉ tính theo tổng lượt nghe (all), giới hạn 10 album
        artist_query = db.session.query(Artist.id, func.count(ListeningHistory.id).label('plays'))
        artist_query = artist_query.join(Song, Song.artist_id == Artist.id)
        artist_query = artist_query.join(ListeningHistory, ListeningHistory.song_id == Song.id)
        artist_play_counts = (
            artist_query
            .group_by(Artist.id)
            .order_by(func.count(ListeningHistory.id).desc())
            .limit(10)
            .all()
        )
        artist_map = {a.id: a for a in Artist.query.filter(Artist.id.in_([apc.id for apc in artist_play_counts])).all()}
        for idx, apc in enumerate(artist_play_counts, start=1):
            artist = artist_map.get(apc.id)
            if artist:
                ranking_artists.append({
                    'position': idx,
                    'artist': artist,
                    'plays': apc.plays
                })

        album_query = db.session.query(Album.id, func.count(ListeningHistory.id).label('plays'))
        album_query = album_query.join(Song, Song.album_id == Album.id)
        album_query = album_query.join(ListeningHistory, ListeningHistory.song_id == Song.id)
        album_play_counts = (
            album_query
            .group_by(Album.id)
            .order_by(func.count(ListeningHistory.id).desc())
            .limit(10)
            .all()
        )
        album_map = {al.id: al for al in Album.query.filter(Album.id.in_([alc.id for alc in album_play_counts])).all()}
        for idx, alc in enumerate(album_play_counts, start=1):
            album = album_map.get(alc.id)
            if album:
                ranking_albums.append({
                    'position': idx,
                    'album': album,
                    'plays': alc.plays
                })
    elif time_filter == 'week':
        # BXH album tuần: tổng week_plays của các bài hát trong album từ SongRankStats, giới hạn 10 album
        stats = db.session.query(Song.album_id, func.sum(SongRankStats.week_plays).label('plays')) \
            .join(Song, Song.id == SongRankStats.song_id) \
            .filter(SongRankStats.week == week, SongRankStats.year == year, Song.album_id != None) \
            .group_by(Song.album_id) \
            .order_by(func.sum(SongRankStats.week_plays).desc()) \
            .limit(10).all()
        album_ids = [row.album_id for row in stats]
        album_map = {al.id: al for al in Album.query.filter(Album.id.in_(album_ids)).all()}
        for idx, row in enumerate(stats, start=1):
            album = album_map.get(row.album_id)
            if album:
                ranking_albums.append({
                    'position': idx,
                    'album': album,
                    'plays': int(row.plays) if row.plays else 0
                })
    elif time_filter == 'month':
        # BXH album tháng: tổng month_plays của các bài hát trong album từ SongRankStats, giới hạn 10 album
        stats = db.session.query(Song.album_id, func.sum(SongRankStats.month_plays).label('plays')) \
            .join(Song, Song.id == SongRankStats.song_id) \
            .filter(SongRankStats.month == month, SongRankStats.year == year, Song.album_id != None) \
            .group_by(Song.album_id) \
            .order_by(func.sum(SongRankStats.month_plays).desc()) \
            .limit(10).all()
        album_ids = [row.album_id for row in stats]
        album_map = {al.id: al for al in Album.query.filter(Album.id.in_(album_ids)).all()}
        for idx, row in enumerate(stats, start=1):
            album = album_map.get(row.album_id)
            if album:
                ranking_albums.append({
                    'position': idx,
                    'album': album,
                    'plays': int(row.plays) if row.plays else 0
                })

    # Fallback nếu chưa có lượt nghe nào cho từng loại
    latest_songs = []
    latest_artists = []
    latest_albums = []
    if not ranking:
        latest_songs = Song.query.order_by(Song.id.desc()).limit(10).all()
    if not ranking_artists:
        latest_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    if not ranking_albums:
        latest_albums = Album.query.order_by(Album.id.desc()).limit(10).all()

    return render_template(
        'bxh.html',
        ranking=ranking,
        ranking_artists=ranking_artists,
        ranking_albums=ranking_albums,
        fallback=latest_songs,
        fallback_artists=latest_artists,
        fallback_albums=latest_albums,
        current_filter=time_filter
    )

# ==============================================================
# API: Chi tiết nghệ sĩ / thể loại / album (JSON) kèm lượt nghe
# Frontend (app.js) sẽ gọi /api/<type>/<id> để lấy danh sách bài hát
# với trường listen_count (số lượt nghe) thay thế phần checkbox chọn.
# ==============================================================

@music_bp.route('/api/artist/<int:id>')
def api_artist_detail(id):
    artist = Artist.query.get(id)
    if not artist:
        return jsonify({'msg': 'Artist not found'}), 404
    
    # ✅ Sử dụng quan hệ many-to-many để lấy TẤT CẢ bài hát của nghệ sĩ
    songs = list(artist.songs.all())  # full list (will be reduced to top 20 by listens)
    
    song_ids = [s.id for s in songs]
    listen_counts = {}
    if song_ids:
        counts = (
            db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id))
            .filter(ListeningHistory.song_id.in_(song_ids))
            .group_by(ListeningHistory.song_id)
            .all()
        )
        listen_counts = {sid: c for sid, c in counts}
    # Sắp xếp theo lượt nghe giảm dần và giới hạn 20 bài nhiều lượt nghe nhất
    songs_sorted = sorted(songs, key=lambda s: listen_counts.get(s.id, 0), reverse=True)[:20]

    return jsonify({
        'id': artist.id,
        'name': artist.name,
        'image_path': artist.image_path,
        'songs': [
            {
                'id': s.id,
                'title': s.title,
                'artist_name': s.artist_name,  # ✅ Hiển thị tất cả nghệ sĩ (có thể nhiều)
                'mp3_path': s.mp3_path,
                'listen_count': int(listen_counts.get(s.id, 0)),
                'image_path': s.image_path,  # Ảnh riêng của bài hát
                'album_image_path': s.album.cover_image_path if s.album else None  # Ảnh album
            } for s in songs_sorted
        ]
    })

@music_bp.route('/api/genre/<int:id>')
def api_genre_detail(id):
    genre = Genre.query.get(id)
    if not genre:
        return jsonify({'msg': 'Genre not found'}), 404
    songs = Song.query.filter_by(genre_id=id).all()  # full list (will reduce to top 20)
    song_ids = [s.id for s in songs]
    listen_counts = {}
    if song_ids:
        counts = (
            db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id))
            .filter(ListeningHistory.song_id.in_(song_ids))
            .group_by(ListeningHistory.song_id)
            .all()
        )
        listen_counts = {sid: c for sid, c in counts}
    # Sắp xếp theo lượt nghe giảm dần và giới hạn 20 bài nhiều lượt nghe nhất
    songs_sorted = sorted(songs, key=lambda s: listen_counts.get(s.id, 0), reverse=True)[:20]
    return jsonify({
        'id': genre.id,
        'name': genre.name,
        'image_path': genre.image_path,
        'songs': [
            {
                'id': s.id,
                'title': s.title,
                'artist_name': s.artist_name,  # Sử dụng property (tất cả nghệ sĩ)
                'mp3_path': s.mp3_path,
                'listen_count': int(listen_counts.get(s.id, 0)),
                'image_path': s.image_path,  # Ảnh riêng của bài hát
                'album_image_path': s.album.cover_image_path if s.album else None  # Ảnh album
            } for s in songs_sorted
        ]
    })

@music_bp.route('/api/album/<int:id>')
def api_album_detail(id):
    album = Album.query.get(id)
    if not album:
        return jsonify({'msg': 'Album not found'}), 404
    songs = Song.query.filter_by(album_id=id).all()
    song_ids = [s.id for s in songs]
    listen_counts = {}
    if song_ids:
        counts = (
            db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id))
            .filter(ListeningHistory.song_id.in_(song_ids))
            .group_by(ListeningHistory.song_id)
            .all()
        )
        listen_counts = {sid: c for sid, c in counts}
    # Album model dùng field 'title' chứ không phải 'name'
    return jsonify({
        'id': album.id,
        'name': album.title,  # front-end kỳ vọng 'name'
        'image_path': album.cover_image_path,
        'songs': [
            {
                'id': s.id,
                'title': s.title,
                'artist_name': s.artist_name,  # Sử dụng property (tất cả nghệ sĩ)
                'mp3_path': s.mp3_path,
                'listen_count': int(listen_counts.get(s.id, 0)),
                'album_image_path': s.image_path or album.cover_image_path
            } for s in songs
        ]
    })
# ==================== BÀI HÁT YÊU THÍCH ====================

@music_bp.route('/liked-songs')
@jwt_required(optional=True)
def liked_songs():
    """Hiển thị danh sách bài hát người dùng đã like."""
    try:
        identity = current_identity()
        if not identity or not identity.get('id'):
            return render_template('login.html'), 401
        
        user_id = identity.get('id')
        
        # Lấy danh sách likes của user, JOIN với Song để lấy thông tin đầy đủ
        liked_songs = (db.session.query(Song, Like.created_at)
                      .join(Like, Song.id == Like.song_id)
                      .filter(Like.user_id == user_id)
                      .order_by(Like.created_at.desc())
                      .all())
        
        # Prepare song data
        songs_data = []
        for song, liked_at in liked_songs:
            songs_data.append({
                'id': song.id,
                'title': song.title,
                'artist_name': song.artist.name if song.artist else 'Unknown',
                'artist_id': song.artist_id,
                'album_title': song.album.title if song.album else None,
                'album_id': song.album_id,
                'genre_name': song.genre.name if song.genre else None,
                'mp3_path': song.mp3_path,
                'liked_at': liked_at.isoformat() if liked_at else None
            })
        
        return render_template('liked_songs.html', songs=songs_data, user=identity)
    except Exception as e:
        return render_template('login.html'), 401


# ==================== LỊCH SỬ NGHE ====================

@music_bp.route('/history')
@jwt_required(optional=True)
def history_page():
    """Hiển thị lịch sử nghe nhạc của người dùng."""
    try:
        # Debug: print request cookies and headers
        from flask import request as flask_request
        print(f"[DEBUG /history] Cookies: {flask_request.cookies}")
        print(f"[DEBUG /history] Auth Header: {flask_request.headers.get('Authorization', 'None')}")
        
        identity = current_identity()
        print(f"[DEBUG /history] Identity: {identity}")
        
        if not identity or not identity.get('id'):
            print("[DEBUG /history] No valid identity, redirecting to login")
            return redirect(url_for('auth.login_page', next='/history'))
        
        user_id = identity.get('id')
        print(f"[DEBUG /history] User ID: {user_id}")
        
        # Lấy từng lần nghe riêng biệt
        history_query = (db.session.query(ListeningHistory, Song)
            .join(Song, ListeningHistory.song_id == Song.id)
            .filter(ListeningHistory.user_id == user_id)
            .order_by(ListeningHistory.listened_at.desc())
            .limit(100)
            .all())
        
        # Prepare history data
        history_data = []
        for listen, song in history_query:
            history_data.append({
                'id': song.id,
                'title': song.title,
                'artist_name': song.artist.name if song.artist else 'Unknown',
                'artist_id': song.artist_id,
                'album_title': song.album.title if song.album else None,
                'album_id': song.album_id,
                'genre_name': song.genre.name if song.genre else None,
                'mp3_path': song.mp3_path,
                'listened_at': listen.listened_at.isoformat() if listen.listened_at else None
            })
        
        return render_template('history.html', history=history_data, user=identity)
    except Exception as e:
        print(f"[ERROR /history] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return render_template('login.html'), 401
