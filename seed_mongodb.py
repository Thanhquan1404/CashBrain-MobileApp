# seed_mongodb.py
import os
from dotenv import load_dotenv
from mongoengine import connect
from expense_service.expense_models import ExpenseCategoryGroup, ExpenseCategory

load_dotenv()

# Kết nối MongoDB
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("Chưa có MONGO_URI trong file .env")

connect(host=MONGO_URI)

# Xoá dữ liệu cũ (nếu muốn chạy lại từ đầu)
print("🗑️  Đang xoá dữ liệu cũ...")
ExpenseCategoryGroup.objects.delete()
ExpenseCategory.objects.delete()
print("✅ Đã xoá.")

# Dữ liệu groups
groups_data = [
    {"title": "Daily Expenses", "color": "#ea8a1a", "bg_color": "#fff4e8"},
    {"title": "Extra Expenses", "color": "#f472b6", "bg_color": "#FFCEE3"},
    {"title": "Fixed Expenses", "color": "#2f7ee6", "bg_color": "#edf4ff"},
    {"title": "Investment & Savings", "color": "#9B5DE0", "bg_color": "#FFDBFD"},
]

# Tạo groups và lưu lại object để lấy _id
groups = []
for g in groups_data:
    group = ExpenseCategoryGroup(
        title=g["title"],
        color=g["color"],
        bg_color=g["bg_color"]
    )
    group.save()
    groups.append(group)
    print(f"📁 Đã tạo group: {group.title} (id: {group.id})")

# Dữ liệu categories theo từng group (dựa trên thứ tự trong danh sách groups)
# (0: Daily Expenses, 1: Extra Expenses, 2: Fixed Expenses, 3: Investment & Savings)
categories_data = [
    # Daily Expenses (group index 0)
    {"group_idx": 0, "label": "Groceries", "icon": "basket-outline", "color": "#f97316"},
    {"group_idx": 0, "label": "Food & Drinks", "icon": "restaurant-outline", "color": "#f3ac33"},
    {"group_idx": 0, "label": "Transportation", "icon": "car-outline", "color": "#F48F68"},
    # Extra Expenses (group index 1)
    {"group_idx": 1, "label": "Shopping", "icon": "bag-handle-outline", "color": "#BF4646"},
    {"group_idx": 1, "label": "Entertainment", "icon": "film-outline", "color": "#fb7185"},
    {"group_idx": 1, "label": "Beauty", "icon": "sparkles-outline", "color": "#ec4899"},
    {"group_idx": 1, "label": "Healthcare", "icon": "medical-outline", "color": "#f43f5e"},
    {"group_idx": 1, "label": "Miscellaneous", "icon": "apps-outline", "color": "#F13E93"},
    # Fixed Expenses (group index 2)
    {"group_idx": 2, "label": "Rent", "icon": "home-outline", "color": "#4f9cf2"},
    {"group_idx": 2, "label": "Bills", "icon": "receipt-outline", "color": "#2FA4D7"},
    {"group_idx": 2, "label": "Family", "icon": "people-outline", "color": "#134E8E"},
    # Investment & Savings (group index 3)
    {"group_idx": 3, "label": "Investment", "icon": "trending-up-outline", "color": "#696FC7"},
    {"group_idx": 3, "label": "Education", "icon": "school-outline", "color": "#a78bfa"},
]

# Tạo categories
for cat in categories_data:
    group = groups[cat["group_idx"]]
    category = ExpenseCategory(
        group_id=group.id,
        label=cat["label"],
        icon=cat["icon"],
        color=cat["color"]
    )
    category.save()
    print(f"   📝 Đã tạo category: {category.label} (thuộc group: {group.title})")

print("\n🎉 Seeding hoàn tất!")