
# Đăng ký alias sau khi history_bp đã được định nghĩa

# Đăng ký alias sau khi các hàm đã xong

# Đăng ký alias sau tất cả các hàm

# ...existing code...

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.jwt_helper import current_identity
from src.extensions import db
from src.models.music import ListeningHistory, Song
from src.models.song_rank_stats import SongRankStats
import datetime as dt
from datetime import datetime

history_bp = Blueprint('history_api', __name__, url_prefix='/api')

@history_bp.route('/listen', methods=['POST'])
@jwt_required()
def log_listen():
    print('=== LOG_LISTEN CALLED - 2025-10-31 ===')
    identity = current_identity()
    user_id = identity.get('id')
    data = request.get_json() or {}
    song_id = data.get('song_id')
    if not song_id:
        print('[DEBUG] Thiếu song_id')
        return jsonify({'msg': 'Thiếu song_id'}), 400
    # Log thông tin kết nối DB để xác nhận đúng DB
    print(f'[DEBUG] DB URL: {db.engine.url}')
    print(f'[DEBUG] Nhận yêu cầu log listen cho song_id={song_id} (type={type(song_id)})')
    # Đảm bảo song_id là int
    try:
        song_id_int = int(song_id)
    except Exception as e:
        print(f'[DEBUG] song_id không phải số nguyên: {song_id} ({e})')
        return jsonify({'msg': 'song_id không hợp lệ', 'error': str(e)}), 400

    song = Song.query.get(song_id_int)
    if not song:
        print(f'[DEBUG] Bài hát không tồn tại trong DB: song_id={song_id_int}')
        return jsonify({'msg': 'Bài hát không tồn tại', 'song_id': song_id_int}), 404
    try:
        lh = ListeningHistory(user_id=user_id, song_id=song_id_int)
        db.session.add(lh)
        print(f'[DEBUG] Đã thêm ListeningHistory: user_id={user_id}, song_id={song_id_int}')
        now = dt.datetime.now()
        week = int(now.strftime('%U'))  # Tuần trong năm (0-53)
        month = now.month
        year = now.year
        print(f'[DEBUG] Logging BXH: song_id={song_id_int}, week={week}, month={month}, year={year}')

        # --- BXH tuần/tháng ---
        stat = SongRankStats.query.filter_by(song_id=song_id_int, week=week, month=month, year=year).first()
        if not stat:
            print(f'[DEBUG] Chưa có BXH tuần/tháng, tạo mới với week={week}, month={month}, year={year}')
            stat = SongRankStats(song_id=song_id_int, week=week, month=month, year=year, week_plays=1, month_plays=1, all_plays=1, last_updated=now)
            db.session.add(stat)
        else:
            # Reset week_plays nếu sang tuần mới, month_plays nếu sang tháng mới
            if stat.week != week or stat.year != year:
                print(f'[DEBUG] Reset week_plays vì sang tuần mới (old={stat.week}, new={week})')
                stat.week_plays = 1
                stat.week = week
                stat.year = year
            else:
                stat.week_plays += 1
            if stat.month != month or stat.year != year:
                print(f'[DEBUG] Reset month_plays vì sang tháng mới (old={stat.month}, new={month})')
                stat.month_plays = 1
                stat.month = month
                stat.year = year
            else:
                stat.month_plays += 1
            stat.last_updated = now
            print(f'[DEBUG] BXH cập nhật: week_plays={stat.week_plays}, month_plays={stat.month_plays}')

        # Cập nhật all_plays cho tất cả các record SongRankStats của bài hát này
        from sqlalchemy import func
        # Flush to ensure the new ListeningHistory is persisted to the DB transaction so counts reflect it
        try:
            db.session.flush()
        except Exception:
            # flush may fail in some edge cases; we'll still attempt commit below
            pass
        total_listens_after = db.session.query(func.count()).select_from(ListeningHistory).filter_by(song_id=song_id_int).scalar()
        all_stats = SongRankStats.query.filter_by(song_id=song_id_int).all()
        for s in all_stats:
            s.all_plays = total_listens_after
        print(f'[DEBUG] Đã cập nhật all_plays={total_listens_after} cho mọi record BXH của song_id={song_id_int}')
        db.session.commit()
        print(f'[DEBUG] Commit thành công BXH cho song_id={song_id_int}, ListeningHistory id={lh.id}')
        # Kiểm tra lại số record ListeningHistory cho bài hát này (post-commit authoritative)
        try:
            total_listens = db.session.query(func.count()).select_from(ListeningHistory).filter_by(song_id=song_id_int).scalar()
        except Exception:
            total_listens = total_listens_after
        print(f'[DEBUG] Tổng số lượt nghe hiện tại của song_id={song_id_int} trong ListeningHistory: {total_listens}')
        return jsonify({'msg': 'Đã ghi lịch sử nghe', 'id': lh.id, 'week_plays': stat.week_plays, 'month_plays': stat.month_plays, 'all_plays': stat.all_plays, 'song_id': song_id_int, 'week': week, 'month': month, 'year': year, 'total_listens': int(total_listens)}), 201
    except Exception as e:
        db.session.rollback()
        print(f'[DEBUG] Commit BXH thất bại: {e} (song_id={song_id_int})')
        return jsonify({'msg': 'Lỗi ghi BXH', 'error': str(e), 'song_id': song_id_int, 'week': week, 'month': month, 'year': year}), 500
    identity = current_identity()
    user_id = identity.get('id')
    data = request.get_json() or {}
    song_id = data.get('song_id')
    if not song_id:
        return jsonify({'msg': 'Thiếu song_id'}), 400
    song = Song.query.get(song_id)
    if not song:
        return jsonify({'msg': 'Bài hát không tồn tại'}), 404
    lh = ListeningHistory(user_id=user_id, song_id=song_id)
    db.session.add(lh)

    # --- BXH tuần/tháng ---
    now = dt.datetime.now()
    week = int(now.strftime('%U'))  # Tuần trong năm (0-53)
    month = now.month
    year = now.year
    stat = SongRankStats.query.filter_by(song_id=song_id, week=week, month=month, year=year).first()
    if not stat:
        # Reset BXH tuần/tháng nếu sang tuần/tháng mới
        stat = SongRankStats(song_id=song_id, week=week, month=month, year=year, week_plays=1, month_plays=1, last_updated=now)
        db.session.add(stat)
    else:
        # Nếu đã có record tuần/tháng này, tăng lượt nghe
        stat.week_plays += 1
        stat.month_plays += 1
        stat.last_updated = now

    db.session.commit()
    return jsonify({'msg': 'Đã ghi lịch sử nghe', 'id': lh.id}), 201


@history_bp.route('/listening_history', methods=['GET'])
@jwt_required()
def get_history():
    identity = current_identity()
    user_id = identity.get('id')
    q = ListeningHistory.query.filter_by(user_id=user_id).order_by(ListeningHistory.listened_at.desc()).limit(200)
    out = []
    for item in q:
        song = Song.query.get(item.song_id)
        out.append({
            'id': item.id,
            'song_id': item.song_id,
            'title': song.title if song else None,
            'artist_name': song.artist_name if song else None,  # Sử dụng property (tất cả nghệ sĩ)
            'mp3_path': song.mp3_path if song else None,
            'album_image_path': (song.image_path or (song.album.cover_image_path if song.album else None)) if song else None,
            'listened_at': item.listened_at.isoformat() if item.listened_at else None
        })
    return jsonify(out), 200

# Đăng ký alias sau tất cả các hàm
@history_bp.route('/history/log', methods=['POST'])
@jwt_required()
def log_listen_alias():
    return log_listen()