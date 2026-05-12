import os
from dotenv import load_dotenv

load_dotenv()  # đọc biến môi trường từ file .env (nếu có)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@localhost/auth_service_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Bind database for finance service
    SQLALCHEMY_BINDS = {
        'finance_db': os.getenv('FINANCE_DATABASE_URL', 'mysql+pymysql://root:password@localhost/finance_db'),
        'chatbot_db': os.getenv('CHATBOT_DATABASE_URL', 'mysql+pymysql://root:password@localhost/chatbot_db')
    }

    # JWT config
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change')
    JWT_ACCESS_TOKEN_EXPIRES = 36000  # 1 giờ (giây)
    JWT_REFRESH_TOKEN_EXPIRES = 864000  # 1 ngày