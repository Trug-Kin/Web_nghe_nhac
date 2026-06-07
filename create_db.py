from app import create_app, db

app = create_app()
app.config.from_object(config)
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
