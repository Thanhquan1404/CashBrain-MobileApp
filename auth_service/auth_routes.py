# auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from mongoengine import DoesNotExist
from auth_service.user_model import User
from auth_service.auth_utils import hash_password, verify_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ─── Đăng ký người dùng ─────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Let fill in your username, email or password'}), 400

    # Kiểm tra username hoặc email đã tồn tại
    if User.objects(username=username).first():
        return jsonify({'message': 'Username has existed'}), 409
    if User.objects(email=email).first():
        return jsonify({'message': 'Email has existed'}), 409

    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role='user'   # mặc định
    )
    new_user.save()

    additional_claims = {'role': new_user.role}
    access_token = create_access_token(identity=str(new_user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(new_user.id))

    return jsonify({
        'msg': 'Successfully register a new account',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }
    }), 201

# ─── Đăng nhập ─────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'Message': 'Do not forget to fill in your username and password'}), 400

    user = User.objects(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'message': 'Your username or password is incorrect'}), 401

    additional_claims = {'role': user.role}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message': "Successfully login!",
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }
    }), 200

# ─── Làm mới token ─────────────────────────────────────
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    # Lấy lại role từ database (hoặc từ token cũ nếu muốn)
    user = User.objects(id=current_user_id).first()
    role = user.role if user else 'user'
    new_access_token = create_access_token(identity=current_user_id,
                                           additional_claims={'role': role})
    return jsonify({
        'message': 'Successfully retrieve new access token via refresh',
        'data': {'access_token': new_access_token}
    }), 200

# ─── Lấy thông tin cá nhân (protected) ────────────────
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    try:
        user = User.objects.get(id=current_user_id)
    except DoesNotExist:
        return jsonify({'message': 'User does not exist'}), 404

    return jsonify({
        'message': 'Successfully retrieve user profile',
        'data': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        }
    }), 200

# ─── Endpoint mẫu kiểm tra role (phân quyền) ─────────
@auth_bp.route('/admin-only', methods=['GET'])
@jwt_required()
def admin_only():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'message': 'You do not have permisssion for this action'}), 403
    return jsonify({'msg': 'Welcome admin!'}), 200