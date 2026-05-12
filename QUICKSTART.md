# QUICKSTART GUIDE - CashBrain AI Chatbot

## 🚀 Setup & Testing (5 phút)

### Step 1: Đảm bảo Backend đang chạy
```bash
cd /Users/quannguyen/Documents/CashBrain_Backend
source .venv/bin/activate
python run.py
# Backend should be running on http://localhost:5000
```

### Step 2: Tạo Test User & Data
Nếu chưa có:
1. Register user qua `/api/auth/register`
2. Login để lấy JWT token
3. Thêm ít nhất 10 Expense entries qua `/api/expense` (cần categories khác nhau)
4. Thêm ít nhất 2 Income entries qua `/api/income`

### Step 3: Xem Database Schema

**Ensure các tables này tồn tại:**
```sql
-- Users
SELECT * FROM users;

-- Income
SELECT * FROM income WHERE user_id = YOUR_USER_ID;

-- Expense
SELECT * FROM expense WHERE user_id = YOUR_USER_ID;

-- Chat History (mới)
SELECT * FROM chat_history WHERE user_id = YOUR_USER_ID;
```

### Step 4: Test API - cách nhanh nhất

#### **4a. Health Check (không cần JWT)**
```bash
curl -X GET "http://localhost:5000/api/chat/health"
```

Response:
```json
{
    "status": "healthy",
    "service": "chatbot",
    "timestamp": "2026-05-12T10:30:00.123456"
}
```

#### **4b. Get JWT Token**
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Copy `access_token` từ response.

#### **4c. Test Financial Analysis**
```bash
curl -X GET "http://localhost:5000/api/chat/financial-debug?months=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Kiểm tra response:
- ✓ `summary.total_income` > 0
- ✓ `summary.total_expense` > 0
- ✓ `categories` không empty
- ✓ `monthly_breakdown` có data

#### **4d. Test Insights Detection**
```bash
curl -X GET "http://localhost:5000/api/chat/insights?months=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Kiểm tra:
- ✓ `insights` array có ít nhất 3-4 items
- ✓ Mỗi insight là một câu mô tả tiếng Việt

#### **4e. Test Main Endpoint - Chat Message**
```bash
curl -X POST "http://localhost:5000/api/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "months": 3
  }'
```

Response chứa:
- `final_prompt`: Full prompt sẵn sàng gửi Gemini (2000+ chars)
- `financial_summary`: Dict tóm tắt tài chính
- `insights`: Array insights
- `history_count`: Số message trong history

#### **4f. Test Prompt Preview**
```bash
curl -X POST "http://localhost:5000/api/chat/prompt-preview" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi chi tiêu bao nhiêu?",
    "months": 3
  }'
```

**Lưu ý**: Preview không lưu message vào history

#### **4g. Test Prompt Blocks Debug**
```bash
curl -X POST "http://localhost:5000/api/chat/prompt-blocks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi chi tiêu bao nhiêu?",
    "months": 3
  }'
```

Response:
```json
{
    "blocks": {
        "system_role": "...",
        "user_context": "...",
        "financial_data": "...",
        "insights": "...",
        "history": "...",
        "timestamp": "2026-05-12T10:30:00"
    },
    "full_prompt_length": 2456
}
```

#### **4h. Check History**
```bash
curl -X GET "http://localhost:5000/api/chat/history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Kiểm tra:
- ✓ `message_count` > 0 (nếu đã test /message)
- ✓ Messages có `role` (user/assistant)
- ✓ Mỗi message có `content`

### Step 5: Run Python Test Suite

```bash
# Make script executable
chmod +x test_chatbot_api.py

# Run tests
python test_chatbot_api.py "YOUR_JWT_TOKEN" 1 3
```

Output akan là:
```
======================================================================
TEST 1: Health Check
======================================================================

✓ Health check passed

======================================================================
TEST 2: Financial Analysis Debug (GET)
======================================================================

✓ Financial data retrieved

Summary:
  • Total Income: 50,000,000 VND
  • Total Expense: 35,000,000 VND
  • Balance: 15,000,000 VND
  • Saving Rate: 30.0%
  • Daily Average: 194,444 VND

Categories:
  • Food: 10,500,000 VND (30%, 28 days)
  • Shopping: 8,400,000 VND (24%, 5 days)
  ...

======================================================================
TEST 3: Insights Only
======================================================================

✓ 4 insights detected

Insights:
  1. ✓ Chi tiêu ổn định...
  2. ⚠️ Mua sắm không kiểm soát...
  3. 🟢 Tỷ lệ tiết kiệm tốt...
  4. 📊 Chi tiêu thực phẩm...

