#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script đơn giản để thêm nghệ sĩ vào bài hát"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config import Config
from src.extensions import db

# Khởi tạo Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def main():
    with app.app_context():
        # Import models sau khi đã có app context
        from src.models.music import Song, Artist
        
        print('=' * 80)
        print('🎵 CÔNG CỤ THÊM NGHỆ SĨ VÀO BÀI HÁT')
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
                # Hiển thị bài hát
                songs = db.session.query(Song).all()
                print('\n📋 Danh sách bài hát:')
                print('-' * 80)
                for s in songs:
                    artists = list(s.artists.all())
                    artist_names = ', '.join([a.name for a in artists]) if artists else 'Chưa có'
                    print(f'{s.id:3d}. {s.title:40s} - Nghệ sĩ: {artist_names}')
                print('-' * 80)
            
            elif choice == '2':
                # Hiển thị nghệ sĩ
                artists = db.session.query(Artist).all()
                print('\n🎤 Danh sách nghệ sĩ:')
                print('-' * 50)
                for a in artists:
                    song_count = a.songs.count()
                    print(f'{a.id:3d}. {a.name:40s} ({song_count} bài hát)')
                print('-' * 50)
            
            elif choice == '3':
                # Hiển thị danh sách để chọn
                songs = db.session.query(Song).all()
                print('\n📋 Danh sách bài hát:')
                for s in songs:
                    artists = list(s.artists.all())
                    artist_names = ', '.join([a.name for a in artists]) if artists else 'Chưa có'
                    print(f'{s.id:3d}. {s.title:40s} - Nghệ sĩ: {artist_names}')
                
                artists = db.session.query(Artist).all()
                print('\n🎤 Danh sách nghệ sĩ:')
                for a in artists:
                    print(f'{a.id:3d}. {a.name}')
                
                # Nhập thông tin
                song_id = input('\n📝 Nhập ID bài hát: ').strip()
                artist_ids = input('📝 Nhập ID nghệ sĩ (có thể nhiều, cách nhau bằng dấu phẩy): ').strip()
                
                if song_id and artist_ids:
                    try:
                        song_id = int(song_id)
                        song = db.session.query(Song).get(song_id)
                        
                        if not song:
                            print(f'❌ Không tìm thấy bài hát ID {song_id}')
                            continue
                        
                        for aid in artist_ids.split(','):
                            artist_id = int(aid.strip())
                            artist = db.session.query(Artist).get(artist_id)
                            
                            if not artist:
                                print(f'❌ Không tìm thấy nghệ sĩ ID {artist_id}')
                                continue
                            
                            # Kiểm tra đã có chưa
                            if artist in song.artists.all():
                                print(f'⚠️  Nghệ sĩ "{artist.name}" đã có trong bài hát "{song.title}"')
                            else:
                                song.artists.append(artist)
                                print(f'✅ Đã thêm nghệ sĩ "{artist.name}" vào bài hát "{song.title}"')
                        
                        db.session.commit()
                        print('💾 Đã lưu thay đổi!')
                        
                    except ValueError:
                        print('❌ ID không hợp lệ!')
                    except Exception as e:
                        print(f'❌ Lỗi: {e}')
                        db.session.rollback()
            
            elif choice == '4':
                # Xóa nghệ sĩ khỏi bài hát
                songs = db.session.query(Song).all()
                print('\n📋 Danh sách bài hát:')
                for s in songs:
                    artists = list(s.artists.all())
                    artist_names = ', '.join([a.name for a in artists]) if artists else 'Chưa có'
                    print(f'{s.id:3d}. {s.title:40s} - Nghệ sĩ: {artist_names}')
                
                song_id = input('\n📝 Nhập ID bài hát: ').strip()
                artist_id = input('📝 Nhập ID nghệ sĩ cần xóa: ').strip()
                
                if song_id and artist_id:
                    try:
                        song = db.session.query(Song).get(int(song_id))
                        artist = db.session.query(Artist).get(int(artist_id))
                        
                        if not song or not artist:
                            print('❌ Không tìm thấy bài hát hoặc nghệ sĩ')
                            continue
                        
                        if artist not in song.artists.all():
                            print(f'⚠️  Nghệ sĩ "{artist.name}" không có trong bài hát "{song.title}"')
                        else:
                            song.artists.remove(artist)
                            db.session.commit()
                            print(f'✅ Đã xóa nghệ sĩ "{artist.name}" khỏi bài hát "{song.title}"')
                    
                    except ValueError:
                        print('❌ ID không hợp lệ!')
                    except Exception as e:
                        print(f'❌ Lỗi: {e}')
                        db.session.rollback()
            
            elif choice == '5':
                print('\n👋 Tạm biệt!')
                break
            
            else:
                print('❌ Lựa chọn không hợp lệ!')

if __name__ == '__main__':
    main()
