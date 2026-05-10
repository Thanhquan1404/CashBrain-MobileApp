from app import db

class ExpenseCategoryGroup(db.Model):
    __bind_key__ = 'finance_db'
    __tablename__ = 'expense_category_groups'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    bg_color = db.Column(db.String(20), nullable=False)

    categories = db.relationship(
        'ExpenseCategory',
        backref='group',
        lazy=True,
        cascade='all, delete'
    )

class ExpenseCategory(db.Model):
    __bind_key__ = 'finance_db'
    __tablename__ = 'expense_category'

    id = db.Column(db.Integer, primary_key=True)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey('expense_category_groups.id'),
        nullable=False
    )

    label = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<ExpenseCategory {self.id}>'


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