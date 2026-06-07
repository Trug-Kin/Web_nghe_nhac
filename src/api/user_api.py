from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from src.jwt_helper import current_identity
from src.models.music import Artist

api_bp = Blueprint('api_user', __name__, url_prefix='/api/user')

@api_bp.route('/followed-artists')
@jwt_required(optional=True)
def followed_artists():
    """Return the list of artists the current user follows.

    This endpoint is tolerant: if no valid JWT is present, return an
    empty list (200) instead of 401. This keeps client-side UI simple
    and avoids leaving placeholders like 'Đang tải...'.
    """
    # Debug logging to help track why client cannot load followed artists
    try:
        current_app.logger.debug('[followed-artists-debug] request.path=%s', request.path)
        # log whether Authorization header was present
        current_app.logger.debug('[followed-artists-debug] Authorization header present=%s', bool(request.headers.get('Authorization')))
        # log cookie header (may contain access_token cookie)
        current_app.logger.debug('[followed-artists-debug] Cookie header=%s', request.headers.get('Cookie'))
    except Exception:
        # best-effort logging; swallow errors so endpoint continues
        pass

    identity = current_identity()
    if not identity or not identity.get('id'):
        # Unauthenticated: return empty list so client shows 'Chưa follow nghệ sĩ nào.'
        current_app.logger.debug('[followed-artists-debug] no identity found, returning empty list')
        return jsonify([]), 200

    current_app.logger.debug('[followed-artists-debug] identity resolved=%s', identity)

    from src.models import User
    from src.models.music import user_artist_followers
    from sqlalchemy import desc
    
    user = User.query.get(identity.get('id'))
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    # Join with user_artist_followers table to get followed_at timestamp
    # and order by followed_at descending (most recent first)
    artists = (
        Artist.query
        .join(user_artist_followers, Artist.id == user_artist_followers.c.artist_id)
        .filter(user_artist_followers.c.user_id == user.id)
        .order_by(desc(user_artist_followers.c.followed_at))
        .all()
    )
    
    return jsonify([
        {'id': a.id, 'name': a.name, 'image_path': a.image_path} for a in artists
    ])


@api_bp.route('/debug-auth-info')
@jwt_required(optional=True)
def debug_auth_info():
    """Debug endpoint to return headers, cookies and resolved identity.

    Call from the browser with credentials: fetch('/api/user/debug-auth-info', {credentials: 'include'})
    """
    try:
        identity = current_identity()
        # only expose Authorization and Cookie headers for debugging
        hdr = {}
        if request.headers.get('Authorization'):
            hdr['Authorization'] = request.headers.get('Authorization')
        if request.headers.get('Cookie'):
            hdr['Cookie'] = request.headers.get('Cookie')

        return jsonify({
            'headers': hdr,
            'cookies': dict(request.cookies),
            'identity': identity
        }), 200
    except Exception as e:
        current_app.logger.exception('debug_auth_info error')
        return jsonify({'error': str(e)}), 500
