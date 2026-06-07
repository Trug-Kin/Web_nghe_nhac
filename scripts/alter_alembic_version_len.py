import importlib.util, pathlib, sys

# Ensure project root is on sys.path
ROOT = pathlib.Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.extensions import db

# Dynamically load root-level app.py (to avoid package name clash with /app dir)
root_app_path = pathlib.Path(__file__).parent.parent / "app.py"
spec = importlib.util.spec_from_file_location("root_app_module", str(root_app_path))
root_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_module)
create_app = root_module.create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    engine = db.engine
    with engine.connect() as conn:
        print('Altering alembic_version.version_num length to 255...')
        conn.execute(text('ALTER TABLE alembic_version MODIFY version_num VARCHAR(255) NOT NULL'))
        print('Done.')
