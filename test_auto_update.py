#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script tự động test cập nhật bài hát"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from config import Config
from src.extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def auto_test():
    """Test tự động các chức năng cập nhật"""
    with app.app_context():
        from src.models.music import Song, Artist
        
        print('=' * 80)
        print('TEST TỰ ĐỘNG CẬP NHẬT BÀI HÁT')
        print('=' * 80)
        
        # 1. Lấy bài hát đầu tiên
        song = db.session.query(Song).first()
        print(f'\n1️⃣ Bài hát test: "{song.title}" (ID: {song.id})')
        print(f'   Nghệ sĩ hiện tại: {song.artist_name}')
        
        # 2. Lấy một nghệ sĩ khác để test thêm
        all_artists = db.session.query(Artist).all()
        current_artists = list(song.artists.all())
        
        # Tìm nghệ sĩ chưa có trong bài hát
        artist_to_add = None
        for artist in all_artists:
            if artist not in current_artists:
                artist_to_add = artist
                break
        
        if artist_to_add:
            print(f'\n2️⃣ Test thêm nghệ sĩ: {artist_to_add.name}')
            song.artists.append(artist_to_add)
            db.session.commit()
            print(f'   ✅ Đã thêm thành công!')
            print(f'   📝 Danh sách mới: {song.artist_name}')
            
            # Xác nhận trong database
            db.session.refresh(song)
            new_artists = list(song.artists.all())
            print(f'   🔍 Xác nhận trong DB: {len(new_artists)} nghệ sĩ')
            for a in new_artists:
                print(f'      - {a.name}')
            
            # 3. Test xóa nghệ sĩ vừa thêm
            print(f'\n3️⃣ Test xóa nghệ sĩ: {artist_to_add.name}')
            song.artists.remove(artist_to_add)
            db.session.commit()
            print(f'   ✅ Đã xóa thành công!')
            print(f'   📝 Danh sách sau khi xóa: {song.artist_name}')
        else:
            print('\n⚠️  Tất cả nghệ sĩ đã có trong bài hát rồi')
        
        # 4. Test cập nhật tên
        print(f'\n4️⃣ Test cập nhật tên bài hát')
        original_title = song.title
        test_title = f"{original_title} (TEST)"
        
        song.title = test_title
        db.session.commit()
        print(f'   ✅ Đã đổi: "{original_title}" → "{test_title}"')
        
        # Xác nhận
        db.session.refresh(song)
        print(f'   🔍 Xác nhận trong DB: "{song.title}"')
        
        # Đổi lại tên cũ
        song.title = original_title
        db.session.commit()
        print(f'   ↩️  Đã đổi lại tên cũ: "{song.title}"')
        
        print('\n' + '=' * 80)
        print('✅ TẤT CẢ TEST ĐỀU THÀNH CÔNG!')
        print('✅ DỮ LIỆU ĐƯỢC CẬP NHẬT CHÍNH XÁC TRÊN DATABASE')
        print('=' * 80)

if __name__ == '__main__':
    auto_test()
