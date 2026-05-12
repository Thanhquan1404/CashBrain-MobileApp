# AI CHATBOT ARCHITECTURE GUIDE - CashBrain

## 🎯 Tổng Quan (Overview)

Đây là hướng dẫn chi tiết xây dựng **AI Chatbot** tích hợp với hệ thống quản lý chi tiêu **CashBrain**. 

**Mục tiêu**: Giúp người dùng hiểu rõ chi tiêu của họ thông qua hội thoại tự nhiên, với AI được cấp quyền truy cập dữ liệu tài chính thực tế của người dùng.

---

## 📊 Kiến Trúc 4 Lớp

```
┌─────────────────────────────────────────────────────────────┐
│                  User sends message to API                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. FINANCIAL ANALYSIS LAYER (financial_analysis.py)         │
│    - Query Expense, Income từ DB                             │
│    - Tính: tổng, trung bình, độ lệch, category breakdown   │
│    - Output: Dict chứa raw numbers (không có text)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FINANCIAL INTENT LAYER (financial_intent.py)             │
│    - Nhận raw numbers từ Layer 1                             │
│    - Áp dụng 15+ Rules để tạo insights                       │
│    - Output: List các câu mô tả bằng tiếng Việt             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PROMPT ENGINE (prompt_engine.py)                          │
│    - Ghép 6 blocks: Role, Context, Data, Insights,          │
│      History, Task                                            │
│    - Output: Final prompt sẵn sàng gửi Gemini API           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONVERSATION MEMORY (conversation_memory.py)             │
│    - Lưu history với sliding window (tối đa 10 turns)       │
│    - Attach financial_snapshot để theo dõi thay đổi         │
│    - Output: Lịch sử hội thoại để context cho turn tới      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ API RESPONSE                                                  │
│ {                                                             │
│   "final_prompt": "...",      ← Ready to send Gemini         │
│   "financial_summary": {...}, ← Debug info                   │
│   "insights": [...]           ← What rules triggered         │
│ }                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 LAYER 1: Financial Analysis Layer

### Nhiệm vụ
Lớp này là "số học thuần túy" - không có ngôn ngữ tự nhiên, chỉ có math.

### Đầu vào
```python
user_id = 123
months = 6  # phân tích 6 tháng gần đây
```

### Quá trình tính toán
1. **Query tổng thu nhập, chi tiêu** từ Income, Expense tables
2. **Tính tỷ lệ tiết kiệm** = (tổng_thu_nhập - tổng_chi_tiêu) / tổng_thu_nhập
3. **Phân tích theo category**:
   - Tổng tiền chi cho từng category
   - Số ngày hoạt động (active_days)
   - % đóng góp vào tổng chi
4. **Tính độ lệch chuẩn** (std_monthly_expense) để đo volatility
5. **Time series data**:
   - Breakdown theo tháng
   - Breakdown theo ngày trong tuần (weekly)
   - Top 5 transactions lớn nhất

### Đầu ra
```python
{
    'user_id': 123,
    'period_months': 6,
    'analysis_date': '2026-05-12T10:30:00',
    'summary': {
        'total_income': 50000000.0,          # 50M VND
        'total_expense': 35000000.0,         # 35M VND
        'balance': 15000000.0,               # 15M VND dư
        'saving_rate': 30.0,                 # 30%
        'avg_monthly_expense': 5833333.33,   # trung bình/tháng
        'std_monthly_expense': 458333.33,    # độ lệch chuẩn
        'daily_avg_expense': 194444.44       # trung bình/ngày
    },
    'categories': {
        'Food': {
            'total': 10500000.0,
            'count': 180,                    # 180 transactions
            'active_days': 28,               # xuất hiện 28/30 ngày
            'pct_of_total': 30.0,            # 30% tổng chi
            'avg_per_day': 375000.0          # 375k/ngày
        },
        'Shopping': {
            'total': 8400000.0,
            'count': 12,
            'active_days': 5,                # chỉ 5/30 ngày
            'pct_of_total': 24.0,
            'avg_per_day': 1680000.0
        },
        # ... other categories
    },
    'monthly_breakdown': [
        {'year': 2025, 'month': 11, 'total': 5500000.0, 'active_days': 30},
        {'year': 2025, 'month': 12, 'total': 6200000.0, 'active_days': 31},
        # ...
    ],
    'top_transactions': [
        {
            'amount': 850000.0,
            'category': 'Shopping',
            'date': '2026-05-10',
            'note': 'Laptop bag'
        },
        # ...
    ]
}
```

### Khi nào dùng
```python
from app.chatbot.financial_analysis import FinancialAnalysisLayer

