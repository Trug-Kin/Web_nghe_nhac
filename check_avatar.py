from src.models import User, db
from app import create_app

app = create_app()
app.app_context().push()

user = User.query.first()
if user:
    print(f'User: {user.username}')
    print(f'Email: {user.email}')
    print(f'Has avatar field: {hasattr(user, "avatar")}')
    if hasattr(user, 'avatar'):
        print(f'Avatar value: {user.avatar}')
else:
    print('No users found')
