#!/usr/bin/env python
"""Script to add image_path column to songs table"""

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
        # Thêm cột image_path vào bảng songs
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE songs ADD COLUMN image_path VARCHAR(255) DEFAULT NULL'))
            conn.commit()
        print('✅ Đã thêm cột image_path vào bảng songs thành công!')
    except Exception as e:
        if '1060' in str(e):  # Duplicate column name
            print('ℹ️  Cột image_path đã tồn tại trong bảng songs')
        else:
            print(f'❌ Lỗi: {e}')
