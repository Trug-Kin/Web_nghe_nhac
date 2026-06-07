from app import create_app
from src.extensions import db
from src.models.song_rank_stats import SongRankStats

app = create_app()

with app.app_context():
    stats = SongRankStats.query.all()
    for s in stats:
        print(f"song_id={s.song_id}, week={s.week}, month={s.month}, year={s.year}, week_plays={s.week_plays}, month_plays={s.month_plays}, last_updated={s.last_updated}")
