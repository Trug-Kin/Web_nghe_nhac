#!/usr/bin/env python3
"""
Normalize Song.mp3_path values in the database so they point to files under DoAnCoSo/music/.
Run with --apply to perform updates; default is dry-run.

Usage:
  python scripts/normalize_mp3_paths.py --apply
"""
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true', help='Apply updates to DB')
args = parser.parse_args()

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC_MUSIC_DIR = os.path.join(BASE, 'DoAnCoSo', 'music')
print('Project root:', BASE)
print('Static music dir:', STATIC_MUSIC_DIR)

# prepare app context
try:
    from app import create_app
    app = create_app()
except Exception as e:
    print('Failed to import create_app():', e)
    raise

with app.app_context():
    from src.models import db
    from src.models import Song

    songs = Song.query.all()
    print('Found', len(songs), 'songs in DB')
    changes = []
    for s in songs:
        orig = (s.mp3_path or '').strip() if s.mp3_path else ''
        if not orig:
            # skip empty
            continue
        # if absolute URL, skip
        if orig.lower().startswith('http://') or orig.lower().startswith('https://'):
            continue
        # derive basename
        candidate = os.path.basename(orig)
        # try DoAnCoSo/music/{basename}
        path1 = os.path.join(STATIC_MUSIC_DIR, candidate)
        # try DoAnCoSo/{orig} (if orig contains folder)
        path2 = os.path.join(BASE, orig.lstrip('/'))
        new_mp3_path = None
        if os.path.isfile(path1):
            new_mp3_path = f'music/{candidate}'
        elif os.path.isfile(path2):
            # if file exists under DoAnCoSo/<orig>
            rel = os.path.relpath(path2, os.path.join(BASE, 'DoAnCoSo'))
            new_mp3_path = rel.replace('\\', '/')
        else:
            # try if orig already has 'music/' and file exists
            if orig.startswith('music/'):
                p = os.path.join(BASE, 'DoAnCoSo', orig)
                if os.path.isfile(p):
                    new_mp3_path = orig
        if new_mp3_path and new_mp3_path != orig:
            print(f"Would update Song(id={s.id}) from '{orig}' -> '{new_mp3_path}'")
            changes.append((s, orig, new_mp3_path))

    if not changes:
        print('No changes detected. Nothing to do.')
    else:
        print('Planned changes:', len(changes))
        if args.apply:
            for s, orig, new in changes:
                print(f"Updating Song {s.id}: {orig} -> {new}")
                s.mp3_path = new
            db.session.commit()
            print('Committed changes to DB.')
        else:
            print('Dry-run mode (no DB changes). Re-run with --apply to apply updates.')
