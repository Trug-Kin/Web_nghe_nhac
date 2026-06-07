from src.extensions import db
from datetime import datetime
from flask_login import UserMixin

# Bảng many-to-many cho user follow user
user_followers = db.Table(
    'user_followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_at', db.DateTime, default=datetime.utcnow)
)


class User(UserMixin, db.Model):
    # Many-to-many với Artist (followed artists)
    followed_artists = db.relationship(
        'Artist',
        secondary='user_artist_followers',
        back_populates='followers',
        lazy='dynamic'
    )
    
    # Many-to-many user follow user
    following = db.relationship(
        'User',
        secondary=user_followers,
        primaryjoin='User.id==user_followers.c.follower_id',
        secondaryjoin='User.id==user_followers.c.followed_id',
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
    __tablename__ = "users"   # khớp với bảng trong DB

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)  # chứa hash
    # Use a simple string for role to avoid enum issues
    # Possible values: 'admin', 'uploader', 'user'
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(255), default='images/default.jpg')  # Đường dẫn avatar
    # Quan hệ: bài hát do user này upload
    songs_uploaded = db.relationship('Song', backref='uploader', lazy=True)
    # Quan hệ: playlist do user này tạo
    playlists = db.relationship('Playlist', backref='owner', lazy=True)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_uploader(self):
        return self.role == 'uploader'
        
    @property
    def is_user(self):
        return self.role == 'user'
