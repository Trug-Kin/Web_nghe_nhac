# Script reset toàn bộ lượt nghe về 0 cho hệ thống
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from src.extensions import db
from src.models.music import ListeningHistory
from src.models.song_rank_stats import SongRankStats

def reset_all_listens():
    app = create_app()
    with app.app_context():
        # Xóa toàn bộ lịch sử nghe
        deleted = ListeningHistory.query.delete()
        print(f"Đã xóa {deleted} record trong ListeningHistory.")
        # Reset BXH tuần/tháng/tất cả về 0
        stats = SongRankStats.query.all()
        for stat in stats:
            stat.week_plays = 0
            stat.month_plays = 0
            stat.all_plays = 0
        db.session.commit()
        print(f"Đã reset {len(stats)} record trong SongRankStats về 0.")

if __name__ == "__main__":
    reset_all_listens()
