from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Khởi tạo extensions
    db.init_app(app)
    jwt.init_app(app)

    # Import models để SQLAlchemy biết
    with app.app_context():
        from app.models import user
        from app.income import models as income_models
        from app.expense import models as expense_models
        from app.chatbot import models as chatbot_models
        db.create_all()

    # Đăng ký blueprint 
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.income.routes import income_bp
    app.register_blueprint(income_bp)

    from app.expense.routes import expense_bp
    app.register_blueprint(expense_bp)

    from app.analysis.routes import analysis_bp
    app.register_blueprint(analysis_bp)

    from app.chatbot.routes import chatbot_bp
    app.register_blueprint(chatbot_bp)

    return app