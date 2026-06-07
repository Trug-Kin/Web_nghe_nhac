import datetime as dt
from sqlalchemy import func
from src.extensions import db
from src.models.music import Artist, Song, ListeningHistory, playlist_songs, user_artist_followers, ArtistStats, SearchEvent
from config import RISING_SCORE_WEIGHTS, RISING_GROWTH_RATE_MAX

# Run: python -m scripts.update_artist_stats (after app context setup)

def compute_metrics_for_artist(artist: Artist, now: dt.datetime):
    start_current = now - dt.timedelta(days=30)
    start_previous = now - dt.timedelta(days=60)
    # Streams current 30d
    streams_current = db.session.query(func.count(ListeningHistory.id)) \
        .join(Song, ListeningHistory.song_id == Song.id) \
        .filter(ListeningHistory.listened_at >= start_current) \
        .filter(ListeningHistory.song_id == Song.id) \
        .filter((Song.artist_id == artist.id) | (Song.artists.any(id=artist.id))) \
        .scalar() or 0
    # Streams previous 30d
    streams_previous = db.session.query(func.count(ListeningHistory.id)) \
        .join(Song, ListeningHistory.song_id == Song.id) \
        .filter(ListeningHistory.listened_at >= start_previous, ListeningHistory.listened_at < start_current) \
        .filter((Song.artist_id == artist.id) | (Song.artists.any(id=artist.id))) \
        .scalar() or 0
    # Playlist adds current 30d
    playlist_adds = db.session.query(func.count(playlist_songs.c.song_id)) \
        .join(Song, playlist_songs.c.song_id == Song.id) \
        .filter(playlist_songs.c.added_at >= start_current) \
        .filter((Song.artist_id == artist.id) | (Song.artists.any(id=artist.id))) \
        .scalar() or 0
    # Followers new current 30d
    followers_new = db.session.query(func.count(user_artist_followers.c.user_id)) \
        .filter(user_artist_followers.c.artist_id == artist.id) \
        .filter(user_artist_followers.c.followed_at >= start_current) \
        .scalar() or 0
    # Search hits & social mentions placeholders
    # Search hits last 30d (count distinct events for this artist)
    search_hits = db.session.query(func.count(SearchEvent.id)) \
        .filter(SearchEvent.artist_id == artist.id) \
        .filter(SearchEvent.created_at >= start_current) \
        .scalar() or 0
    social_mentions = 0
    # Growth rate
    growth_rate = (streams_current - streams_previous) / max(streams_previous, 1)
    if growth_rate > RISING_GROWTH_RATE_MAX:
        growth_rate = RISING_GROWTH_RATE_MAX
    # Rising score
    w = RISING_SCORE_WEIGHTS
    rising_score = (
        (growth_rate * 100) * w['growth_rate'] +
        (followers_new / 1000.0) * w['followers_new'] +
        (playlist_adds / 500.0) * w['playlist_adds'] +
        (search_hits / 200.0) * w['search_hits'] +
        (social_mentions / 200.0) * w['social_mentions']
    )
    return dict(streams_current=streams_current, streams_previous=streams_previous, followers_new=followers_new,
                playlist_adds=playlist_adds, search_hits=search_hits, social_mentions=social_mentions,
                growth_rate=growth_rate, rising_score=rising_score)


TOP_LIMIT = 20

def update_all_artists(app):
    now = dt.datetime.utcnow()
    artists = Artist.query.all()
    for artist in artists:
        metrics = compute_metrics_for_artist(artist, now)
        stats = ArtistStats.query.get(artist.id)
        if not stats:
            stats = ArtistStats(artist_id=artist.id)
            db.session.add(stats)
        for k, v in metrics.items():
            setattr(stats, k, v)
        # EMA smoothing for rising_score
        if (stats.moving_avg_score or 0) <= 0:
            stats.moving_avg_score = metrics['rising_score']
        else:
            stats.moving_avg_score = (stats.moving_avg_score * 0.7) + (metrics['rising_score'] * 0.3)
        stats.window_start = now - dt.timedelta(days=30)
        stats.window_end = now
        stats.updated_at = now
    db.session.flush()
    # Compute ranking and update badge fields
    ranked = ArtistStats.query.order_by(ArtistStats.rising_score.desc()).limit(TOP_LIMIT).all()
    for idx, r in enumerate(ranked, start=1):
        was_in_top = r.last_rank is not None and r.last_rank <= TOP_LIMIT
        r.last_rank = idx
        if not was_in_top:
            r.appearances_count = (r.appearances_count or 0) + 1
            if not r.first_seen_in_top_at:
                r.first_seen_in_top_at = now
    db.session.commit()
    print(f"Updated stats & ranking for {len(artists)} artists at {now}")

if __name__ == '__main__':
    # Example manual run: ensure app context
    from app import create_app  # adjust if your factory differs
    flask_app = create_app()
    with flask_app.app_context():
        update_all_artists(flask_app)
