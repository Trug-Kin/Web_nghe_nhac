#!/usr/bin/env python
"""Script to verify song_artists table and data"""

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
            # Kiểm tra bảng song_artists có tồn tại không
            result = conn.execute(text("SHOW TABLES LIKE 'song_artists'"))
            if result.fetchone():
                print('✅ Bảng song_artists đã tồn tại trong database')
                
                # Đếm số bản ghi
                count_result = conn.execute(text('SELECT COUNT(*) as count FROM song_artists'))
                count = count_result.fetchone()[0]
                print(f'📊 Số lượng quan hệ song-artist: {count}')
                
                # Hiển thị 10 bản ghi đầu tiên
                if count > 0:
                    print('\n📋 10 quan hệ đầu tiên:')
                    sample = conn.execute(text('''
                        SELECT sa.song_id, s.title, sa.artist_id, a.name 
                        FROM song_artists sa
                        JOIN songs s ON sa.song_id = s.id
                        JOIN artists a ON sa.artist_id = a.id
                        LIMIT 10
                    '''))
                    for row in sample:
                        print(f'  Song ID {row[0]}: "{row[1]}" - Artist ID {row[2]}: "{row[3]}"')
                
                # Kiểm tra songs.artist_id đã nullable chưa
                print('\n🔍 Kiểm tra cột songs.artist_id:')
                col_result = conn.execute(text('''
                    SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'songs' AND COLUMN_NAME = 'artist_id'
                '''))
                col_info = col_result.fetchone()
                if col_info:
                    print(f'  artist_id: {col_info[2]} - Nullable: {col_info[1]}')
            else:
                print('❌ Bảng song_artists chưa được tạo!')
                
    except Exception as e:
        print(f'❌ Lỗi: {e}')
