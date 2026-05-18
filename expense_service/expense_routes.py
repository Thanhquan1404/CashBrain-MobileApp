# expense_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from expense_service.expense_models import ExpenseCategoryGroup, ExpenseCategory, Expense, ExpenseImage
import cloudinary.uploader
from werkzeug.utils import secure_filename
from utils.cloudinary_helper import upload_expense_image, delete_expense_image

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


# ────────────────────── EXPENSE-IMAGE CRUD ──────────────────────
@expense_bp.route('/image', methods=['POST'])
@jwt_required()
def create_expense_image():
    user_id = str(get_jwt_identity())
    
    # Lấy dữ liệu text từ form
    category_id = request.form.get('category_id')
    amount = request.form.get('amount')
    date_str = request.form.get('date')
    note = request.form.get('note', '')
    
    # File ảnh (bắt buộc)
    if 'image' not in request.files:
        return jsonify({'message': 'Do not have image file'}), 400
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'message': 'File is empty'}), 400
    
    # Validate các trường
    if not category_id or not amount or not date_str:
        return jsonify({'message': 'Fill in category_id, amount or date'}), 400
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Date format is unacceptable (YYYY-MM-DD)'}), 400
    
    # Kiểm tra category tồn tại
    if not ExpenseCategory.objects(id=ObjectId(category_id)).first():
        return jsonify({'message': 'category_id does not exist'}), 400
    
    # Upload ảnh lên Cloudinary
    try:
        upload_result = upload_expense_image(image_file)
    except Exception as e:
        return jsonify({'message': f'Error image uploading: {str(e)}'}), 500
    
    # Tạo expense
    expense = Expense(
        user_id=user_id,
        category_id=ObjectId(category_id),
        amount=float(amount),
        date=date,
        note=note
    )
    expense.save()
    
    # Tạo bản ghi image
    expense_image = ExpenseImage(
        expense_id=expense.id,
        image_url=upload_result['url'],
        public_id=upload_result['public_id']
    )
    expense_image.save()
    
    # Chuẩn bị response (gộp thêm image_url)
    expense_dict = expense.to_dict()
    expense_dict['image_url'] = upload_result['url']
    
    return jsonify({
        'message': 'Sucessfully create an expense with image',
        'data': expense_dict
    }), 201

@expense_bp.route('/image', methods=['GET'])
@jwt_required()
def get_expenses_image():
    user_id = str(get_jwt_identity())
    
    # BƯỚC 1: Lấy tất cả ảnh thuộc về user này trước (giả định ExpenseImage hoặc Expense có liên kết user_id)
    # Nếu ExpenseImage không có user_id, chúng ta sẽ tối ưu theo cách lọc ở bước sau.
    
    # Cách 1: Giữ nguyên luồng truy vấn của bạn nhưng lọc kết quả đầu ra
    expenses = list(Expense.objects(user_id=user_id).order_by('-date'))
    
    if not expenses:
        return jsonify({'message': 'Success', 'data': []}), 200
    
    expense_ids = [exp.id for exp in expenses]
    
    # Truy vấn tất cả ảnh tương ứng
    images = ExpenseImage.objects(expense_id__in=expense_ids)
    image_map = {str(img.expense_id): img.image_url for img in images}
    
    # Gắn image_url và CHỈ lấy những expense có ảnh
    result = []
    for exp in expenses:
        image_url = image_map.get(str(exp.id))
        
        if image_url:  # <-- ĐIỀU KIỆN QUAN TRỌNG: Chỉ lấy nếu có ảnh
            exp_dict = exp.to_dict()
            exp_dict['image_url'] = image_url
            result.append(exp_dict)
    
    return jsonify({
        'message': 'Lấy danh sách chi tiêu có ảnh thành công',
        'data': result
    }), 200

@expense_bp.route('/image/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_expense_image(id):
    user_id = str(get_jwt_identity())
    try:
        expense = Expense.objects.get(id=ObjectId(id))
    except Expense.DoesNotExist:
        return jsonify({'message': 'Expense do not exist'}), 404
    
    if expense.user_id != user_id:
        return jsonify({'message': 'You do not have permission to delete'}), 403
    
    # Lấy bản ghi ảnh (nếu có)
    expense_image = ExpenseImage.objects(expense_id=expense.id).first()
    if expense_image:
        # Xoá ảnh trên Cloudinary
        delete_expense_image(expense_image.public_id)
        # Xoá bản ghi ảnh trong DB
        expense_image.delete()
    
    # Xoá expense
    expense.delete()
    return jsonify({'message': 'Successfully delete expense with image'}), 200