# chatbot/conversation_memory.py
from app import db
from .models import ChatHistory

class ConversationMemory:
    MAX_TURNS = 10  # số cặp (user+assistant) gần nhất giữ lại

    def __init__(self, user_id):
        self.user_id = user_id

    def load_history(self):
        """Lấy lịch sử hội thoại gần nhất (sliding window)"""
        messages = ChatHistory.query.filter_by(user_id=self.user_id)\
                        .order_by(ChatHistory.timestamp.asc())\
                        .all()
        # Cắt chỉ giữ MAX_TURNS * 2 dòng cuối
        trimmed = messages[-(self.MAX_TURNS * 2):]
        return [{'role': m.role, 'content': m.content} for m in trimmed]

    def add_message(self, role, content, snapshot=None):
        """Lưu một tin nhắn mới"""
        msg = ChatHistory(
            user_id=self.user_id,
            role=role,
            content=content,
            financial_snapshot=snapshot
        )
        db.session.add(msg)
        db.session.commit()

    def clear_history(self):
        """Xóa toàn bộ lịch sử (nếu người dùng muốn reset)"""
        ChatHistory.query.filter_by(user_id=self.user_id).delete()
        db.session.commit()