analysis = FinancialAnalysisLayer(user_id=123, months=3)
data = analysis.compute()  # <- Returns the dict above
```

---

## 🧠 LAYER 2: Financial Intent Layer

### Nhiệm vụ
Lớp này "diễn giải thông minh" dữ liệu raw numbers thành những câu văn mô tả bằng tiếng Việt.

### Cơ chế Rules
- Mỗi rule là một method bắt đầu với `_rule_`
- Engine tự động **discover** tất cả rules bằng `dir()` + `getattr()`
- Không cần đăng ký ở đâu cả - chỉ cần thêm method mới là rule được kích hoạt

### Ví dụ: Rule phát hiện mua sắm bốc đồng
```python
def _rule_impulsive_shopping(self):
    """Nhận diện khi người dùng mua sắm không kiểm soát"""
    cats = self.data.get('categories', {})
    
    # Tìm shopping category
    for cat_name in cats:
        if 'shopping' in cat_name.lower():
            shopping_cat = cats[cat_name]
            break
    
    if not shopping_cat:
        return None
    
    # Logic: > 20% tổng chi + xuất hiện < 8 ngày = bốc đồng
    if shopping_cat['pct_of_total'] > 20 and shopping_cat['active_days'] < 8:
        return (f"⚠️ Mua sắm: {shopping_cat['pct_of_total']}% tổng chi nhưng chỉ "
                f"{shopping_cat['active_days']} ngày → chi tiêu tập trung, không kiểm soát")
    
    return None  # Rule không trigger
```

### Tất cả Rules Hiện Tại

| Rule | Mục đích | Điều kiện |
|------|---------|----------|
| `_rule_stable_food_spending` | Chi tiêu thức ăn ổn định | > 20% + > 20 ngày |
| `_rule_impulsive_shopping` | Phát hiện mua sắm bốc đồng | > 20% + < 8 ngày |
| `_rule_entertainment_frequency` | Giải trí thường xuyên | > 10% + > 15 ngày |
| `_rule_transport_efficiency` | Vận chuyển cao → cơ hội tiết kiệm | > 15% + > 20 ngày |
| `_rule_critical_saving_rate` | 🔴 Tỷ lệ tiết kiệm < 5% | saving_rate < 5% |
| `_rule_low_saving_rate` | 🟡 Tỷ lệ tiết kiệm thấp | 5% ≤ rate ≤ 15% |
| `_rule_good_saving_rate` | 🟢 Tỷ lệ tiết kiệm tốt | 15% < rate ≤ 30% |
| `_rule_excellent_saving_rate` | 🌟 Tỷ lệ tiết kiệm xuất sắc | rate > 30% |
| `_rule_high_spending_volatility` | Chi tiêu không ổn định | std/mean > 0.3 |
| `_rule_stable_spending_pattern` | Chi tiêu ổn định | std/mean < 0.15 |
| `_rule_deficit_spending` | 🔴 Chi tiêu vượt thu nhập | balance < 0 |
| `_rule_healthy_balance` | ✓ Tình hình tài chính khỏe | 0 < balance ≤ income*0.3 |
| `_rule_top_spending_category` | Nhận diện category cao nhất | top_pct > 25% |
| `_rule_diversified_spending` | Chi tiêu đa dạng | max_pct < 30% + 3+ categories |
| `_rule_daily_spending_average` | Mức chi trung bình ngày | > 500k hoặc < 100k |

### Đầu ra
```python
insights = [
    "✓ Chi tiêu ổn định: chênh lệch giữa các tháng chỉ 450k đ → bạn có thói quen chi tiêu dự đoán được.",
    "⚠️ Mua sắm: 24.0% tổng chi nhưng chỉ 5 ngày → chi tiêu tập trung không kiểm soát.",
    "🟢 Tỷ lệ tiết kiệm 28% là tốt. Tiếp tục duy trì!",
    "📊 Chi tiêu không ổn định: độ lệch 450k đ (tương đối 30%). Gợi ý: lập ngân sách cụ thể cho từng tháng.",
]
```

### Khi nào dùng
```python
from app.chatbot.financial_intent import FinancialIntentLayer

