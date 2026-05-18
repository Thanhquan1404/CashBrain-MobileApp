from flask import Flask
from flask_jwt_extended import JWTManager
from mongoengine import connect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

app = Flask(__name__)

# ====================== CẤU HÌNH CHO RENDER ======================
app.config['DEBUG'] = False                    # ← Quan trọng: Tắt debug khi deploy
app.config['ENV'] = 'production'

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
if not app.config.get('JWT_SECRET_KEY'):
    raise ValueError("JWT_SECRET_KEY is missing in environment variables!")

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)   # Nên để ngắn hơn
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# CORS - Rất quan trọng khi frontend gọi từ domain khác
CORS(app, resources={r"/*": {"origins": "*"}}, 
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

jwt = JWTManager(app)
# ============================================================

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable")

connect(host=MONGO_URI, alias='default')

# Import và register blueprints
from expense_service.expense_routes import expense_bp
from auth_service.auth_routes import auth_bp
from income_service.income_routes import income_bp
from analysis_service.analysis_routes import analysis_bp

app.register_blueprint(expense_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(income_bp)
app.register_blueprint(analysis_bp)

@app.after_request
def add_cors_headers(response):
    if response.headers.get('Access-Control-Allow-Origin') is None:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# ====================== CHẠY TRÊN RENDER ======================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)