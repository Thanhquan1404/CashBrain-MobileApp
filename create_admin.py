# create_admin.py
from mongoengine import connect
from auth_service.user_model import User
from auth_service.auth_utils import hash_password
import os
from dotenv import load_dotenv

load_dotenv()
connect(host=os.getenv('MONGO_URI'))

if not User.objects(username='admin').first():
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=hash_password('admin123'),
        role='admin'
    )
    admin.save()
    print("Admin created: username=admin, password=admin123")
else:
    print("Admin already exists")