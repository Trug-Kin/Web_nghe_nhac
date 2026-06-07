from flask import Blueprint, request, jsonify
from app.models import Genre  # Điều chỉnh import cho đúng với project của bạn
from app import db

admin_genre_bp = Blueprint('admin_genre', __name__)

# ... các route khác ...

@admin_genre_bp.route('/admin/api/genre/search')
def search_genre():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify(genres=[])
    genres = Genre.query.filter(Genre.name.ilike(f'%{keyword}%')).all()
    result = [
        {
            'id': g.id,
            'name': g.name,
            'color_class': getattr(g, 'color_class', None),
            'image_path': getattr(g, 'image_path', None)
        }
        for g in genres
    ]
    return jsonify(genres=result)
