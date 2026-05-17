# models.py
from mongoengine import Document, fields
from datetime import datetime

class User(Document):
    meta = {'collection': 'users'}
    username = fields.StringField(required=True, unique=True, max_length=80)
    email = fields.StringField(required=True, unique=True, max_length=120)
    password_hash = fields.StringField(required=True, max_length=255)
    role = fields.StringField(default='user')  # 'user' hoặc 'admin'
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        # Tự động cập nhật updated_at khi lưu
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def __repr__(self):
        return f'<User {self.username}>'