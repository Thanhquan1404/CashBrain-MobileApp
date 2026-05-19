# chatbot_service/financial_analysis.py
from datetime import datetime, timedelta
from mongoengine import *
from expense_service.expense_models import Expense, ExpenseCategory
from income_service.income_models import Income
import numpy as np

class FinancialAnalysisLayer:
    def __init__(self, user_id, months=6):
        self.user_id = user_id
        self.months = months
        self.end_date = datetime.today()
        self.start_date = self.end_date - timedelta(days=30 * months)

    def compute(self):
        # 1) Tổng thu nhập và chi tiêu
        total_income = Income.objects(
            user_id=self.user_id,
            date__gte=self.start_date
        ).sum('amount') or 0.0

        total_expense = Expense.objects(
            user_id=self.user_id,
            date__gte=self.start_date
        ).sum('amount') or 0.0

        balance = total_income - total_expense
        saving_rate = (balance / total_income * 100) if total_income > 0 else 0.0

        # 2) Chi tiêu theo category (dùng aggregation pipeline)
        category_pipeline = [
            {'$match': {'user_id': self.user_id, 'date': {'$gte': self.start_date}}},
            {'$lookup': {
                'from': ExpenseCategory._get_collection_name(),
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category'
            }},
            {'$unwind': '$category'},
            {'$group': {
                '_id': '$category.label',
                'total': {'$sum': '$amount'},
                'count': {'$sum': 1},
                'active_days': {'$addToSet': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$date'}}}
            }},
            {'$project': {
                'label': '$_id',
                'total': 1,
                'count': 1,
                'active_days': {'$size': '$active_days'}
            }}
        ]
        category_stats = list(Expense.objects.aggregate(*category_pipeline))

        categories = {}
        for row in category_stats:
            total = float(row['total'])
            active_days = row['active_days']
            pct = (total / total_expense * 100) if total_expense > 0 else 0.0
            categories[row['label']] = {
                'total': round(total, 2),
                'count': row['count'],
                'active_days': active_days,
                'pct_of_total': round(pct, 1),
                'avg_per_day': round(total / active_days if active_days > 0 else total, 2)
            }

        # 3) Chi tiêu trung bình hàng tháng (group by year+month)
        monthly_pipeline = [
            {'$match': {'user_id': self.user_id, 'date': {'$gte': self.start_date}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$date'},
                    'month': {'$month': '$date'}
                },
                'total_amount': {'$sum': '$amount'},
                'active_days': {'$addToSet': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$date'}}}
            }},
            {'$project': {
                'year': '$_id.year',
                'month': '$_id.month',
                'total_amount': 1,
                'active_days': {'$size': '$active_days'}
            }},
            {'$sort': {'year': 1, 'month': 1}}
        ]
        monthly_expenses = list(Expense.objects.aggregate(*monthly_pipeline))

        monthly_totals = [float(m['total_amount']) for m in monthly_expenses]
        if monthly_totals:
            avg_monthly = np.mean(monthly_totals)
            std_monthly = np.std(monthly_totals)
        else:
            avg_monthly = std_monthly = 0.0

        # 4) Weekly breakdown (từ đầu tuần đến hôm nay)
        current_date = datetime.today()
        week_start = current_date - timedelta(days=current_date.weekday())
        weekly_pipeline = [
            {'$match': {
                'user_id': self.user_id,
                'date': {'$gte': week_start, '$lte': self.end_date}
            }},
            {'$group': {
                '_id': {'$dayOfWeek': '$date'},  # 1=Chủ nhật, 2=Thứ 2, ..., 7=Thứ 7
                'total': {'$sum': '$amount'}
            }},
            {'$project': {
                'day_of_week': '$_id',
                'total': 1
            }},
            {'$sort': {'day_of_week': 1}}
        ]
        weekly_expenses = list(Expense.objects.aggregate(*weekly_pipeline))

        # 5) Top 5 giao dịch lớn nhất
        top_transactions = Expense.objects(
            user_id=self.user_id,
            date__gte=self.start_date
        ).order_by('-amount').limit(5)

        top_list = []
        for txn in top_transactions:
            category = ExpenseCategory.objects(id=txn.category_id).first() if txn.category_id else None
            category_label = category.label if category else 'Unknown'
            top_list.append({
                'amount': float(txn.amount),
                'category': category_label,
                'date': txn.date.isoformat(),
                'note': txn.note or ''
            })

        # Tính daily_avg_expense (tổng chi / số ngày trong kỳ)
        days_range = (self.end_date - self.start_date).days + 1
        daily_avg_expense = total_expense / days_range if days_range > 0 else 0.0

        return {
            'summary': {
                'total_income': round(total_income, 2),
                'total_expense': round(total_expense, 2),
                'balance': round(balance, 2),
                'saving_rate': round(saving_rate, 1),
                'avg_monthly_expense': round(avg_monthly, 2),
                'std_monthly_expense': round(std_monthly, 2),
                'daily_avg_expense': round(daily_avg_expense, 2)
            },
            'categories': categories,
            'monthly_breakdown': [
                {'year': m['year'], 'month': m['month'], 'total': float(m['total_amount'])}
                for m in monthly_expenses
            ],
            'weekly_breakdown': [
                {'day_of_week': w['day_of_week'], 'total': float(w['total'])}
                for w in weekly_expenses
            ],
            'top_transactions': top_list,
            'period_months': self.months   # thêm để prompt engine dùng
        }