"""Legacy package shim for projects that import `app` as a package.

This project also has a top-level module `app.py` that defines the real
`create_app()` factory. In order to avoid the common Python import
collision where `import app` picks up this package instead of the top-level
module, we delegate `create_app` to the top-level module here.

Files that previously did `from app import create_app` will continue to work.
"""

from importlib import util
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

# Keep a small compatibility shim: expose db object if code imports it from
# this package (legacy behavior). The real app uses `src.models.db` so this
# is just for any code under the legacy `app/` folder.
db = SQLAlchemy()

# Cache loaded top-level module
_top_app_module = None

def _load_top_level_app():
    global _top_app_module
    if _top_app_module is not None:
        return _top_app_module

    # Locate the top-level app.py (one directory above this package)
    pkg_dir = Path(__file__).resolve().parent
    top_app_path = pkg_dir.parent / 'app.py'
    if not top_app_path.exists():
        raise ImportError(f"Top-level app.py not found at {top_app_path}")

    spec = util.spec_from_file_location('top_level_app', str(top_app_path))
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _top_app_module = module
    return module


def create_app(*args, **kwargs):
    """Delegate to the top-level app.py create_app factory loaded by path.

    This avoids importing the `app` package and prevents recursive imports.
    """
    top = _load_top_level_app()
    return top.create_app(*args, **kwargs)

# For compatibility, attempt to expose the legacy playlist blueprint loader
# if code inside the old package expects it (not necessary but harmless).
try:
    from .routes.playlist_routes import playlist_bp  # type: ignore
except Exception:
    # ignore; this package is now just a shim
    playlist_bp = None