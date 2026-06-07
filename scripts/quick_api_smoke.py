"""Quick smoke test for playlist and listening history endpoints.
Run: python scripts/quick_api_smoke.py
"""
from app import create_app
from src.models import db
from werkzeug.security import generate_password_hash

app = create_app()
app.config['TESTING'] = True

USERNAME = 'smoke_user'
PASSWORD = 'pass'

def ensure_user():
    from src.models.user import User
    u = User.query.filter_by(username=USERNAME).first()
    if not u:
        u = User(username=USERNAME, email=f'{USERNAME}@example.test', password=generate_password_hash(PASSWORD), role='user')
        db.session.add(u)
        db.session.commit()
        print('Created user', u.id)
    return u

with app.app_context():
    client = app.test_client()
    ensure_user()
    # login
    r = client.post('/auth/login', json={'username':USERNAME, 'password':PASSWORD})
    print('Login status:', r.status_code)
    # create playlist
    r2 = client.post('/api/playlists', json={'name':'smoke_playlist'})
    print('Create playlist:', r2.status_code, r2.get_json())
    pid = (r2.get_json() or {}).get('id')
    # list playlists
    r3 = client.get('/api/playlists/')
    print('List playlists:', r3.status_code, len(r3.get_json() or []))
    # log listen (song id 1 if exists)
    from src.models.music import Song
    s = Song.query.first()
    if s:
        r4 = client.post('/api/listen', json={'song_id': s.id})
        print('Log listen:', r4.status_code)
        r5 = client.get('/api/listening_history')
        print('History count:', len(r5.get_json() or []))
    else:
        print('No song found; skipping listen test.')
    print('Smoke test complete.')