from src.extensions import db # Lấy đối tượng db từ extensions để tránh circular import

# Bảng trung gian cho quan hệ many-to-many giữa User và Artist (follow nghệ sĩ)
user_artist_followers = db.Table('user_artist_followers',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True),
    db.Column('followed_at', db.TIMESTAMP, server_default=db.func.current_timestamp())
)

# Bảng trung gian cho quan hệ many-to-many giữa Song và Artist
song_artists = db.Table('song_artists',
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)

# Model Genre (giữ nguyên)
class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255))  # Tên cột đúng trong database
    color_class = db.Column(db.String(50))   # Tên cột đúng trong database
    # NEW: track uploader ownership (nullable for legacy rows or admin-created)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    songs = db.relationship('Song', backref='genre', lazy=True)

# ✅ BỔ SUNG MODEL ALBUM
class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)  # Cho phép null
    release_year = db.Column(db.Integer)
    cover_image_path = db.Column(db.String(255))
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Thêm trường này
    songs = db.relationship('Song', backref='album', lazy=True)

# ✅ CẬP NHẬT MODEL ARTIST
class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(255))
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Thêm để track uploader
    # Many-to-many với Song
    songs = db.relationship('Song', secondary=song_artists, back_populates='artists', lazy='dynamic')
    albums = db.relationship('Album', backref='artist', lazy=True)
    # Many-to-many với User (followers)
    followers = db.relationship(
        'User',
        secondary='user_artist_followers',
        back_populates='followed_artists',
        lazy='dynamic'
    )

# Model Song (giữ nguyên, đã đúng)
class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    mp3_path = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # Ảnh riêng của bài hát
    # GIỮ artist_id để backward compatibility (nghệ sĩ chính)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=True)
    # Thêm trường uploader_id để biết ai upload bài này (nullable cho case admin)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Many-to-many với Artist (nhiều nghệ sĩ)
    artists = db.relationship('Artist', secondary=song_artists, back_populates='songs', lazy='dynamic')
    
    @property
    def artist(self):
        """Trả về nghệ sĩ chính (artist_id) hoặc nghệ sĩ đầu tiên trong danh sách"""
        from . import Artist as ArtistModel
        if self.artist_id:
            return ArtistModel.query.get(self.artist_id)
        first_artist = self.artists.first()
        return first_artist if first_artist else None
    
    @property
    def artist_name(self):
        """Trả về tên các nghệ sĩ, ngăn cách bằng dấu phẩy"""
        artist_list = list(self.artists.all())
        if artist_list:
            return ', '.join([a.name for a in artist_list])
        elif self.artist:
            return self.artist.name
        return 'Unknown'

    @property
    def mp3_url(self):
        """Return a normalized URL for the MP3 so clients can play it directly.

        Rules:
        - If mp3_path is an absolute URL (http/https) return as-is.
        - If mp3_path starts with '/', return as-is (assumed correct path).
        - If mp3_path contains a slash (e.g., 'music/foo.mp3'), prefix with '/DoAnCoSo/'.
        - If mp3_path is a bare filename, prefix with '/DoAnCoSo/music/'.
        """
        p = (self.mp3_path or '').strip()
        if not p:
            return ''
        import re
        if re.match(r'^https?://', p, re.I):
            return p
        if p.startswith('/'):
            return p
        if '/' in p:
            return f"/DoAnCoSo/{p}"
        return f"/DoAnCoSo/music/{p}"

# ✅ BỔ SUNG MODEL PLAYLIST
class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    cover_image_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    # Order songs by added_at to reflect insertion sequence
    songs = db.relationship('Song', secondary='playlist_songs', backref='playlists', lazy='dynamic', order_by='playlist_songs.c.added_at')    

# Bảng phụ để liên kết nhiều-nhiều giữa Playlist và Song
playlist_songs = db.Table(
    'playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True),
    # Track insertion order into playlist
    db.Column('added_at', db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
)
# ✅ BỔ SUNG MODEL LISTENING HISTORY
class ListeningHistory(db.Model):
    __tablename__ = 'listening_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    listened_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class ArtistStats(db.Model):
    __tablename__ = 'artist_stats'
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    streams_current = db.Column(db.Integer, default=0)
    streams_previous = db.Column(db.Integer, default=0)
    followers_new = db.Column(db.Integer, default=0)
    playlist_adds = db.Column(db.Integer, default=0)
    search_hits = db.Column(db.Integer, default=0)
    social_mentions = db.Column(db.Integer, default=0)
    growth_rate = db.Column(db.Float, default=0.0)  # computed
    rising_score = db.Column(db.Float, default=0.0)
    window_start = db.Column(db.TIMESTAMP, nullable=True)
    window_end = db.Column(db.TIMESTAMP, nullable=True)
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    # Badge support fields
    last_rank = db.Column(db.Integer, nullable=True)
    appearances_count = db.Column(db.Integer, server_default='0')  # number of times appeared in top list
    first_seen_in_top_at = db.Column(db.TIMESTAMP, nullable=True)
    moving_avg_score = db.Column(db.Float, default=0.0)  # EMA smoothing for display

    artist = db.relationship('Artist')

class SearchEvent(db.Model):
    __tablename__ = 'search_events'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)
    query = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    artist = db.relationship('Artist')
#  MODEL LIKE (ngu?i d�ng like b�i h�t)
class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    # �?m b?o m?t user ch? like m?t b�i h�t m?t l?n
    __table_args__ = (db.UniqueConstraint('user_id', 'song_id', name='unique_user_song_like'),)
    
    user = db.relationship('User', backref='likes')
    song = db.relationship('Song', backref='likes')


# MODEL COMMENT (bình luận trên bài hát)
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    user = db.relationship('User', backref='comments')
    song = db.relationship('Song', backref='comments')

# MODEL QUẢNG CÁO (Ad)
class Ad(db.Model):
    __tablename__ = 'ads'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(255))
    link = db.Column(db.String(255))
    mp3_path = db.Column(db.String(255))  # Đường dẫn file mp3 quảng cáo
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
