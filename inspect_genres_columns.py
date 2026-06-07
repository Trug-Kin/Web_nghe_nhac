from sqlalchemy import inspect
import importlib.util, pathlib

# Load root-level app.py dynamically to access create_app factory
root_app_path = pathlib.Path(__file__).parent / "app.py"
spec = importlib.util.spec_from_file_location("root_app_module", str(root_app_path))
root_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_module)

app = root_module.create_app()
from src.extensions import db  # ensure db instance is bound after init_app

with app.app_context():
    inspector = inspect(db.engine)
    cols = inspector.get_columns("genres")
    print("genres columns:")
    for c in cols:
        print(f" - {c['name']} ({c.get('type')})")
