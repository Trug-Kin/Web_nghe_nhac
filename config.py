# Rising Score weight configuration
RISING_SCORE_WEIGHTS = {
    'growth_rate': 0.4,
    'followers_new': 0.25,
    'playlist_adds': 0.20,
    'search_hits': 0.10,
    'social_mentions': 0.05
}

# Clamp for growth rate to avoid outliers (e.g., newly added songs causing 1000% spikes)
RISING_GROWTH_RATE_MAX = 5.0  # 500%

# Trending cache TTL seconds (optional optimization)
TRENDING_CACHE_TTL = 1800  # 30 minutes
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "my_secret_key"
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL")
        or "mysql+pymysql://root:Kin0919136592@localhost:3306/Flask_Web"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==============================
    # ⚙️  JWT CONFIG (dùng cookie)
    # ==============================
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "super-secret-key"

    # ✅ Cho phép token nằm trong cookie và/hoặc header Authorization
    # This lets clients use cookie-based auth (browser) or header-based (SPA fallback)
    JWT_TOKEN_LOCATION = ["cookies", "headers"]

    # ✅ Tên cookie lưu token
    JWT_ACCESS_COOKIE_NAME = "access_token"

    # ✅ Cookie tồn tại tới khi đăng xuất
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # Change from False to 7 days
    # ✅ Cho phép frontend (JS) gửi cookie cross-origin
    JWT_COOKIE_SECURE = False  # Đặt True nếu dùng HTTPS
    # In local dev (HTTP) browsers block SameSite=None without Secure; switch to Lax
    JWT_COOKIE_SAMESITE = "Lax"
    
    # CRITICAL: Allow JS to read the cookie (set to False to disable HttpOnly)
    JWT_COOKIE_HTTPONLY = False
    JWT_SESSION_COOKIE = False  # Don't use session cookie
    
    # Access cookie configuration
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_COOKIE_DOMAIN = None  # Allow all domains

    # ⚠️ Tạm tắt CSRF trong giai đoạn dev, có thể bật lại khi deploy
    JWT_COOKIE_CSRF_PROTECT = False
