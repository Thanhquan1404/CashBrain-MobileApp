from app import db

class ExpenseCategory(db.Model):
    __bind_key__ = 'finance_db'
    __tablename__ = 'expense_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'


class Expense(db.Model):
    __bind_key__ = 'finance_db'
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'amount': float(self.amount),
            'date': self.date.isoformat(),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }