# income_models.py
from mongoengine import Document, fields
from datetime import datetime

class IncomeCategory(Document):
    meta = {'collection': 'income_categories'}
    name = fields.StringField(required=True, max_length=100)
    description = fields.StringField()

    def __repr__(self):
        return f'<IncomeCategory {self.name}>'


class Income(Document):
    meta = {'collection': 'incomes'}
    user_id = fields.StringField(required=True)   # lưu trực tiếp user_id từ JWT (string)
    amount = fields.FloatField(required=True)     # hoặc DecimalField nếu cần độ chính xác cao
    date = fields.DateField(required=True)
    note = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'type': 'Income',
            'amount': self.amount,
            'date': self.date.isoformat(),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }