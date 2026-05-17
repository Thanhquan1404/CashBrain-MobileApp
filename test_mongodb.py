#!/usr/bin/env python3
"""
test_mongodb.py - Kiểm tra kết nối tới MongoDB Serverless

Cách dùng:
1. Đặt chuỗi kết nối MongoDB vào biến môi trường MONGO_URI
   hoặc sửa trực tiếp biến MONGO_URI bên dưới.
2. Chạy lệnh: python test_mongodb.py
"""

import os
import sys
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (nếu có)
load_dotenv()

# Lấy chuỗi kết nối - ưu tiên từ biến môi trường, nếu không thì dùng giá trị mặc định (cần sửa)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    # Nếu chưa set biến môi trường, bạn có thể nhập trực tiếp tại đây (không khuyến khích cho production)
    print("⚠️ Chưa tìm thấy biến môi trường MONGO_URI.")
    print("Bạn có thể nhập connection string bên dưới (hoặc cài đặt MONGO_URI trong .env):")
    MONGO_URI = input("Nhập MongoDB URI: ").strip()
    if not MONGO_URI:
        print("❌ Không có URI. Thoát.")
        sys.exit(1)

# Ẩn mật khẩu khi in ra log (chỉ hiển thị một phần)
def mask_uri(uri):
    import re
    return re.sub(r'(mongodb(?:\+srv)?://)([^:]+):([^@]+)@', r'\1\2:****@', uri)

print(f"🔌 Đang kết nối tới: {mask_uri(MONGO_URI)}")

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
except ImportError:
    print("❌ Thư viện 'pymongo' chưa được cài. Hãy chạy: pip install pymongo")
    sys.exit(1)

# Tạo client với timeout hợp lý (5 giây)
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Thực hiện lệnh ping để kiểm tra kết nối thực tế
    client.admin.command('ping')
    print("✅ Kết nối MongoDB thành công!")

    # Lấy thông tin server version
    server_info = client.server_info()
    print(f"📦 Server version: {server_info.get('version', 'unknown')}")

    # Liệt kê các database (tuỳ chọn, để xác nhận quyền truy cập)
    db_list = client.list_database_names()
    print(f"🗄️  Các database hiện có: {', '.join(db_list) if db_list else '(không có hoặc không có quyền xem)'}")

    # Đóng kết nối
    client.close()

except ConnectionFailure as e:
    print(f"❌ Không thể kết nối tới MongoDB (ConnectionFailure): {e}")
    print("   Kiểm tra: URI, whitelist IP, tường lửa, hoặc server có đang hoạt động?")
    sys.exit(1)
except ServerSelectionTimeoutError as e:
    print(f"❌ Timeout khi chọn server: {e}")
    print("   Nguyên nhân có thể: sai URI, network bị chặn, hoặc cluster không truy cập được.")
    sys.exit(1)
except ConfigurationError as e:
    print(f"❌ Lỗi cấu hình URI: {e}")
    print("   Đảm bảo connection string đúng định dạng (ví dụ: mongodb+srv://...).")
    sys.exit(1)
except Exception as e:
    print(f"❌ Lỗi không xác định: {type(e).__name__} - {e}")
    sys.exit(1)

print("🎉 Test hoàn tất. Project của bạn có thể kết nối MongoDB Serverless.")