from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
from .user import User
from .music import Genre, Artist, Song, Album, Playlist, ListeningHistory
from .song_rank_stats import SongRankStats
bcrypt = Bcrypt()