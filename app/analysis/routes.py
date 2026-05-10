from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.expense.models import Expense
from app.income.models import Income
from datetime import datetime, timedelta
from sqlalchemy import extract, func, case

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')


@analysis_bp.route('/monthly', methods=['GET'])
@jwt_required()
def get_monthly_analysis():
    user_id = int(get_jwt_identity())
    today = datetime.today()
    
    # Lọc theo năm và tháng hiện tại
    total_income = db.session.query(func.sum(Income.amount))\
        .filter(Income.user_id == user_id)\
        .filter(extract('year', Income.date) == today.year)\
        .filter(extract('month', Income.date) == today.month)\
        .scalar() or 0

    total_expense = db.session.query(func.sum(Expense.amount))\
        .filter(Expense.user_id == user_id)\
        .filter(extract('year', Expense.date) == today.year)\
        .filter(extract('month', Expense.date) == today.month)\
        .scalar() or 0

    return jsonify({
        'msg': 'Retrieve the monthly analysis data',
        'data': {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(total_income - total_expense),
            'month': today.strftime('%Y-%m')
        }
    })

@analysis_bp.route('/weekly', methods=['GET'])
@jwt_required()
def get_weekly_analysis():
    user_id = int(get_jwt_identity())
    today = datetime.today()
    current_weekday = today.weekday()  # 0= Monday ... 6=Sunday

    # Tạo danh sách 7 ngày trong tuần (bắt đầu từ Monday)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Tính ngày bắt đầu của tuần (Monday)
    start_of_week = today - timedelta(days=current_weekday)
    
    result = []
    
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = weekdays[i]
        
        # Tính tổng chi tiêu + thu nhập trong ngày đó
        daily_income = db.session.query(func.sum(Income.amount))\
            .filter(Income.user_id == user_id)\
            .filter(Income.date == day_date.date())\
            .scalar() or 0

        daily_expense = db.session.query(func.sum(Expense.amount))\
            .filter(Expense.user_id == user_id)\
            .filter(Expense.date == day_date.date())\
            .scalar() or 0

        daily_total = float(daily_expense)  # Có thể điều chỉnh logic theo nhu cầu

        result.append({
            'day': day_name,
            'amount': round(daily_total, 0),   # hoặc abs nếu chỉ muốn xem chi tiêu
            'active': i == current_weekday
        })

    return jsonify({
        'msg': 'Retrieve the weekly analysis data',
        'data': result,
        'week': f"{start_of_week.strftime('%d/%m')} - {(start_of_week + timedelta(days=6)).strftime('%d/%m/%Y')}"
    })