intent = FinancialIntentLayer(financial_data)
insights = intent.detect_insights()  # <- Returns list of strings
```

---

## 🎨 LAYER 3: Prompt Engine

### Nhiệm vụ
Ghép tất cả thông tin (data, insights, history) thành **1 final prompt** sẵn sàng gửi Gemini.

### Cấu trúc 6 Blocks

```
┌─────────────────────────────────────────┐
│ BLOCK 0: SYSTEM ROLE & INSTRUCTIONS     │
│ "Bạn là trợ lý tài chính CashBrain..." │
│                                          │
│ Định nghĩa vai trò, hướng dẫn hành vi   │
└─────────────────────────────────────────┘
                    ↓ SEPARATOR
┌─────────────────────────────────────────┐
│ BLOCK 1: USER CONTEXT                   │
│ Tên: Quan, Email: quan@email.com        │
│ Thời kỳ: 3 tháng gần đây                │
└─────────────────────────────────────────┘
                    ↓ SEPARATOR
┌─────────────────────────────────────────┐
│ BLOCK 2: FINANCIAL DATA (RAW NUMBERS)   │
│ • Thu nhập: 50M, Chi: 35M               │
│ • Food: 10.5M (30%, 28 ngày)            │
│ • Shopping: 8.4M (24%, 5 ngày)          │
│ • Top txn: Laptop bag 850k              │
└─────────────────────────────────────────┘
                    ↓ SEPARATOR
┌─────────────────────────────────────────┐
│ BLOCK 3: INSIGHTS (INTERPRETATIONS)     │
│ • ✓ Chi tiêu ổn định...                 │
│ • ⚠️ Mua sắm không kiểm soát...         │
│ • 🟢 Tỷ lệ tiết kiệm tốt...             │
└─────────────────────────────────────────┘
                    ↓ SEPARATOR
┌─────────────────────────────────────────┐
│ BLOCK 4: CONVERSATION HISTORY           │
│ User: "Chi tiêu của tôi thế nào?"       │
│ Assistant: "Theo dữ liệu..."            │
│                                          │
│ (Tối đa 6 messages gần nhất)             │
└─────────────────────────────────────────┘
                    ↓ SEPARATOR
┌─────────────────────────────────────────┐
│ BLOCK 5: TASK INSTRUCTION (ANCHOR)      │
│ Trả lời câu hỏi: "Tôi chi tiêu..."    │
│                                          │
│ Kéo AI về đúng hướng (anchor)            │
└─────────────────────────────────────────┘
```

### Lý do dùng Block Separator
- **Debug dễ**: Biết prompt dừng ở đâu
- **Fine-tune**: Có thể tắt/bật từng block độc lập
  ```
  # Ví dụ: tắt history để stateless
  blocks = engine.build_prompt_preview()
  blocks['history'] = ""  # Tắt history block
  ```
- **Maintain**: Mỗi block có trách nhiệm rõ ràng

### Cách dùng
```python
from app.chatbot.prompt_engine import PromptEngine

engine = PromptEngine(
    user_info={'username': 'Quan', 'email': 'quan@...'},
    financial_data=financial_data,
    insights=insights,
    history_messages=history
)

# Lấy full prompt
final_prompt = engine.build_prompt("Tôi chi tiêu bao nhiêu cho ăn?")