...
```

---

## 🔍 Troubleshooting

### Issue 1: "404 Not Found" trên /api/chat endpoints
**Nguyên nhân**: Chatbot blueprint không được register
**Giải pháp**: Kiểm tra `app/__init__.py`
```python
from app.chatbot.routes import chatbot_bp
app.register_blueprint(chatbot_bp)
```

### Issue 2: "JWT_REQUIRED_ERROR"
**Nguyên nhân**: Không có valid token
**Giải pháp**: 
1. Login lại để lấy token mới
2. Đảm bảo format đúng: `Authorization: Bearer TOKEN`

### Issue 3: No financial data (categories empty)
**Nguyên nhân**: Người dùng không có expense/income data
**Giải pháp**:
1. Thêm test data via API
2. Hoặc insert trực tiếp vào database
3. Đảm bảo expense có category_id

### Issue 4: "categories" trong database query fail
**Nguyên nhân**: Expense table không có `category_id` hoặc không join đúng
**Giải pháp**: Kiểm tra [financial_analysis.py](app/chatbot/financial_analysis.py) Line 48-58
```python
# Ensure join này đúng:
category_stats = db.session.query(
    ExpenseCategory.label,  # <- table name
    ...
).join(Expense, Expense.category_id == ExpenseCategory.id)  # <- join condition
```

### Issue 5: Insights không trigger (insights list empty)
**Nguyên nhân**: Rule conditions quá khắt khe
**Giải pháp**: Tạm thời gỡ bỏ điều kiện để test
```python
def _rule_stable_food_spending(self):
    # Gỡ bỏ tạm thời:
    # if food_cat['pct_of_total'] > 20 and food_cat['active_days'] > 20:
    #     return "..."
    
    # Test: Always return
    return "TEST: Thực phẩm chi tiêu 30%, 28 ngày"
```

---

## 📋 Expected Behavior

### ✓ Correct Flow
```
1. POST /message
   ↓
2. Financial Analysis: Query DB → Calculate numbers
   ↓
3. Financial Intent: Apply rules → Generate insights
   ↓
4. Prompt Engine: Assemble 6 blocks → Create prompt
   ↓
5. Save to DB: ChatHistory (user message + snapshot)
   ↓
6. Response: Return final_prompt, insights, etc.
```

### ✓ What Good Data Looks Like

**Financial Data:**
```python
{
    'total_income': 50000000.0,      # Non-zero
    'total_expense': 35000000.0,     # Non-zero
    'balance': 15000000.0,           # Can be positive or negative
    'saving_rate': 30.0,             # Between -100 to 100
    'categories': {
        'Food': {...},
        'Shopping': {...},
        'Transport': {...},
        # At least 3 categories
    }
}
```

**Insights:**
```python
[
    "✓ Chi tiêu ổn định...",
    "⚠️ Mua sắm không kiểm soát...",
    "🟢 Tỷ lệ tiết kiệm tốt...",
    # At least 3-4 insights
]
```

**Final Prompt:**
- Contains 6 blocks separated by `────────────────...`
- Length: 2000-3000 characters
- Ends with: "Assistant:" (ready for Gemini)

---

## 🛠️ Common Test Messages

Test các categories khác nhau:

```bash
# Food
"Tôi chi tiêu bao nhiêu cho ăn uống?"

# Shopping  
"Mua sắm của tôi là bao nhiêu?"

# Overall
"Tình hình tài chính của tôi thế nào?"

# Trends
"Chi tiêu của tôi có ổn định không?"

# Income
"Thu nhập của tôi là bao nhiêu?"

# Savings
"Tôi tiết kiệm được bao nhiêu?"
```

---

## 📊 Database Checks

### Check if ChatHistory is saving correctly
```sql
SELECT * FROM chat_history WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 5;

-- Should show:
-- | id | user_id | role | content | timestamp | financial_snapshot |
-- | 1  | 1       | user | "Tôi..." | 2026-05-12 10:30:00 | {...} |
```

### Check ChatHistory schema
```sql
DESCRIBE chat_history;

-- Must have:
-- - id
-- - user_id
-- - role (user/assistant)
-- - content
-- - timestamp
-- - financial_snapshot (JSON)
```

---

## 🚀 Next Steps After Testing

1. **Integrate Gemini API**
   - Get API key from Google Cloud Console
   - Modify `/api/chat/message` endpoint to:
     ```python
     # Call Gemini with final_prompt
     gemini_response = gemini_client.generate_content(final_prompt)
     
     # Save assistant response
     memory.add_message('assistant', gemini_response.text)
     
     # Return both prompt and response
     return jsonify({
         'final_prompt': final_prompt,
         'assistant_response': gemini_response.text,
         ...
     })
     ```

2. **Fine-tune Rules**
   - Monitor which rules trigger most
   - Adjust thresholds based on real data
   - Add new rules for edge cases

3. **Memory Tracking Phase**
   - Analyze `financial_snapshot` trends
   - Track saving_rate over time
   - Predict future patterns

4. **Frontend Integration**
   - Call `/api/chat/message` on send
   - Display assistant_response (once Gemini integrated)
   - Show insights in UI
   - Display chat history

---

## 📞 Quick Reference

| Endpoint | Method | Purpose | JWT Required |
|----------|--------|---------|--------------|
| /api/chat/health | GET | Health check | No |
| /api/chat/message | POST | Send message, get prompt | Yes |
| /api/chat/prompt-preview | POST | Preview prompt (no save) | Yes |
| /api/chat/history | GET | View history | Yes |
| /api/chat/history | DELETE | Clear history | Yes |
| /api/chat/financial-debug | GET | Raw financial data | Yes |
| /api/chat/financial-debug | POST | Data + insights | Yes |
| /api/chat/insights | GET | Insights only | Yes |
| /api/chat/prompt-blocks | POST | Debug prompt blocks | Yes |

---

## ✅ Done!

Nếu tất cả tests pass, chatbot architecture đã sẵn sàng cho:
1. **Gemini API integration** (next phase)
2. **Frontend chatbot UI** (next phase)
3. **Memory tracking & analytics** (future phase)

Good luck! 🚀
