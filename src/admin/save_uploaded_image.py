import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_image(file, subfolder):
    if not file or not file.filename:
        return None
    filename = secure_filename(file.filename)
    # Normalize subfolder so callers can pass either 'images/songs' or os.path.join('static','images','songs')
    if not subfolder:
        subfolder = ''
    # Normalize separators to '/'
    subfolder_norm = str(subfolder).replace('\\', '/').lstrip('/')
    # Remove leading 'static/' if present to avoid creating static/static/...
    if subfolder_norm.startswith('static/'):
        subfolder_norm = subfolder_norm[len('static/'):]
    # Final upload folder is inside the app's static folder
    upload_folder = os.path.join(current_app.static_folder, subfolder_norm)
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    # Trả về đường dẫn tương đối để lưu vào DB (bắt đầu từ 'static/...')
    rel_path = os.path.relpath(file_path, current_app.static_folder)
    # Ensure we return a POSIX-style relative path without any leading 'static/'
    rel_path = rel_path.replace('\\', '/')
    if rel_path.startswith('static/'):
        rel_path = rel_path[len('static/'):]
    return rel_path
