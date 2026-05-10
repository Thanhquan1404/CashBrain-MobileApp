from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.income.models import IncomeCategory, Income
from datetime import datetime

income_bp = Blueprint('income', __name__, url_prefix='/api/income')

# ────────────────────── CATEGORY CRUD ──────────────────────
# Lưu ý: Danh mục hiện tại dùng chung, chưa phân biệt user.

@income_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_income_categories():
    categories = IncomeCategory.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'description': c.description} for c in categories]), 200

@income_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_income_category():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'msg': 'Thiếu tên danh mục'}), 400
    cat = IncomeCategory(name=name, description=data.get('description', ''))
    db.session.add(cat)
    db.session.commit()
    return jsonify({'msg': 'Tạo danh mục thành công', 'id': cat.id}), 201

@income_bp.route('/categories/<int:id>', methods=['PUT'])
@jwt_required()
def update_income_category(id):
    cat = IncomeCategory.query.get_or_404(id)
    data = request.get_json()
    cat.name = data.get('name', cat.name)
    cat.description = data.get('description', cat.description)
    db.session.commit()
    return jsonify({'msg': 'Cập nhật danh mục thành công'}), 200

@income_bp.route('/categories/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_income_category(id):
    cat = IncomeCategory.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'msg': 'Xóa danh mục thành công'}), 200

# ────────────────────── INCOME CRUD ──────────────────────

@income_bp.route('/', methods=['GET'])
@jwt_required()
def get_incomes():
    user_id = get_jwt_identity()
    incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).all()
    return jsonify(
        {'msg': 'Successfully get user incomes', 'data': [inc.to_dict() for inc in incomes]}
    ), 200

@income_bp.route('/', methods=['POST'])
@jwt_required()
def create_income():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')
    date_str = data.get('date')

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'msg': 'Sai định dạng ngày (YYYY-MM-DD)'}), 400

    income = Income(
        user_id=user_id,
        amount=amount,
        date=date,
        note=data.get('note', '')
    )
    db.session.add(income)
    db.session.commit()
    return jsonify({'msg': 'Thêm thu nhập thành công', 'data': income.to_dict()}), 201

@income_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_income(id):
    user_id = get_jwt_identity()
    income = Income.query.get_or_404(id)

    # Kiểm tra chủ sở hữu
    if income.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền sửa bản ghi này'}), 403

    data = request.get_json()
    income.category_id = data.get('category_id', income.category_id)
    income.amount = data.get('amount', income.amount)
    if 'date' in data:
        try:
            income.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'msg': 'Sai định dạng ngày'}), 400
    income.note = data.get('note', income.note)
    db.session.commit()
    return jsonify({'msg': 'Cập nhật thu nhập thành công'}), 200

@income_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_income(id):
    user_id = get_jwt_identity()
    income = Income.query.get_or_404(id)
    if income.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền xóa bản ghi này'}), 403
    db.session.delete(income)
    db.session.commit()
    return jsonify({'msg': 'Xóa thu nhập thành công'}), 200