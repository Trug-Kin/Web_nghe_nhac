from src.extensions import db
from datetime import datetime

class SongRankStats(db.Model):
    __tablename__ = 'song_rank_stats'
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    week_plays = db.Column(db.Integer, default=0, nullable=False)
    month_plays = db.Column(db.Integer, default=0, nullable=False)
    all_plays = db.Column(db.Integer, default=0, nullable=False)  # Tổng lượt nghe tất cả thời gian
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    song = db.relationship('Song', backref=db.backref('rank_stats', lazy=True))

    def __repr__(self):
        return f'<SongRankStats song_id={self.song_id} week={self.week} month={self.month} year={self.year}>'
