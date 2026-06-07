from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from src.extensions import db
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from src.admin.user_management import admin_users
from src.extensions import login_manager
from flask import redirect, url_for, request, jsonify

migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, 
                template_folder='src/templates', 
                static_folder='static',
                static_url_path='/static'
                )
    # API: User followed artists
    from src.api.user_api import api_bp as user_api_bp
    app.register_blueprint(user_api_bp)
    
    # API: User follow/search
    from src.api.user_routes import user_api_bp as user_routes_bp
    app.register_blueprint(user_routes_bp)
    
    app.config.from_object(Config)

    # In ra để debug DB URI
    print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Khởi tạo db + migrate
    db.init_app(app)
    migrate.init_app(app, db)

# ✅ Gắn JWT vào app (sau khi app được tạo)
    jwt.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'

    # ✅ Cho phép cookie giữa frontend và backend
    # Khi sử dụng credentials, Access-Control-Allow-Origin không thể là '*'
    # flask-cors sẽ phản chiếu Origin nếu resources origins='*' và supports_credentials=True.
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    # Thêm header được chấp nhận
    app.config.setdefault('CORS_HEADERS', 'Content-Type')
    # Đăng ký blueprint
    from src.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from src.music.routes import music_bp
    app.register_blueprint(music_bp)

    from src.api.routes import api_bp
    app.register_blueprint(api_bp)

    from src.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Uploader blueprint
    from src.uploader.routes import uploader_bp
    app.register_blueprint(uploader_bp)

    # Playlist API blueprint
    from src.music.playlist_routes import playlist_bp
    app.register_blueprint(playlist_bp)

    # Listening history API
    from src.api.listening_history_routes import history_bp
    app.register_blueprint(history_bp)

    # Đăng ký BXH API cho JS
    from src.api.bxh_api import bxh_api
    app.register_blueprint(bxh_api)

    # Like & Comment interactions
    from src.music.interactions_routes import interactions_bp
    app.register_blueprint(interactions_bp)

    # Register admin users management blueprint
    app.register_blueprint(admin_users)

    # Song-Artist management blueprint
    from src.admin.song_artist_management import song_artist_bp
    app.register_blueprint(song_artist_bp)

    # JWT error handlers - redirect to login for web pages, return JSON for API
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        # Check if request is for a page (HTML) or API (JSON)
        if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
            return jsonify(msg="Missing Authorization Header"), 401
        # For web pages, redirect to login
        return redirect(url_for('auth.login_page'))
    
    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
            return jsonify(msg="Invalid token"), 401
        return redirect(url_for('auth.login_page'))
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
            return jsonify(msg="Token has expired"), 401
        return redirect(url_for('auth.login_page'))

    # Đảm bảo các model được import để Flask-Migrate nhận diện
    from src.models import user, music

    # Context processor: inject followed artists when a session token is available
    from src.jwt_helper import current_identity
    from flask_jwt_extended import verify_jwt_in_request
    @app.context_processor
    def inject_followed_artists():
        try:
            # Ensure JWT (cookie or header) is parsed so get_jwt_identity works even on routes without @jwt_required
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                # optional=True: ignore errors (invalid/missing token) and proceed with empty list
                pass
            identity = current_identity()
            if not identity or not identity.get('id'):
                # Luôn cung cấp biến (rỗng) để template phân biệt trạng thái đăng nhập vs chưa tải
                return {'server_followed_artists': []}
            # import here to avoid circular imports at module load time
            from src.models import User
            user = User.query.get(identity.get('id'))
            if not user:
                return {'server_followed_artists': []}
            artists = [{'id': a.id, 'name': a.name, 'image_path': a.image_path} for a in user.followed_artists.all()]
            return {'server_followed_artists': artists}
        except Exception:
            app.logger.exception('inject_followed_artists error')
            return {'server_followed_artists': []}
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)


