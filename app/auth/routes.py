from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.user import User
from app.auth.utils import hash_password, verify_password

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

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username has existed'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email has existed'}), 409

    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)
    )
    db.session.add(new_user)
    db.session.commit()

    additional_claims = {'role': 'user'}  # sau này lấy từ DB
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

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'message': 'Your username or password is incorrect'}), 401

    # Tạo token, có thể thêm claim (ví dụ: role)
    additional_claims = {'role': 'user'}  # sau này lấy từ DB
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
@jwt_required(refresh=True)  # yêu cầu refresh token
def refresh():
    current_user_id = get_jwt_identity()
    # Có thể thêm claims mới nếu cần
    new_access_token = create_access_token(identity=current_user_id,
                                           additional_claims={'role': 'user'})
    return jsonify({'access_token': new_access_token}), 200


# ─── Lấy thông tin cá nhân (protected) ────────────────
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'msg': 'User do not exist'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    }), 200


# ─── Endpoint mẫu kiểm tra role (phân quyền) ─────────
@auth_bp.route('/admin-only', methods=['GET'])
@jwt_required()
def admin_only():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'msg': 'Bạn không có quyền truy cập'}), 403
    return jsonify({'msg': 'Chào mừng admin!'}), 200