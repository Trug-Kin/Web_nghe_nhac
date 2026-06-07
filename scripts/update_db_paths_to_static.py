# Script to update all file paths in the database from 'DoAnCoSo/' to 'static/' or just remove 'DoAnCoSo/'
# Run this script once after migrating your static files and code

from app import app
from src.extensions import db
from src.models.music import Song, Album, Artist

with app.app_context():
    # Update Song paths
    songs = Song.query.all()
    for song in songs:
        changed = False
        if song.mp3_path and song.mp3_path.startswith('DoAnCoSo/'):
            song.mp3_path = song.mp3_path[len('DoAnCoSo/'):]
            changed = True
        if song.image_path and song.image_path.startswith('DoAnCoSo/'):
            song.image_path = song.image_path[len('DoAnCoSo/'):]
            changed = True
        if changed:
            print(f"Updated Song ID {song.id}")
    # Update Album images
    albums = Album.query.all()
    for album in albums:
        if album.image_path and album.image_path.startswith('DoAnCoSo/'):
            album.image_path = album.image_path[len('DoAnCoSo/'):]
            print(f"Updated Album ID {album.id}")
    # Update Artist avatars
    artists = Artist.query.all()
    for artist in artists:
        if artist.avatar and artist.avatar.startswith('DoAnCoSo/'):
            artist.avatar = artist.avatar[len('DoAnCoSo/'):]
            print(f"Updated Artist ID {artist.id}")
    db.session.commit()
    print("All paths updated.")
