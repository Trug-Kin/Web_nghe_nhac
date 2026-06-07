# Script cập nhật lại all_plays cho tất cả bài hát dựa trên bảng ListeningHistory
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from src.extensions import db
from src.models.music import Song, ListeningHistory
from src.models.song_rank_stats import SongRankStats
from sqlalchemy import func

def update_all_plays():
    app = create_app()
    with app.app_context():
        # Đếm tổng số lượt nghe cho từng bài hát
        song_play_counts = dict(db.session.query(ListeningHistory.song_id, func.count()).group_by(ListeningHistory.song_id).all())
        print(f"Tìm thấy {len(song_play_counts)} bài hát có lượt nghe.")
        updated = 0
        import datetime
        now = datetime.datetime.now()
        week = int(now.strftime('%U'))
        month = now.month
        year = now.year
        for song_id, total in song_play_counts.items():
            stats = SongRankStats.query.filter_by(song_id=song_id).all()
            if not stats:
                # Nếu chưa có record nào, tạo mới 1 record cho bài hát này
                stat = SongRankStats(song_id=song_id, week=week, month=month, year=year, week_plays=0, month_plays=0, all_plays=total, last_updated=now)
                db.session.add(stat)
                updated += 1
            else:
                for stat in stats:
                    stat.all_plays = total
                updated += 1
        db.session.commit()
        print(f"Đã cập nhật all_plays cho {updated} bài hát.")

if __name__ == "__main__":
    update_all_plays()
