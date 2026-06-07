# File: src/admin/song_artist_management.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.extensions import db
from src.models.music import Song, Artist
from src.jwt_helper import current_identity
from src.decorators import admin_required

song_artist_bp = Blueprint("song_artist_management", __name__, url_prefix="/admin/api/song-artists")


# --- Lấy danh sách nghệ sĩ của bài hát ---
@song_artist_bp.route('/<int:song_id>', methods=['GET'])
def get_song_artists(song_id):
    """Lấy danh sách nghệ sĩ của một bài hát"""
    song = Song.query.get(song_id)
    if not song:
        return jsonify({'error': 'Không tìm thấy bài hát'}), 404
    
    artists = list(song.artists.all())
    return jsonify({
        'song_id': song.id,
        'song_title': song.title,
        'artists': [
            {
                'id': a.id,
                'name': a.name,
                'image_path': a.image_path if a.image_path not in [None, "None", ""] else None
            } for a in artists
        ]
    }), 200


# --- Thêm nghệ sĩ vào bài hát ---
@song_artist_bp.route('/<int:song_id>/add', methods=['POST'])
@jwt_required()
@admin_required()
def add_artists_to_song(song_id):
    """Thêm một hoặc nhiều nghệ sĩ vào bài hát"""
    try:
        data = request.get_json() or {}
        artist_ids = data.get('artist_ids', [])  # Mảng IDs hoặc chuỗi "1,2,3"
        
        # Chuyển đổi nếu là string
        if isinstance(artist_ids, str):
            artist_ids = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
        
        if not artist_ids:
            return jsonify({'error': 'Thiếu artist_ids'}), 400
        
        # Kiểm tra bài hát
        song = Song.query.get(song_id)
        if not song:
            return jsonify({'error': 'Không tìm thấy bài hát'}), 404
        
        added_artists = []
        already_exists = []
        not_found = []
        
        for artist_id in artist_ids:
            artist = Artist.query.get(artist_id)
            
            if not artist:
                not_found.append(artist_id)
                continue
            
            # Kiểm tra đã có chưa
            if artist in song.artists.all():
                already_exists.append(artist.name)
            else:
                song.artists.append(artist)
                added_artists.append(artist.name)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'msg': f'Đã thêm {len(added_artists)} nghệ sĩ',
            'song_id': song.id,
            'song_title': song.title,
            'added_artists': added_artists,
            'already_exists': already_exists,
            'not_found': not_found,
            'current_artists': [a.name for a in song.artists.all()]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500


# --- Xóa nghệ sĩ khỏi bài hát ---
@song_artist_bp.route('/<int:song_id>/remove', methods=['POST'])
@jwt_required()
@admin_required()
def remove_artists_from_song(song_id):
    """Xóa một hoặc nhiều nghệ sĩ khỏi bài hát"""
    try:
        data = request.get_json() or {}
        artist_ids = data.get('artist_ids', [])
        
        # Chuyển đổi nếu là string
        if isinstance(artist_ids, str):
            artist_ids = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
        
        if not artist_ids:
            return jsonify({'error': 'Thiếu artist_ids'}), 400
        
        # Kiểm tra bài hát
        song = Song.query.get(song_id)
        if not song:
            return jsonify({'error': 'Không tìm thấy bài hát'}), 404
        
        removed_artists = []
        not_in_song = []
        not_found = []
        
        for artist_id in artist_ids:
            artist = Artist.query.get(artist_id)
            
            if not artist:
                not_found.append(artist_id)
                continue
            
            # Kiểm tra có trong bài hát không
            if artist not in song.artists.all():
                not_in_song.append(artist.name)
            else:
                song.artists.remove(artist)
                removed_artists.append(artist.name)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'msg': f'Đã xóa {len(removed_artists)} nghệ sĩ',
            'song_id': song.id,
            'song_title': song.title,
            'removed_artists': removed_artists,
            'not_in_song': not_in_song,
            'not_found': not_found,
            'current_artists': [a.name for a in song.artists.all()]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500


