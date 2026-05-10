```text
auth_service/
├── app/
│   ├── __init__.py
│   ├── config.py            # Thêm bind database
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # Bind auth_db
│   ├── auth/
│   │   └── ...
│   ├── income/              # Service Thu nhập
│   │   ├── __init__.py
│   │   ├── models.py        # IncomeCategory, Income
│   │   └── routes.py        # CRUD API
│   ├── expense/             # Service Chi tiêu
│   │   ├── __init__.py
│   │   ├── models.py        # ExpenseCategory, Expense
│   │   └── routes.py
├── run.py
├── .env
├── requirements.txt
├── authentication_service.md
├── income_service.md
└── expense_service.md
```