# Lấy từng block riêng (debug)
blocks = engine.build_prompt_preview()
# blocks['system_role']
# blocks['financial_data']
# blocks['insights']
# ... etc
```

---

## 💾 LAYER 4: Conversation Memory

### Nhiệm vụ
Lưu trữ lịch sử hội thoại với **sliding window** để không bị vượt context limit của Gemini.

### Chiến lược
- Lưu tối đa 10 turns (1 turn = 1 user message + 1 assistant response)
- Khi vượt quá, xóa các turn cũ nhất
- Attach `financial_snapshot` vào từng user message để theo dõi thay đổi tài chính theo thời gian

### Database Schema
```python
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    role = db.Column(db.String(10))  # 'user' or 'assistant'
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    financial_snapshot = db.Column(db.JSON)  # Lưu tài chính lúc đó
```

### Ví dụ Message
```python
{
    'user_id': 123,
    'role': 'user',
    'content': 'Tôi chi tiêu bao nhiêu cho ăn uống trong tháng này?',
    'timestamp': '2026-05-12T10:30:00',
    'financial_snapshot': {
        'total_income': 50000000.0,
        'total_expense': 35000000.0,
        'balance': 15000000.0,
        'saving_rate': 30.0,
        # ... other summary data
    }
}
```

### Cách dùng
```python
from app.chatbot.conversation_memory import ConversationMemory

memory = ConversationMemory(user_id=123)

# Lấy lịch sử
history = memory.load_history()  # <- list of dicts

# Thêm message
memory.add_message(
    role='user',
    content='Tôi chi tiêu bao nhiêu?',
    snapshot=financial_data['summary']
)

# Xóa history
memory.clear_history()
```

---

## 🚀 API ENDPOINTS

### 1. **POST /api/chat/message** (Main Endpoint)
Gửi tin nhắn, nhận final prompt, tự động lưu memory.

**Request:**
```json
{
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "months": 3  // optional
}
```

**Response:**
```json
{
    "status": "success",
    "final_prompt": "Bạn là trợ lý tài chính...\n\n── ... ── \n\n...",
    "financial_summary": {
        "total_income": 50000000,
        "total_expense": 35000000,
        "balance": 15000000,
        "saving_rate": 30.0
    },
    "insights": [
        "✓ Chi tiêu ổn định...",
        "🟢 Tỷ lệ tiết kiệm tốt..."
    ],
    "insights_count": 2,
    "history_count": 5,
    "timestamp": "2026-05-12T10:30:00"
}
```

### 2. **POST /api/chat/prompt-preview** (Debug Only)
Xem prompt một lần mà không lưu memory.

**Request:** Tương tự /message
**Response:** Tương tự /message nhưng `"status": "preview_only"`

### 3. **GET /api/chat/history**
Xem lịch sử hội thoại.

**Response:**
```json
{
    "status": "success",
    "message_count": 5,
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        // ...
    ],
    "max_turns": 10
}
```

### 4. **DELETE /api/chat/history**
Xóa toàn bộ history (reset conversation).

### 5. **GET /api/chat/financial-debug**
Debug: Xem raw financial data.

**Query Params:**
- `months=3` (optional)

**Response:**
```json
{
    "status": "debug",
    "data": { /* full financial_data dict */ }
}
```

### 6. **POST /api/chat/prompt-blocks**
Advanced debug: Xem từng block của prompt riêng biệt.

**Response:**
```json
{
    "status": "prompt_blocks_debug",
    "blocks": {
        "system_role": "...",
        "user_context": "...",
        "financial_data": "...",
        "insights": "...",
        "history": "...",
        "timestamp": "2026-05-12T10:30:00"
    },
    "full_prompt": "...",
    "full_prompt_length": 2456
}
```

---

## 🧪 Testing Examples

### Example 1: Xem Financial Analysis
```bash
curl -X GET "http://localhost:5000/api/chat/financial-debug?months=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Example 2: Gửi tin nhắn
```bash
curl -X POST "http://localhost:5000/api/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "months": 3
  }'
```

### Example 3: Debug prompt blocks
```bash
curl -X POST "http://localhost:5000/api/chat/prompt-blocks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi chi tiêu bao nhiêu?",
    "months": 3
  }'
```

---

## 🔄 Workflow Tổng Thể

