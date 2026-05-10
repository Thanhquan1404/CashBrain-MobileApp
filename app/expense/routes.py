from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.expense.models import ExpenseCategory, Expense, ExpenseCategoryGroup
from datetime import datetime

expense_bp = Blueprint('expense', __name__, url_prefix='/api/expense')

# ────────────────────── CATEGORY CRUD ──────────────────────
@expense_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_expense_categories():

    groups = ExpenseCategoryGroup.query.all()

    result = []

    for group in groups:

        categories = ExpenseCategory.query.filter_by(
            group_id=group.id
        ).all()

        result.append({
            'id': group.id,
            'title': group.title,
            'color': group.color,
            'bgColor': group.bg_color,

            'categories': [
                {
                    'id': category.id,
                    'label': category.label,
                    'icon': category.icon,
                    'color': category.color
                }
                for category in categories
            ]
        })

    return jsonify({
        'message': 'Successfully fetching expense categories',
        'data': result
    }), 200

# ────────────────────── EXPENSE CRUD ──────────────────────
@expense_bp.route('/', methods=['GET'])
@jwt_required()
def get_expenses():
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    return jsonify([exp.to_dict() for exp in expenses]), 200

@expense_bp.route('/', methods=['POST'])
@jwt_required()
def create_expense():
    user_id = get_jwt_identity()
    data = request.get_json()
    category_id = data.get('category_id')
    amount = data.get('amount')
    date_str = data.get('date')

    if not category_id or not amount or not date_str:
        return jsonify({'msg': 'Thiếu category_id, amount hoặc date'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'msg': 'Sai định dạng ngày (YYYY-MM-DD)'}), 400

    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        date=date,
        note=data.get('note', '')
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({'msg': 'Thêm chi tiêu thành công', 'id': expense.id}), 201

@expense_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_expense(id):
    user_id = int(get_jwt_identity())
    # Retrieve expense base on expense id
    expense = Expense.query.get_or_404(id)
    if expense.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền sửa bản ghi này'}), 403

    data = request.get_json()
    expense.category_id = data.get('category_id', expense.category_id)
    expense.amount = data.get('amount', expense.amount)
    if 'date' in data:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'msg': 'Sai định dạng ngày'}), 400
    expense.note = data.get('note', expense.note)
    db.session.commit()
    return jsonify({
        'msg': 'Cập nhật chi tiêu thành công',
        'data': {
            'amount': expense.amount,
            'category_id': expense.category,
            'category_name': expense.name,
            'date': expense.date,
            'note': expense.note,
        }
    }), 200

@expense_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_expense(id):
    user_id = int(get_jwt_identity())
    expense = Expense.query.get_or_404(id)
    if expense.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền xóa bản ghi này'}), 403
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'msg': 'Xóa chi tiêu thành công'}), 200