# analysis_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
import calendar
from expense_service.expense_models import Expense, ExpenseCategory
from income_service.income_models import Income
from decimal import Decimal

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@analysis_bp.route('/monthly', methods=['GET'])
@jwt_required()
def get_monthly_analysis():
    user_id = get_jwt_identity()  # string
    today = datetime.today()
    year = today.year
    month = today.month

    # Dùng aggregation để tính tổng thu nhập trong tháng
    income_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {
                '$gte': datetime(year, month, 1),
                '$lt': datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            }
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    income_result = list(Income.objects.aggregate(*income_pipeline))
    total_income = income_result[0]['total'] if income_result else 0.0

    expense_pipeline = [
        {'$match': {
            'user_id': user_id,
            'date': {
                '$gte': datetime(year, month, 1),
                '$lt': datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            }
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    expense_result = list(Expense.objects.aggregate(*expense_pipeline))
    total_expense = expense_result[0]['total'] if expense_result else 0.0

    return jsonify({
        'message': 'Retrieve the monthly analysis data',
        'data': {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense,
            'month': today.strftime('%Y-%m')
        }
    })

@analysis_bp.route('/weekly', methods=['GET'])
@jwt_required()
def get_weekly_analysis():
    user_id = get_jwt_identity()
    today = datetime.today()
    current_weekday = today.weekday()  # 0=Monday
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    start_of_week = today - timedelta(days=current_weekday)
    end_of_week = start_of_week + timedelta(days=6)

    # Lấy tất cả expenses trong tuần (dùng filter date range)
    expenses_in_week = Expense.objects(
        user_id=user_id,
        date__gte=start_of_week.date(),
        date__lte=end_of_week.date()
    )
    # Nhóm theo ngày bằng Python (vì số lượng không lớn)
    daily_expense = {}
    for exp in expenses_in_week:
        day = exp.date.weekday()  # 0=Monday
        daily_expense[day] = daily_expense.get(day, 0) + exp.amount

    result = []
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = weekdays[i]
        daily_total = daily_expense.get(i, 0.0)
        result.append({
            'day': day_name,
            'amount': round(daily_total, 0),
            'active': i == current_weekday
        })

    return jsonify({
        'message': 'Retrieve the weekly analysis data',
        'data': result,
        'week': f"{start_of_week.strftime('%d/%m')} - {end_of_week.strftime('%d/%m/%Y')}"
    })

@analysis_bp.route('/calendar-month', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    date_param = request.args.get('date')
    
    try:
        if date_param:
            dt = datetime.fromisoformat(date_param.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
        target_month = dt.month
        target_year = dt.year
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO 8601"}), 400

    start_date = datetime(target_year, target_month, 1)
    if target_month == 12:
        end_date = datetime(target_year + 1, 1, 1)
    else:
        end_date = datetime(target_year, target_month + 1, 1)

    incomes = Income.objects(
        user_id=user_id,
        date__gte=start_date,
        date__lt=end_date
    )
    
    expenses = Expense.objects(
        user_id=user_id,
        date__gte=start_date,
        date__lt=end_date
    )

    # Pre-fetch categories
    cat_ids = list(set(str(exp.category_id) for exp in expenses if exp.category_id))
    categories = {str(cat.id): cat for cat in ExpenseCategory.objects(id__in=cat_ids)}

    formatted_data = []
    total_expense = Decimal('0')
    total_income = Decimal('0')

    # Process Incomes
    for inc in incomes:
        amount = Decimal(inc.amount) if inc.amount is not None else Decimal('0')
        total_income += amount

        formatted_data.append({
            "id": f"inc_{inc.id}",
            "day": inc.date.day,
            "title": inc.note if inc.note else "Income",
            "time": inc.created_at.strftime("%I:%M %p") if inc.created_at else "08:00 AM",
            "amount": float(amount),        # Frontend usually prefers number
            "category": "Income"
        })

    # Process Expenses
    for exp in expenses:
        amount = Decimal(exp.amount) if exp.amount is not None else Decimal('0')
        total_expense += amount

        cat = categories.get(str(exp.category_id))
        cat_label = cat.label if cat else "Unknown"

        formatted_data.append({
            "id": f"exp_{exp.id}",
            "day": exp.date.day,
            "title": exp.note if exp.note else cat_label,
            "time": exp.created_at.strftime("%I:%M %p") if exp.created_at else "09:30 AM",
            "amount": float(-amount),       # negative for expense
            "category": cat_label
        })

    formatted_data.sort(key=lambda x: x['day'])

    return jsonify({
        "status": "success",
        "month": target_month,
        "year": target_year,
        "net_value": float(total_income - total_expense),
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "transactions": formatted_data
    })


@analysis_bp.route('/overview-transactions', methods=['GET'])
@jwt_required()
def get_overview_transactions():
    user_id = get_jwt_identity()
    incomes = Income.objects(user_id=user_id)
    expenses = Expense.objects(user_id=user_id)

    results = []
    for inc in incomes:
        results.append({
            "date": [inc.date.year, inc.date.month, inc.date.day],
            "amount": str(float(inc.amount))
        })
    for exp in expenses:
        print(exp.id)
        results.append({
            "date": [exp.date.year, exp.date.month, exp.date.day],
            "amount": str(-float(exp.amount))
        })

    results.sort(key=lambda x: (x['date'][0], x['date'][1], x['date'][2]))
    return jsonify({
        'message': 'Successfully get overview transactions',
        'data': results
    })