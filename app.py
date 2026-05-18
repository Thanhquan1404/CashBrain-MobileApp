from flask import Flask
from flask_jwt_extended import JWTManager
from mongoengine import connect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

app = Flask(__name__)

# ====================== CORS ======================
CORS(app, origins="*", supports_credentials=False,
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ====================== JWT & Mongo ======================
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
# ... (giữ nguyên phần JWT và Mongo của bạn)

# ====================== REGISTER BLUEPRINTS ======================
from expense_service.expense_routes import expense_bp
from auth_service.auth_routes import auth_bp
from income_service.income_routes import income_bp
from analysis_service.analysis_routes import analysis_bp

app.register_blueprint(expense_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(income_bp)
app.register_blueprint(analysis_bp)

# ====================== FIX OPTIONS 404 - Catch all Preflight ======================
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_api_options(path):
    """Catch tất cả request OPTIONS bắt đầu bằng /api/"""
    print(f"✅ OPTIONS caught: /api/{path}")  # Log để debug trên Render
    response = app.make_response('')
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response, 200


@app.route('/<path:path>', methods=['OPTIONS'])
def handle_all_options(path):
    """Catch-all dự phòng"""
    print(f"✅ OPTIONS caught: /{path}")
    response = app.make_response('')
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"
    return response, 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)