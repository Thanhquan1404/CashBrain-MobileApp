from datetime import datetime, timedelta
from sqlalchemy import extract, func, and_
from app import db
from app.expense.models import Expense, ExpenseCategory
from app.income.models import Income
import numpy as np

class FinancialAnalysisLayer:
    def __init__(self, user_id, months=6):
        self.user_id = user_id
        self.months = months
        self.end_date = datetime.today()
        # Tính toán ngày bắt đầu dựa trên số tháng
        self.start_date = self.end_date - timedelta(days=30 * months)

    def compute(self):
        # 1) Lấy tổng thu nhập, chi tiêu (Không đổi)
        total_income = float(db.session.query(func.sum(Income.amount))
            .filter(Income.user_id == self.user_id)
            .filter(Income.date >= self.start_date)
            .scalar() or 0.0)

        total_expense = float(db.session.query(func.sum(Expense.amount))
            .filter(Expense.user_id == self.user_id)
            .filter(Expense.date >= self.start_date)
            .scalar() or 0.0)

        balance = total_income - total_expense
        saving_rate = (balance / total_income * 100) if total_income > 0 else 0.0

        # 2) Chi tiết theo category (Không đổi)
        category_stats = db.session.query(
            ExpenseCategory.label,
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count'),
            func.count(func.distinct(Expense.date)).label('active_days')
        ).join(Expense, Expense.category_id == ExpenseCategory.id)\
        .filter(
            Expense.user_id == self.user_id,
            Expense.date >= self.start_date
        ).group_by(ExpenseCategory.label).all()

        categories = {
            row.label: {
                'total': round(float(row.total), 2),
                'count': int(row.count),
                'active_days': int(row.active_days),
                'pct_of_total': round((float(row.total) / total_expense * 100), 1) if total_expense > 0 else 0.0,
                'avg_per_day': round(float(row.total) / (row.active_days if row.active_days > 0 else 1), 2)
            } for row in category_stats
        }

        # 3) Trung bình chi tiêu hàng tháng (Sử dụng func.year/month cho MySQL)
        monthly_expenses = db.session.query(
            func.year(Expense.date).label('year'),
            func.month(Expense.date).label('month'),
            func.sum(Expense.amount).label('total_amount'),
            func.count(func.distinct(Expense.date)).label('active_days')
        ).filter(
            Expense.user_id == self.user_id,
            Expense.date >= self.start_date
        ).group_by(func.year(Expense.date), func.month(Expense.date)).all()

        monthly_totals = [float(m.total_amount) for m in monthly_expenses]
        if monthly_totals:
            avg_monthly = np.mean(monthly_totals)
            std_monthly = np.std(monthly_totals)
        else:
            avg_monthly = std_monthly = 0.0

        # 4) Weekly breakdown (Thay đổi quan trọng cho MySQL)
        # MySQL DAYOFWEEK trả về: 1 (CN), 2 (T2), ..., 7 (T7)
        current_date = datetime.today()
        week_start = current_date - timedelta(days=current_date.weekday())
        
        weekly_expenses = db.session.query(
            func.dayofweek(Expense.date).label('day_of_week'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == self.user_id,
            Expense.date >= week_start,
            Expense.date <= self.end_date
        ).group_by(func.dayofweek(Expense.date)).all()

        # 5) Top 5 single transactions (Không đổi)
        top_transactions = db.session.query(
            Expense.amount,
            ExpenseCategory.label,
            Expense.date,
            Expense.note
        ).join(ExpenseCategory, Expense.category_id == ExpenseCategory.id)\
        .filter(
            Expense.user_id == self.user_id,
            Expense.date >= self.start_date
        ).order_by(Expense.amount.desc()).limit(5).all()

        return {
            'summary': {
                'total_income': round(total_income, 2),
                'total_expense': round(total_expense, 2),
                'balance': round(balance, 2),
                'saving_rate': round(saving_rate, 1),
                'avg_monthly_expense': round(avg_monthly, 2),
                'std_monthly_expense': round(std_monthly, 2)
            },
            'categories': categories,
            'monthly_breakdown': [
                {'year': m.year, 'month': m.month, 'total': float(m.total_amount)} 
                for m in monthly_expenses
            ],
            'weekly_breakdown': [
                {'day_of_week': w.day_of_week, 'total': float(w.total)} 
                for w in weekly_expenses
            ],
            'top_transactions': [
                {'amount': float(t.amount), 'category': t.label, 'date': t.date.isoformat(), 'note': t.note}
                for t in top_transactions
            ]
        }