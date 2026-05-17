# expense_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from expense_service.expense_models import ExpenseCategoryGroup, ExpenseCategory, Expense

expense_bp = Blueprint('expense', __name__, url_prefix='/api/expense')

# ────────────────────── CATEGORY CRUD ──────────────────────
@expense_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_expense_categories():
    groups = ExpenseCategoryGroup.objects()
    result = []
    for group in groups:
        categories = ExpenseCategory.objects(group_id=group.id)
        result.append({
            'id': str(group.id),
            'title': group.title,
            'color': group.color,
            'bgColor': group.bg_color,
            'categories': [
                {
                    'id': str(cat.id),
                    'label': cat.label,
                    'icon': cat.icon,
                    'color': cat.color
                }
                for cat in categories
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
    user_id = str(get_jwt_identity())
    expenses = Expense.objects(user_id=user_id).order_by('-date')
    return jsonify({
        'message': 'Successfully retrieve user\'s expense data',
        'data': [exp.to_dict() for exp in expenses]
        
    }), 200

@expense_bp.route('/', methods=['POST'])
@jwt_required()
def create_expense():
    user_id = str(get_jwt_identity())
    data = request.get_json()
    category_id = data.get('category_id')
    amount = data.get('amount')
    date_str = data.get('date')

    if not category_id or not amount or not date_str:
        return jsonify({'message': 'Fill in category_id, amount or date'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Sai định dạng ngày (YYYY-MM-DD)'}), 400

    # Kiểm tra category có tồn tại không (tuỳ chọn)
    if not ExpenseCategory.objects(id=ObjectId(category_id)).first():
        return jsonify({'message': 'category_id không hợp lệ'}), 400

    expense = Expense(
        user_id=user_id,
        category_id=ObjectId(category_id),
        amount=float(amount),
        date=date,
        note=data.get('note', '')
    )
    expense.save()
    return jsonify({
        'message': 'Successfully posting a new user expense',
        'data': expense.to_dict()
    }), 201

@expense_bp.route('/<string:id>', methods=['PUT'])
@jwt_required()
def update_expense(id):
    user_id = str(get_jwt_identity())
    try:
        expense = Expense.objects.get(id=ObjectId(id))
    except Expense.DoesNotExist:
        return jsonify({'message': 'Expense không tồn tại'}), 404

    if expense.user_id != user_id:
        return jsonify({'message': 'Bạn không có quyền sửa bản ghi này'}), 403

    data = request.get_json()
    if 'category_id' in data:
        expense.category_id = ObjectId(data['category_id'])
    if 'amount' in data:
        expense.amount = float(data['amount'])
    if 'date' in data:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Sai định dạng ngày'}), 400
    if 'note' in data:
        expense.note = data['note']
    expense.save()

    # Lấy lại thông tin category để trả về (tương tự to_dict)
    category = ExpenseCategory.objects(id=expense.category_id).first()
    group = None
    if category:
        group = ExpenseCategoryGroup.objects(id=category.group_id).first()

    return jsonify({
        'message': 'Cập nhật chi tiêu thành công',
        'data': {
            'amount': expense.amount,
            'category_id': str(expense.category_id),
            'category_name': category.label if category else None,
            'date': expense.date.isoformat(),
            'note': expense.note,
        }
    }), 200

@expense_bp.route('/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_expense(id):
    user_id = str(get_jwt_identity())
    try:
        expense = Expense.objects.get(id=ObjectId(id))
    except Expense.DoesNotExist:
        return jsonify({'message': 'Expense không tồn tại'}), 404

    if expense.user_id != user_id:
        return jsonify({'message': 'Bạn không có quyền xóa bản ghi này'}), 403

    expense.delete()
    return jsonify({'message': 'Xóa chi tiêu thành công'}), 200