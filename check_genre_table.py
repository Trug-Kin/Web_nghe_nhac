from app import create_app
from src.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    result = db.session.execute(text("DESCRIBE genres"))
    print("Cấu trúc bảng genres:")
    for row in result:
        print(row)