```
1. User: "Tôi chi tiêu bao nhiêu cho ăn uống?"
                           ↓
2. API nhận request (/api/chat/message)
                           ↓
3. Financial Analysis Layer:
   - Query Expense WHERE user_id=123 AND category LIKE '%food%'
   - Calculate sum, avg, std
   - Output: {'food': {'total': 10.5M, 'pct': 30%, ...}, ...}
                           ↓
4. Financial Intent Layer:
   - Áp dụng _rule_stable_food_spending
   - Output: ["✓ Chi tiêu thức ăn ổn định..."]
                           ↓
5. Prompt Engine:
   - Ghép 6 blocks
   - Output: Full prompt 2000+ characters
                           ↓
6. API Response:
   - Trả về final_prompt, financial_summary, insights
   - Lưu user message + snapshot vào ChatHistory
                           ↓
7. Developer:
   - Copy final_prompt
   - Gửi Gemini API
   - Nhận response từ Gemini
   - Gọi /api/chat/message lần nữa để lưu assistant response
                           ↓
8. Next turn:
   - Lịch sử được load từ ChatHistory (sliding window)
   - Đưa vào prompt block 4
   - Gemini có context về hội thoại trước đó
```

---

## 📝 Tuning & Customization

### Thay đổi số cơ sở
```python
# Trong financial_intent.py
def _rule_impulsive_shopping(self):
    # Hiện tại: > 20% và < 8 ngày
    if shopping_cat['pct_of_total'] > 20 and shopping_cat['active_days'] < 8:
        # Thay đổi thành: > 30% và < 5 ngày
        # if shopping_cat['pct_of_total'] > 30 and shopping_cat['active_days'] < 5:
```

### Thêm rule mới
```python
# Trong financial_intent.py, thêm method mới:
def _rule_healthcare_alert(self):
    """Cảnh báo khi chi phí y tế cao"""
    cats = self.data.get('categories', {})
    
    for cat_name in cats:
        if 'health' in cat_name.lower() or 'medical' in cat_name.lower():
            health_cat = cats[cat_name]
            if health_cat['pct_of_total'] > 15:
                return f"🏥 Chi phí y tế: {health_cat['pct_of_total']}% - Hãy cân nhắc bảo hiểm."
    
    return None

# Rule tự động được discover - không cần đăng ký!
```

### Tắt history (stateless mode)
```python
# Trong prompt_engine.py
def build_prompt(self, current_user_message):
    blocks = []
    # ... build other blocks ...
    
    # Comment out history block
    # blocks.append(self._build_history_block())
    
    # ... build task block ...
```

---

## 🎯 Future Enhancements

1. **Gemini API Integration**
   - Replace `final_prompt` -> Gemini API call
   - Save Gemini response to ChatHistory
   - Add streaming support

2. **Memory Tracking**
   - Analyze financial_snapshots over time
   - Track saving rate trend
   - Predict spending patterns

3. **Multi-turn Reasoning**
   - Use Gemini's system instructions
   - Add follow-up questions

4. **Feedback Loop**
   - Rate assistant responses
   - Improve rules based on user feedback

---

## 📚 File Structure

```
app/chatbot/
├── __init__.py                    # Module documentation
├── routes.py                      # API endpoints
├── financial_analysis.py          # Layer 1: Raw numbers
├── financial_intent.py            # Layer 2: Rules & insights
├── prompt_engine.py               # Layer 3: Prompt assembly
├── conversation_memory.py         # Layer 4: History storage
└── models.py                      # ChatHistory database model
```

---

## ✅ Checklist trước khi deploy

- [ ] Financial Analysis queries chính xác
- [ ] Tất cả rules được test
- [ ] Prompt blocks rõ ràng
- [ ] History sliding window hoạt động
- [ ] JWT authentication bảo mật
- [ ] Error handling đầy đủ
- [ ] Database migration done
- [ ] API documentation cập nhật
- [ ] Test API endpoints với data thực

---

## 🤝 Support

Nếu có issues, debug bằng cách:

1. Xem `/api/chat/financial-debug` → kiểm tra raw numbers
2. Xem `/api/chat/prompt-blocks` → kiểm tra từng block
3. Check ChatHistory table → verify lưu trữ đúng
4. Run `/api/chat/insights` → verify rules trigger đúng

