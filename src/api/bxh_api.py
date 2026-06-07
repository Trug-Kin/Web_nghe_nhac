from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.music import Song, ListeningHistory
from src.models.song_rank_stats import SongRankStats

bxh_api = Blueprint('bxh_api', __name__, url_prefix='/api/bxh')

@bxh_api.route('/songs', methods=['GET'])
def get_bxh_songs():
    filter_type = request.args.get('filter', 'all')
    limit = 10  # Always limit to 10 songs for BXH
    now = db.func.now()
    week = int(db.session.execute(db.text('SELECT WEEK(now())')).scalar())
    month = int(db.session.execute(db.text('SELECT MONTH(now())')).scalar())
    year = int(db.session.execute(db.text('SELECT YEAR(now())')).scalar())
    results = []
    if filter_type == 'week':
        # BXH tuần: chỉ lấy mỗi bài hát một lần với week_plays cao nhất
        from sqlalchemy import func
        subq = (
            db.session.query(
                SongRankStats.song_id,
                func.max(SongRankStats.week_plays).label('max_week_plays')
            )
            .filter(SongRankStats.week == week, SongRankStats.year == year)
            .group_by(SongRankStats.song_id)
            .subquery()
        )
        q = (
            db.session.query(Song, SongRankStats)
            .join(SongRankStats, Song.id == SongRankStats.song_id)
            .join(subq, (SongRankStats.song_id == subq.c.song_id) & (SongRankStats.week_plays == subq.c.max_week_plays))
            .order_by(SongRankStats.week_plays.desc())
            .limit(limit)
        )
        results = []
        # collect song ids to fetch listen counts in bulk
        rows = []
        song_ids = []
        for idx, (song, stat) in enumerate(q):
            rows.append((idx+1, song, stat))
            song_ids.append(song.id)
        # get listen counts from ListeningHistory
        from sqlalchemy import func
        counts = dict(db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()) if song_ids else {}
        for idx, song, stat in rows:
            results.append({
                'position': idx,
                'song': {
                    'id': song.id,
                    'title': song.title,
                    'mp3_path': song.mp3_path,
                    'image_path': song.image_path,
                    'artist_name': song.artist_name,
                    'artist_id': song.artist_id,
                    'album_id': song.album_id,
                    'album_image_path': song.album.cover_image_path if song.album else None,
                    'listen_count': int(counts.get(song.id, 0))
                },
                'week_plays': stat.week_plays,
                'month_plays': stat.month_plays,
                'total_plays': stat.week_plays
            })
    elif filter_type == 'month':
        # BXH tháng: chỉ lấy tháng hiện tại, reset khi sang tháng mới
        q = db.session.query(Song, SongRankStats)
        q = q.join(SongRankStats, Song.id == SongRankStats.song_id)
        q = q.filter(SongRankStats.month == month, SongRankStats.year == year)
        q = q.order_by(SongRankStats.month_plays.desc())
        q = q.limit(limit)
        rows = []
        song_ids = []
        for idx, (song, stat) in enumerate(q):
            rows.append((idx+1, song, stat))
            song_ids.append(song.id)
        from sqlalchemy import func
        counts = dict(db.session.query(ListeningHistory.song_id, func.count(ListeningHistory.id)).filter(ListeningHistory.song_id.in_(song_ids)).group_by(ListeningHistory.song_id).all()) if song_ids else {}
        for idx, song, stat in rows:
            results.append({
                'position': idx,
                'song': {
                    'id': song.id,
                    'title': song.title,
                    'mp3_path': song.mp3_path,
                    'image_path': song.image_path,
                    'artist_name': song.artist_name,
                    'artist_id': song.artist_id,
                    'album_id': song.album_id,
                    'album_image_path': song.album.cover_image_path if song.album else None,
                    'listen_count': int(counts.get(song.id, 0))
                },
                'week_plays': stat.week_plays,
                'month_plays': stat.month_plays,
                'total_plays': stat.month_plays
            })
    else:
        # BXH tất cả: lấy tổng lượt nghe thực tế từ bảng ListeningHistory cho mỗi bài hát
        from sqlalchemy import func
        play_counts = dict(db.session.query(ListeningHistory.song_id, func.count()).group_by(ListeningHistory.song_id).all())
        if not play_counts:
            return jsonify([])
        song_ids = list(play_counts.keys())
        song_map = {s.id: s for s in Song.query.filter(Song.id.in_(song_ids)).all()}
        # Sắp xếp theo tổng lượt nghe giảm dần
        sorted_songs = sorted(play_counts.items(), key=lambda x: x[1], reverse=True)
        # we already have play counts from play_counts; attach listen_count == total_plays here
        for idx, (song_id, total_plays) in enumerate(sorted_songs[:limit]):
            song = song_map.get(song_id)
            if not song:
                continue
            results.append({
                'position': idx+1,
                'song': {
                    'id': song.id,
                    'title': song.title,
                    'mp3_path': song.mp3_path,
                    'image_path': song.image_path,
                    'artist_name': song.artist_name,
                    'artist_id': song.artist_id,
                    'album_id': song.album_id,
                    'album_image_path': song.album.cover_image_path if song.album else None,
                    'listen_count': int(total_plays)
                },
                'week_plays': 0,
                'month_plays': 0,
                'total_plays': int(total_plays)
            })
    return jsonify(results)
    return jsonify(results)
