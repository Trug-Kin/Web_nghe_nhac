from app import create_app
from sqlalchemy import inspect, text
from src.extensions import db

app = create_app()
with app.app_context():
    engine = db.engine
    insp = inspect(engine)
    cols = insp.get_columns('alembic_version')
    print('alembic_version columns:')
    for c in cols:
        print(f" - {c['name']} {c.get('type')} nullable={c.get('nullable')}")
    # Print current value
    try:
        with engine.connect() as conn:
            val = conn.execute(text('SELECT version_num FROM alembic_version')).fetchone()
            print('Current version_num row:', val)
    except Exception as e:
        print('Error reading version_num:', e)
