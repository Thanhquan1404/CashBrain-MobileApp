# chatbot/models.py
from app import db
from datetime import datetime

class ChatHistory(db.Model):
    __bind_key__ = 'chatbot_db'
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # (Optional) Lưu snapshot của financial analysis lúc đó để dùng sau
    financial_snapshot = db.Column(db.JSON)