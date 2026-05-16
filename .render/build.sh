#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running database migrations..."
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app.models import user
    from app.income import models as income_models
    from app.expense import models as expense_models
    from app.chatbot import models as chatbot_models
    from app import db
    db.create_all()
    print('Database tables created/verified successfully!')
"

echo "Build completed successfully!"
