from app import db

class IncomeCategory(db.Model):
    __bind_key__ = 'finance_db'          # chỉ định bind
    __tablename__ = 'income_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    incomes = db.relationship('Income', backref='category', lazy=True)

    def __repr__(self):
        return f'<IncomeCategory {self.name}>'


class Income(db.Model):
    __bind_key__ = 'finance_db'
    __tablename__ = 'income'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)   # lấy từ JWT
    category_id = db.Column(db.Integer, db.ForeignKey('income_category.id'), nullable=False)
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