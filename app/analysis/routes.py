from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.expense.models import Expense
from app.income.models import Income
from datetime import datetime, timedelta
from sqlalchemy import extract, func, case
import calendar
from calendar import monthrange
from flask import Blueprint, request, jsonify

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

@analysis_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_analysis():
    user_id = int(get_jwt_identity())
    
    # Lấy tháng/năm từ query params, mặc định là tháng hiện tại
    try:
        year = int(request.args.get('year', datetime.today().year))
        month = int(request.args.get('month', datetime.today().month))
    except ValueError:
        return jsonify({'msg': 'Invalid month or year format'}), 400

    # 1. Xác định số ngày trong tháng
    # monthrange trả về (ngày đầu tuần, số ngày trong tháng)
    _, days_in_month = calendar.monthrange(year, month)
    
    # 2. Truy vấn gộp toàn bộ dữ liệu trong tháng (Batch Query)
    # Lấy tổng thu nhập theo từng ngày
    incomes = db.session.query(
        func.extract('day', Income.date).label('day'),
        func.sum(Income.amount).label('total')
    ).filter(
        Income.user_id == user_id,
        extract('year', Income.date) == year,
        extract('month', Income.date) == month
    ).group_by('day').all()

    # Lấy tổng chi tiêu theo từng ngày
    expenses = db.session.query(
        func.extract('day', Expense.date).label('day'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).group_by('day').all()

    # 3. Chuyển kết quả truy vấn vào dictionary để truy xuất nhanh
    income_map = {int(i.day): float(i.total) for i in incomes}
    expense_map = {int(e.day): float(e.total) for e in expenses}

    # 4. Xây dựng mảng dữ liệu cho FE
    calendar_days = []
    for day in range(1, days_in_month + 1):
        day_income = income_map.get(day, 0)
        day_expense = expense_map.get(day, 0)
        balance = day_income - day_expense
        
        day_data = {'day': day}
        
        # Chỉ thêm badge nếu có phát sinh giao dịch (balance khác 0)
        if balance != 0:
            prefix = '+' if balance > 0 else '-'
            # Format số: 400000 -> 400K, 45000 -> 45K
            abs_balance = abs(balance)
            if abs_balance >= 1000:
                badge_value = f"{prefix}{int(abs_balance/1000)}K"
            else:
                badge_value = f"{prefix}{int(abs_balance)}"
            
            day_data['badge'] = badge_value
            day_data['balance'] = balance # Gửi thêm số nguyên để FE dễ xử lý logic màu sắc nếu cần

        calendar_days.append(day_data)

    return jsonify({
        'msg': f'Retrieve analysis for {year}-{month:02d}',
        'data': {
            'month': f"{year}-{month:02d}",
            'calendar_days': calendar_days
        }
    })

@analysis_bp.route('/calendar-month', methods=['GET'])
@jwt_required()
def get_transactions():
    # 1. Lấy token từ header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = int(get_jwt_identity())

    # 2. Lấy tham số tháng/năm (Optional - giúp hiệu năng tốt hơn)
    date_param = request.args.get('date')
    try:
        if date_param:
            # Xử lý chuỗi ISO. Replace 'Z' bằng '+00:00' để datetime.fromisoformat hiểu được trên các bản python cũ
            dt = datetime.fromisoformat(date_param.replace('Z', '+00:00'))
        else:
            dt = datetime.now()
        
        target_month = dt.month
        target_year = dt.year
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO 8601"}), 400

    # 3. Truy vấn dữ liệu từ cả 2 bảng
    # Lọc theo user_id và (tùy chọn) theo tháng/năm
    incomes = Income.query.filter(
        Income.user_id == user_id,
        extract('month', Income.date) == target_month,
        extract('year', Income.date) == target_year
    ).all()

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == target_month,
        extract('year', Expense.date) == target_year
    ).all()

    formatted_data = []
    total_income = 0
    total_expense = 0

    # 4. Format dữ liệu từ bảng Income
    for inc in incomes:
        amount = float(inc.amount)
        total_income += amount
        formatted_data.append({
            "id": f"inc_{inc.id}",
            "day": inc.date.day,
            "title": inc.note if inc.note else "Income",
            "time": inc.created_at.strftime("%I:%M %p") if inc.created_at else "08:00 AM",
            "amount": amount,
            "category": "Income"
        })

    # 5. Format Expense & Tính tổng chi
    for exp in expenses:
        amount = float(exp.amount)
        total_expense += amount
        formatted_data.append({
            "id": f"exp_{exp.id}",
            "day": exp.date.day,
            "title": exp.note if exp.note else exp.category.label,
            "time": exp.created_at.strftime("%I:%M %p") if exp.created_at else "09:30 AM",
            "amount": -amount, # FE nhận số âm cho chi tiêu
            "category": exp.category.label
        })

    # 6. Sắp xếp dữ liệu theo ngày
    formatted_data.sort(key=lambda x: x['day'])

    return jsonify({
        "status": "success",
        "month": target_month,
        "year": target_year,
        "net_value": total_income - total_expense, # Tổng thu - Tổng chi
        "total_income": total_income,
        "total_expense": total_expense,
        "transactions": formatted_data
    })

@analysis_bp.route('/overview-transactions', methods=['GET'])
@jwt_required()
def get_overview_transactions():
    user_id = int(get_jwt_identity())
    
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()
    
    results = []
    
    for inc in incomes:
        year = inc.date.year
        month = inc.date.month - 1      # JavaScript month là 0-based
        day = inc.date.day
        
        results.append({
            "date": [year, month, day],   # Dạng new Date(2026, 3, 14)
            "amount": float(inc.amount)
        })
    
    for exp in expenses:
        year = exp.date.year
        month = exp.date.month - 1
        day = exp.date.day
        
        results.append({
            "date": [year, month, day],
            "amount": -float(exp.amount)
        })
    
    # Sắp xếp theo ngày
    results.sort(key=lambda x: x['date'])
    
    return jsonify({
        'msg': 'Successfully get overview transactions',
        'data': results
    })