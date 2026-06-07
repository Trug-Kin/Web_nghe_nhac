#!/usr/bin/env python
"""Script to create song_artists junction table for many-to-many relationship"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.extensions import db
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Tạo bảng song_artists
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS song_artists (
                    song_id INT NOT NULL,
                    artist_id INT NOT NULL,
                    PRIMARY KEY (song_id, artist_id),
                    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
                    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
                )
            '''))
            conn.commit()
            print('✅ Đã tạo bảng song_artists thành công!')
            
            # Migrate dữ liệu cũ từ songs.artist_id sang song_artists
            print('📋 Đang migrate dữ liệu cũ...')
            conn.execute(text('''
                INSERT INTO song_artists (song_id, artist_id)
                SELECT id, artist_id 
                FROM songs 
                WHERE artist_id IS NOT NULL
                ON DUPLICATE KEY UPDATE song_id=song_id
            '''))
            conn.commit()
            print('✅ Đã migrate dữ liệu từ songs.artist_id sang song_artists!')
            
            # Thay đổi artist_id thành nullable
            conn.execute(text('ALTER TABLE songs MODIFY artist_id INT NULL'))
            conn.commit()
            print('✅ Đã thay đổi songs.artist_id thành nullable!')
            
    except Exception as e:
        if '1050' in str(e):  # Table already exists
            print('ℹ️  Bảng song_artists đã tồn tại')
        else:
            print(f'❌ Lỗi: {e}')
