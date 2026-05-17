# app.py
from flask import Flask
from flask_jwt_extended import JWTManager
from mongoengine import connect
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Cấu hình JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
jwt = JWTManager(app)

# Kết nối MongoDB Serverless
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable")

connect(host=MONGO_URI, alias='default')   # kết nối mặc định

# Import và đăng ký blueprint sau khi connect
from expense_service.expense_routes import expense_bp
from auth_service.auth_routes import auth_bp
from income_service.income_routes import income_bp
app.register_blueprint(expense_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(income_bp)

if __name__ == '__main__':
    app.run(debug=True)