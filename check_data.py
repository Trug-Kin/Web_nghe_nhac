from src.extensions import db
from src.models.music import Artist, Album, Song
from app import create_app

app = create_app()

with app.app_context():
    a = Artist.query.first()
    al = Album.query.first()
    s = Song.query.first()
    
    print('=== ARTIST ===')
    if a:
        print(f'ID: {a.id}')
        print(f'Name: {a.name}')
        print(f'Image: {a.image_path}')
    else:
        print('No artist found')
    
    print('\n=== ALBUM ===')
    if al:
        print(f'ID: {al.id}')
        print(f'Title: {al.title}')
        print(f'Image: {al.cover_image_path}')
    else:
        print('No album found')
    
    print('\n=== SONG ===')
    if s:
        print(f'ID: {s.id}')
        print(f'Title: {s.title}')
        print(f'Image: {s.image_path}')
        print(f'MP3: {s.mp3_path}')
    else:
        print('No song found')
