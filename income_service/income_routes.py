# income_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from income_service.income_models import IncomeCategory, Income

income_bp = Blueprint('income', __name__, url_prefix='/api/income')

# ────────────────────── CATEGORY CRUD ──────────────────────
@income_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_income_categories():
    categories = IncomeCategory.objects()
    return jsonify([
        {'id': str(c.id), 'name': c.name, 'description': c.description}
        for c in categories
    ]), 200

@income_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_income_category():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'msg': 'Thiếu tên danh mục'}), 400
    cat = IncomeCategory(
        name=name,
        description=data.get('description', '')
    )
    cat.save()
    return jsonify({'msg': 'Tạo danh mục thành công', 'id': str(cat.id)}), 201

@income_bp.route('/categories/<string:id>', methods=['PUT'])
@jwt_required()
def update_income_category(id):
    try:
        cat = IncomeCategory.objects.get(id=ObjectId(id))
    except IncomeCategory.DoesNotExist:
        return jsonify({'msg': 'Danh mục không tồn tại'}), 404

    data = request.get_json()
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    cat.save()
    return jsonify({'msg': 'Cập nhật danh mục thành công'}), 200

@income_bp.route('/categories/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_income_category(id):
    try:
        cat = IncomeCategory.objects.get(id=ObjectId(id))
    except IncomeCategory.DoesNotExist:
        return jsonify({'msg': 'Danh mục không tồn tại'}), 404
    cat.delete()
    return jsonify({'msg': 'Xóa danh mục thành công'}), 200

# ────────────────────── INCOME CRUD ──────────────────────
@income_bp.route('/', methods=['GET'])
@jwt_required()
def get_incomes():
    user_id = get_jwt_identity()   # string
    incomes = Income.objects(user_id=user_id).order_by('-date')
    return jsonify({
        'msg': 'Successfully get user incomes',
        'data': [inc.to_dict() for inc in incomes]
    }), 200

@income_bp.route('/', methods=['POST'])
@jwt_required()
def create_income():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')
    date_str = data.get('date')

    if amount is None or not date_str:
        return jsonify({'msg': 'Thiếu amount hoặc date'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'msg': 'Sai định dạng ngày (YYYY-MM-DD)'}), 400

    income = Income(
        user_id=user_id,
        amount=float(amount),
        date=date,
        note=data.get('note', '')
    )
    income.save()
    return jsonify({'msg': 'Thêm thu nhập thành công', 'data': income.to_dict()}), 201

@income_bp.route('/<string:id>', methods=['PUT'])
@jwt_required()
def update_income(id):
    user_id = get_jwt_identity()
    try:
        income = Income.objects.get(id=ObjectId(id))
    except Income.DoesNotExist:
        return jsonify({'msg': 'Bản ghi thu nhập không tồn tại'}), 404

    if income.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền sửa bản ghi này'}), 403

    data = request.get_json()
    if 'amount' in data:
        income.amount = float(data['amount'])
    if 'date' in data:
        try:
            income.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'msg': 'Sai định dạng ngày'}), 400
    if 'note' in data:
        income.note = data['note']
    # Nếu có category_id (dù model Income hiện tại không có, nhưng nếu thêm sau)
    if 'category_id' in data:
        # Có thể thêm trường category_id vào model nếu cần
        pass
    income.save()
    return jsonify({'msg': 'Cập nhật thu nhập thành công'}), 200

@income_bp.route('/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_income(id):
    user_id = get_jwt_identity()
    try:
        income = Income.objects.get(id=ObjectId(id))
    except Income.DoesNotExist:
        return jsonify({'msg': 'Bản ghi thu nhập không tồn tại'}), 404

    if income.user_id != user_id:
        return jsonify({'msg': 'Bạn không có quyền xóa bản ghi này'}), 403

    income.delete()
    return jsonify({'msg': 'Xóa thu nhập thành công'}), 200