# --- Cập nhật toàn bộ danh sách nghệ sĩ của bài hát ---
@song_artist_bp.route('/<int:song_id>/update', methods=['PUT'])
@jwt_required()
@admin_required()
def update_song_artists(song_id):
    """Thay thế toàn bộ danh sách nghệ sĩ của bài hát"""
    try:
        data = request.get_json() or {}
        artist_ids = data.get('artist_ids', [])
        
        # Chuyển đổi nếu là string
        if isinstance(artist_ids, str):
            artist_ids = [int(aid.strip()) for aid in artist_ids.split(',') if aid.strip()]
        
        # Kiểm tra bài hát
        song = Song.query.get(song_id)
        if not song:
            return jsonify({'error': 'Không tìm thấy bài hát'}), 404
        
        # Lưu danh sách cũ
        old_artists = [a.name for a in song.artists.all()]
        
        # Xóa tất cả nghệ sĩ hiện tại
        current_artists = list(song.artists.all())
        for artist in current_artists:
            song.artists.remove(artist)
        
        # Thêm nghệ sĩ mới
        new_artists = []
        not_found = []
        
        for artist_id in artist_ids:
            artist = Artist.query.get(artist_id)
            if artist:
                song.artists.append(artist)
                new_artists.append(artist.name)
            else:
                not_found.append(artist_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'msg': 'Đã cập nhật danh sách nghệ sĩ',
            'song_id': song.id,
            'song_title': song.title,
            'old_artists': old_artists,
            'new_artists': new_artists,
            'not_found': not_found
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500


# --- Thêm nghệ sĩ vào nhiều bài hát ---
@song_artist_bp.route('/bulk-add', methods=['POST'])
@jwt_required()
@admin_required()
def bulk_add_artist_to_songs():
    """Thêm một nghệ sĩ vào nhiều bài hát"""
    try:
        data = request.get_json() or {}
        artist_id = data.get('artist_id')
        song_ids = data.get('song_ids', [])
        
        if not artist_id:
            return jsonify({'error': 'Thiếu artist_id'}), 400
        
        if not song_ids:
            return jsonify({'error': 'Thiếu song_ids'}), 400
        
        # Chuyển đổi nếu là string
        if isinstance(song_ids, str):
            song_ids = [int(sid.strip()) for sid in song_ids.split(',') if sid.strip()]
        
        # Kiểm tra nghệ sĩ
        artist = Artist.query.get(artist_id)
        if not artist:
            return jsonify({'error': 'Không tìm thấy nghệ sĩ'}), 404
        
        added_to_songs = []
        already_exists = []
        not_found = []
        
        for song_id in song_ids:
            song = Song.query.get(song_id)
            
            if not song:
                not_found.append(song_id)
                continue
            
            if artist in song.artists.all():
                already_exists.append(song.title)
            else:
                song.artists.append(artist)
                added_to_songs.append(song.title)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'msg': f'Đã thêm nghệ sĩ "{artist.name}" vào {len(added_to_songs)} bài hát',
            'artist_id': artist.id,
            'artist_name': artist.name,
            'added_to_songs': added_to_songs,
            'already_exists': already_exists,
            'not_found': not_found
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500


# --- Xóa nghệ sĩ khỏi nhiều bài hát ---
@song_artist_bp.route('/bulk-remove', methods=['POST'])
@jwt_required()
@admin_required()
def bulk_remove_artist_from_songs():
    """Xóa một nghệ sĩ khỏi nhiều bài hát"""
    try:
        data = request.get_json() or {}
        artist_id = data.get('artist_id')
        song_ids = data.get('song_ids', [])
        
        if not artist_id:
            return jsonify({'error': 'Thiếu artist_id'}), 400
        
        if not song_ids:
            return jsonify({'error': 'Thiếu song_ids'}), 400
        
        # Chuyển đổi nếu là string
        if isinstance(song_ids, str):
            song_ids = [int(sid.strip()) for sid in song_ids.split(',') if sid.strip()]
        
        # Kiểm tra nghệ sĩ
        artist = Artist.query.get(artist_id)
        if not artist:
            return jsonify({'error': 'Không tìm thấy nghệ sĩ'}), 404
        
        removed_from_songs = []
        not_in_song = []
        not_found = []
        
        for song_id in song_ids:
            song = Song.query.get(song_id)
            
            if not song:
                not_found.append(song_id)
                continue
            
            if artist not in song.artists.all():
                not_in_song.append(song.title)
            else:
                song.artists.remove(artist)
                removed_from_songs.append(song.title)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'msg': f'Đã xóa nghệ sĩ "{artist.name}" khỏi {len(removed_from_songs)} bài hát',
            'artist_id': artist.id,
            'artist_name': artist.name,
            'removed_from_songs': removed_from_songs,
            'not_in_song': not_in_song,
            'not_found': not_found
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500
