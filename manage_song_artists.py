#!/usr/bin/env python
"""Script to add artists to existing songs"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config import Config
from src.extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Import models AFTER app context
with app.app_context():
    from src.models.music import Song, Artist

def show_songs():
    """Hiển thị danh sách bài hát"""
    songs = Song.query.all()
    print('\n📋 Danh sách bài hát:')
    print('-' * 80)
    for s in songs:
        artists = list(s.artists.all())
        artist_names = ', '.join([a.name for a in artists]) if artists else 'Chưa có'
        print(f'{s.id:3d}. {s.title:40s} - Nghệ sĩ: {artist_names}')
    print('-' * 80)

def show_artists():
    """Hiển thị danh sách nghệ sĩ"""
    artists = Artist.query.all()
    print('\n🎤 Danh sách nghệ sĩ:')
    print('-' * 50)
    for a in artists:
        song_count = a.songs.count()
        print(f'{a.id:3d}. {a.name:40s} ({song_count} bài hát)')
    print('-' * 50)

def add_artist_to_song(song_id, artist_id):
    """Thêm nghệ sĩ vào bài hát"""
    song = Song.query.get(song_id)
    artist = Artist.query.get(artist_id)
    
    if not song:
        print(f'❌ Không tìm thấy bài hát ID {song_id}')
        return False
    
    if not artist:
        print(f'❌ Không tìm thấy nghệ sĩ ID {artist_id}')
        return False
    
    # Kiểm tra xem nghệ sĩ đã được thêm chưa
    if artist in song.artists.all():
        print(f'⚠️  Nghệ sĩ "{artist.name}" đã có trong bài hát "{song.title}"')
        return False
    
    # Thêm nghệ sĩ vào bài hát
    song.artists.append(artist)
    db.session.commit()
    print(f'✅ Đã thêm nghệ sĩ "{artist.name}" vào bài hát "{song.title}"')
    return True

def remove_artist_from_song(song_id, artist_id):
    """Xóa nghệ sĩ khỏi bài hát"""
    song = Song.query.get(song_id)
    artist = Artist.query.get(artist_id)
    
    if not song or not artist:
        print(f'❌ Không tìm thấy bài hát hoặc nghệ sĩ')
        return False
    
    if artist not in song.artists.all():
        print(f'⚠️  Nghệ sĩ "{artist.name}" không có trong bài hát "{song.title}"')
        return False
    
    song.artists.remove(artist)
    db.session.commit()
    print(f'✅ Đã xóa nghệ sĩ "{artist.name}" khỏi bài hát "{song.title}"')
    return True

with app.app_context():
    print('=' * 80)
    print('🎵 QUẢN LÝ NGHỆ SĨ CHO BÀI HÁT')
    print('=' * 80)
    
    while True:
        print('\n📌 Menu:')
        print('1. Hiển thị danh sách bài hát')
        print('2. Hiển thị danh sách nghệ sĩ')
        print('3. Thêm nghệ sĩ vào bài hát')
        print('4. Xóa nghệ sĩ khỏi bài hát')
        print('5. Thoát')
        
        choice = input('\n👉 Chọn (1-5): ').strip()
        
        if choice == '1':
            show_songs()
        
        elif choice == '2':
            show_artists()
        
        elif choice == '3':
            show_songs()
            show_artists()
            song_id = input('\n📝 Nhập ID bài hát: ').strip()
            artist_ids = input('📝 Nhập ID nghệ sĩ (có thể nhiều, cách nhau bằng dấu phẩy): ').strip()
            
            if song_id and artist_ids:
                try:
                    song_id = int(song_id)
                    for aid in artist_ids.split(','):
                        artist_id = int(aid.strip())
                        add_artist_to_song(song_id, artist_id)
                except ValueError:
                    print('❌ ID không hợp lệ!')
        
        elif choice == '4':
            show_songs()
            song_id = input('\n📝 Nhập ID bài hát: ').strip()
            artist_id = input('📝 Nhập ID nghệ sĩ: ').strip()
            
            if song_id and artist_id:
                try:
                    remove_artist_from_song(int(song_id), int(artist_id))
                except ValueError:
                    print('❌ ID không hợp lệ!')
        
        elif choice == '5':
            print('\n👋 Thoát chương trình!')
            break
        
        else:
            print('❌ Lựa chọn không hợp lệ!')
