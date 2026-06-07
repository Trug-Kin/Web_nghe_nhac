import alembic.config, alembic.command
import importlib.util, pathlib

# Dynamically load root-level app.py (name clashes with package directory 'app/')
root_app_path = pathlib.Path(__file__).parent / "app.py"
spec = importlib.util.spec_from_file_location("root_app_module", str(root_app_path))
root_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_module)

app = root_module.create_app()  # factory to build Flask app
# db is imported inside app.py via src.extensions; ensure it's available
from src.extensions import db  # type: ignore

with app.app_context():
	cfg = alembic.config.Config("migrations/alembic.ini")
	print("Running alembic upgrade head (after merge)...")
	alembic.command.upgrade(cfg, "head")
	print("Alembic upgrade complete")
