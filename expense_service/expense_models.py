# expense_models.py
from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

# expense_models.py (bổ sung)
class ExpenseImage(Document):
    meta = {'collection': 'expense_images'}
    expense_id = fields.ObjectIdField(required=True, unique=True)  # 1-1 với expense
    image_url = fields.StringField(required=True)   # URL trên Cloudinary
    public_id = fields.StringField(required=True)   # dùng để xoá khỏi Cloudinary
    created_at = fields.DateTimeField(default=datetime.utcnow)

class ExpenseCategoryGroup(Document):
    meta = {'collection': 'expense_category_groups'}
    title = fields.StringField(required=True, max_length=100)
    color = fields.StringField(required=True, max_length=20)
    bg_color = fields.StringField(required=True, max_length=20)

class ExpenseCategory(Document):
    meta = {'collection': 'expense_categories'}
    group_id = fields.ObjectIdField(required=True)
    label = fields.StringField(required=True, max_length=100)
    icon = fields.StringField(required=True, max_length=100)
    color = fields.StringField(required=True, max_length=20)

class Expense(Document):
    meta = {'collection': 'expenses'}
    user_id = fields.StringField(required=True)  # giữ int vì từ JWT
    category_id = fields.ObjectIdField(required=True)
    amount = fields.DecimalField(required=True, precision=2)
    date = fields.DateField(required=True)
    note = fields.StringField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        # Lấy thông tin category và group (cần query riêng)
        category = ExpenseCategory.objects(id=self.category_id).first()
        group = None
        if category:
            group = ExpenseCategoryGroup.objects(id=category.group_id).first()
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'category_id': str(self.category_id),
            'category_name': category.label if category else None,
            'category_icon': category.icon if category else None,
            'category_color': category.color if category else None,
            'category_bg_color': group.bg_color if group else None,
            'type': 'Expense',
            'amount': float(self.amount),
            'date': self.date.isoformat(),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }