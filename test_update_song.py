#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script kiểm tra API cập nhật bài hát"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config import Config
from src.extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def test_update_song():
    """Kiểm tra xem dữ liệu đã được cập nhật chưa"""
    with app.app_context():
        from src.models.music import Song, Artist
        
        print('=' * 80)
        print('KIỂM TRA CẬP NHẬT BÀI HÁT')
        print('=' * 80)
        
        # Lấy bài hát đầu tiên để test
        song = db.session.query(Song).first()
        
        if not song:
            print('❌ Không có bài hát nào trong database')
            return
        
        print(f'\n📋 Bài hát ID: {song.id}')
        print(f'   Tên: {song.title}')
        print(f'   MP3: {song.mp3_path}')
        print(f'   Ảnh: {song.image_path or "(chưa có)"}')
        print(f'   Album ID: {song.album_id}')
        print(f'   Genre ID: {song.genre_id}')
        print(f'   Artist ID (cũ): {song.artist_id}')
        
        # Lấy danh sách nghệ sĩ từ many-to-many
        artists = list(song.artists.all())
        print(f'\n🎤 Nghệ sĩ (many-to-many):')
        if artists:
            for artist in artists:
                print(f'   - {artist.name} (ID: {artist.id})')
        else:
            print('   (chưa có)')
        
        print(f'\n📝 Artist Name Property: {song.artist_name}')
        
        # Test thử cập nhật
        print('\n' + '=' * 80)
        print('TEST CẬP NHẬT')
        print('=' * 80)
        
        choice = input('\nBạn có muốn test cập nhật bài hát này không? (y/n): ').strip().lower()
        
        if choice == 'y':
            print('\nChọn thao tác:')
            print('1. Thêm nghệ sĩ vào bài hát')
            print('2. Xóa nghệ sĩ khỏi bài hát')
            print('3. Cập nhật tên bài hát')
            print('4. Hiển thị tất cả nghệ sĩ có thể thêm')
            
            action = input('\nChọn (1-4): ').strip()
            
            if action == '1':
                # Hiển thị danh sách nghệ sĩ
                all_artists = db.session.query(Artist).all()
                print('\n🎤 Danh sách nghệ sĩ:')
                for a in all_artists:
                    is_in_song = a in artists
                    status = '✅ (đã có)' if is_in_song else ''
                    print(f'{a.id:3d}. {a.name:30s} {status}')
                
                artist_ids = input('\nNhập ID nghệ sĩ cần thêm (cách nhau bằng dấu phẩy): ').strip()
                if artist_ids:
                    for aid in artist_ids.split(','):
                        artist_id = int(aid.strip())
                        artist = db.session.query(Artist).get(artist_id)
                        
                        if not artist:
                            print(f'❌ Không tìm thấy nghệ sĩ ID {artist_id}')
                            continue
                        
                        if artist in song.artists.all():
                            print(f'⚠️  Nghệ sĩ "{artist.name}" đã có trong bài hát')
                        else:
                            song.artists.append(artist)
                            print(f'✅ Đã thêm nghệ sĩ "{artist.name}"')
                    
                    db.session.commit()
                    print('\n💾 Đã lưu vào database!')
                    
                    # Hiển thị lại
                    print(f'\n📝 Danh sách nghệ sĩ mới: {song.artist_name}')
            
            elif action == '2':
                if not artists:
                    print('❌ Bài hát chưa có nghệ sĩ nào')
                else:
                    print('\n🎤 Nghệ sĩ hiện tại:')
                    for i, a in enumerate(artists, 1):
                        print(f'{i}. {a.name} (ID: {a.id})')
                    
                    artist_id = input('\nNhập ID nghệ sĩ cần xóa: ').strip()
                    if artist_id:
                        artist = db.session.query(Artist).get(int(artist_id))
                        if artist and artist in song.artists.all():
                            song.artists.remove(artist)
                            db.session.commit()
                            print(f'✅ Đã xóa nghệ sĩ "{artist.name}"')
                            print(f'📝 Danh sách nghệ sĩ mới: {song.artist_name}')
                        else:
                            print('❌ Nghệ sĩ không có trong bài hát')
            
            elif action == '3':
                new_title = input(f'\nNhập tên mới (hiện tại: {song.title}): ').strip()
                if new_title:
                    old_title = song.title
                    song.title = new_title
                    db.session.commit()
                    print(f'✅ Đã đổi tên từ "{old_title}" → "{new_title}"')
                    print('💾 Đã lưu vào database!')
            
            elif action == '4':
                all_artists = db.session.query(Artist).all()
                print('\n🎤 Tất cả nghệ sĩ trong database:')
                for a in all_artists:
                    song_count = a.songs.count()
                    print(f'{a.id:3d}. {a.name:30s} ({song_count} bài hát)')

if __name__ == '__main__':
    test_update_song()
