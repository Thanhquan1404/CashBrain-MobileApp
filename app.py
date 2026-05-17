# app.py
from flask import Flask
from flask_jwt_extended import JWTManager
from mongoengine import connect
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

app = Flask(__name__)

# ====================== JWT CONFIGURATION ======================
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-super-secret-key')

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=600)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)    # Recommended: 7 - 30 days
#==================================================================

# Kết nối MongoDB Serverless
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable")

connect(host=MONGO_URI, alias='default')   # kết nối mặc định

# Import và đăng ký blueprint sau khi connect
from expense_service.expense_routes import expense_bp
from auth_service.auth_routes import auth_bp
from income_service.income_routes import income_bp
from analysis_service.analysis_routes import analysis_bp
app.register_blueprint(expense_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(income_bp)
app.register_blueprint(analysis_bp)

if __name__ == '__main__':
    app.run(debug=True)