from app import db
from datetime import datetime

# Giả định: Bảng User đã tồn tại
class User(db.Model):
    # ... các trường id, username, password_hash, v.v.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    
    # Thiết lập mối quan hệ: Một User có thể có nhiều Playlists
    playlists = db.relationship('Playlist', backref='owner', lazy=True)

class Playlist(db.Model):
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Khóa ngoại: Liên kết với bảng User
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Liên kết với bảng Songs thông qua bảng phụ PlaylistSong (cho N-to-N)
    songs = db.relationship('Song', secondary='playlist_song', backref='playlists', lazy='dynamic')
    
    def to_json(self):
        return {
            'playlistId': self.id,
            'name': self.name,
            'ownerId': self.owner_id
        }

# Bảng liên kết cho mối quan hệ N-to-N giữa Playlist và Song
# Giả định Song Model cũng đã tồn tại
playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True),
    # Có thể thêm trường 'order' hoặc 'added_at' nếu cần
)

# class Song(db.Model):
#     __tablename__ = 'songs'
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(255), nullable=False)
#     # ... các trường khác