# Authentication Service – Tài liệu phát triển

## 1. Giới thiệu
Authentication Service cung cấp API xác thực người dùng dựa trên JWT, xây dựng bằng Flask, MySQL và JWT. Dịch vụ cho phép đăng ký, đăng nhập, làm mới token, và truy cập các tài nguyên được bảo vệ. Hệ thống được thiết kế sẵn sàng mở rộng phân quyền (role‑based access control) và tích hợp WebSocket trong tương lai.

## 2. Công nghệ sử dụng
- **Python 3.10+** với Flask framework.
- **MySQL 8.x** – lưu trữ dữ liệu người dùng.
- **Flask-SQLAlchemy** – ORM kết nối cơ sở dữ liệu.
- **Flask-JWT-Extended** – sinh và xác thực JWT.
- **Werkzeug Security** – băm và kiểm tra mật khẩu.

## 3. Cấu trúc project

auth_service/
├── app/
│ ├── init.py # App factory, khởi tạo extensions
│ ├── config.py # Cấu hình
│ ├── models/
│ │ └── user.py # Định nghĩa bảng users
│ ├── auth/
│ │ ├── routes.py # API xác thực
│ │ └── utils.py # Hàm băm mật khẩu
├── run.py # Điểm khởi chạy
├── requirements.txt
└── authentication_service.md


## 4. Thiết kế cơ sở dữ liệu

### 4.1. Bảng `users`
| Cột            | Kiểu dữ liệu | Ràng buộc                  | Mô tả                          |
|----------------|--------------|----------------------------|--------------------------------|
| id             | INT          | PK, AUTO_INCREMENT         | ID duy nhất                    |
| username       | VARCHAR(80)  | UNIQUE, NOT NULL           | Tên đăng nhập                  |
| email          | VARCHAR(120) | UNIQUE, NOT NULL           | Email                          |
| password_hash  | VARCHAR(255) | NOT NULL                   | Mật khẩu đã được băm           |
| created_at     | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP  | Thời gian tạo                  |
| updated_at     | TIMESTAMP    | ON UPDATE CURRENT_TIMESTAMP| Thời gian cập nhật             |

*(Mở rộng trong tương lai: thêm bảng `roles`, `permissions`, `user_roles` để phân quyền chi tiết).*

### 4.2. Khởi tạo database
```sql
CREATE DATABASE auth_service_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 5. API Endpoints

Tất cả endpoint đều có tiền tố /api/auth.

### 5.1. Đăng ký

URL: /api/auth/register
Method: POST
Body JSON:

json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
Phản hồi thành công: 201 Created

json
{"msg": "Đăng ký thành công"}
Lỗi: 400 nếu thiếu trường, 409 nếu username/email đã tồn tại.
### 5.2. Đăng nhập

URL: /api/auth/login
Method: POST
Body JSON:

json
{
  "username": "string",
  "password": "string"
}
Thành công: 200 OK

json
{
  "access_token": "eyJ0...",
  "refresh_token": "eyJ1...",
  "token_type": "bearer"
}
Lỗi: 401 Unauthorized nếu sai thông tin.
5.3. Làm mới Access Token

URL: /api/auth/refresh
Method: POST
Headers: Authorization: Bearer <refresh_token>
Thành công:

json
{"access_token": "eyJ0..."}
Lỗi: 401 nếu refresh token không hợp lệ hoặc hết hạn.
5.4. Xem hồ sơ (yêu cầu xác thực)

URL: /api/auth/profile
Method: GET
Headers: Authorization: Bearer <access_token>
Thành công:

json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2026-05-07T..."
}
5.5. Kiểm tra phân quyền (ví dụ)

URL: /api/auth/admin-only
Method: GET
Headers: Authorization: Bearer <access_token>
Yêu cầu: token chứa claim role: admin.
Trả về: 200 nếu có quyền, 403 nếu không.
6. Bảo mật

Mật khẩu được băm bằng werkzeug.security.generate_password_hash (sử dụng pbkdf2:sha256).
JWT được ký bằng secret key riêng (JWT_SECRET_KEY), không lưu trữ token phía server.
Access token có thời hạn ngắn (1 giờ), refresh token giúp hạn chế lộ access token.
Các endpoint nhạy cảm đều được bảo vệ bởi decorator @jwt_required().