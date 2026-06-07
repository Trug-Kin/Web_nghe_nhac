"""scripts/test_playlists.py

Quick test runner to verify playlist flows for user/uploader/admin using Flask test client.
Run from project root with the project's venv active:

venv\Scripts\python scripts\test_playlists.py

This script is intentionally simple and idempotent for local dev debugging.
"""

from app import create_app
from src.models import db
from werkzeug.security import generate_password_hash
import json

app = create_app()
app.config['TESTING'] = True

USERS = [
    {'username':'ptest_user','email':'ptest_user@example.test','password':'pass','role':'user'},
    {'username':'ptest_uploader','email':'ptest_uploader@example.test','password':'pass','role':'uploader'},
    {'username':'ptest_admin','email':'ptest_admin@example.test','password':'pass','role':'admin'}
]


def ensure_user(username, email, password, role='user'):
    from src.models.user import User
    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(username=username, email=email, password=generate_password_hash(password), role=role)
        db.session.add(u)
        db.session.commit()
        print(f'Created user {username} id={u.id} role={role}')
    else:
        if u.role != role:
            u.role = role
            db.session.commit()
            print(f'Updated role for {username} -> {role}')
    return u


with app.app_context():
    client = app.test_client()

    # Ensure sample song exists for add/remove tests
    from src.models.music import Song
    song = Song.query.first()
    if not song:
        print('No song found in DB; skipping add/remove song tests.')

    # Register/ensure users
    for u in USERS:
        ensure_user(u['username'], u['email'], u['password'], u['role'])

    def login(client, username, password):
        r = client.post('/auth/login', json={'username':username,'password':password})
        print(f'Login {username}:', r.status_code)
        return r.status_code == 200

    # Run flows for each user
    for u in USERS:
        print('\n--- Testing flow for', u['username'], 'role=', u['role'])
        ok = login(client, u['username'], u['password'])
        if not ok:
            print('Login failed; skipping')
            continue

        # Create playlist
        r = client.post('/api/playlists', json={'name':f"pl_{u['username']}", 'description':'test'})
        print('Create playlist status:', r.status_code, r.get_data(as_text=True))
        if r.status_code not in (200,201):
            continue
        try:
            created = r.get_json() or {}
            pid = created.get('id')
        except Exception:
            pid = None

        # List playlists
        r2 = client.get('/api/playlists')
        print('List playlists status:', r2.status_code)
        try:
            print('List body:', json.dumps(r2.get_json(), ensure_ascii=False))
        except Exception:
            pass

        # Add song if possible
        if song and pid:
            r3 = client.post(f'/api/playlists/{pid}/add_song', json={'song_id': song.id})
            print('Add song status:', r3.status_code, r3.get_data(as_text=True))
            r4 = client.post(f'/api/playlists/{pid}/remove_song', json={'song_id': song.id})
            print('Remove song status:', r4.status_code, r4.get_data(as_text=True))

    print('\nAll flows executed.\n')
