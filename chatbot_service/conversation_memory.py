# chatbot/conversation_memory.py
from .chatbot_models import ChatHistory
from datetime import datetime

class ConversationMemory:
    MAX_TURNS = 20

    def __init__(self, user_id: str):          # ← user_id là string
        self.user_id = user_id

    def load_history(self, limit: int = None):
        if limit is None:
            limit = self.MAX_TURNS
        qs = ChatHistory.objects(user_id=self.user_id).order_by('timestamp')
        history = list(qs.limit(limit))
        return [{'role': msg.role, 'content': msg.content} for msg in history]

    def add_message(self, role: str, content: str, snapshot: dict = None):
        msg = ChatHistory(
            user_id=self.user_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            financial_snapshot=snapshot or {}
        )
        msg.save()
        total = ChatHistory.objects(user_id=self.user_id).count()
        if total > self.MAX_TURNS:
            oldest = ChatHistory.objects(user_id=self.user_id).order_by('timestamp').first()
            if oldest:
                oldest.delete()

    def clear_history(self):
        ChatHistory.objects(user_id=self.user_id).delete()