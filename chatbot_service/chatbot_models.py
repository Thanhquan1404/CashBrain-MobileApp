# chatbot/models.py
from mongoengine import Document, StringField, DateTimeField, DictField
from datetime import datetime

class ChatHistory(Document):
    user_id = StringField(required=True)   # ← đã sửa thành StringField
    role = StringField(required=True, max_length=10, choices=('user', 'assistant'))
    content = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)
    financial_snapshot = DictField()

    meta = {
        'collection': 'chat_history',
        'indexes': ['user_id', ('user_id', '-timestamp')]
    }