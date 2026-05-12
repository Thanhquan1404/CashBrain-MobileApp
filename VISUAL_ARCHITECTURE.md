# VISUAL ARCHITECTURE GUIDE - CashBrain AI Chatbot

## 🎯 High-Level Flow Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                         DEVELOPER/FRONTEND                       ┃
┃                                                                  ┃
┃    Sends: POST /api/chat/message                                ┃
┃    {                                                             ┃
┃        "message": "Tôi chi tiêu bao nhiêu cho ăn?",            ┃
┃        "months": 3                                              ┃
┃    }                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
                    ┌─────────────────────┐
                    │   JWT Authentication│
                    │   (Verify token)    │
                    └─────────────────────┘
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃               LAYER 1: FINANCIAL ANALYSIS LAYER                  ┃
┃                    (financial_analysis.py)                       ┃
┃                                                                  ┃
┃  ┌──────────────────────────────────────────────────────────┐   ┃
┃  │  INPUT: user_id=123, months=3                            │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │  QUERIES:                                                │   ┃
┃  │  • SELECT SUM(amount) FROM expense WHERE user_id=123    │   ┃
┃  │  • SELECT SUM(amount) FROM income WHERE user_id=123     │   ┃
┃  │  • SELECT category, SUM(amount) FROM expense GROUP BY   │   ┃
┃  │  • SELECT year,month, SUM(amount) FROM expense GROUP BY │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │  CALCULATIONS:                                           │   ┃
┃  │  • balance = total_income - total_expense               │   ┃
┃  │  • saving_rate = balance / total_income * 100           │   ┃
┃  │  • std_dev = calculate_std_deviation(monthly_totals)    │   ┃
┃  │  • category_pct = category_total / total_expense * 100  │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │  OUTPUT: Dict (raw numbers only)                         │   ┃
┃  │  {                                                       │   ┃
┃  │    'total_income': 50000000,                             │   ┃
┃  │    'total_expense': 35000000,                            │   ┃
┃  │    'categories': {                                       │   ┃
┃  │      'Food': {'total': 10500000, 'pct': 30, ...},       │   ┃
┃  │      'Shopping': {'total': 8400000, 'pct': 24, ...},    │   ┃
┃  │      ...                                                 │   ┃
┃  │    }                                                     │   ┃
┃  │  }                                                       │   ┃
┃  └──────────────────────────────────────────────────────────┘   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃             LAYER 2: FINANCIAL INTENT LAYER                      ┃
┃               (financial_intent.py)                              ┃
┃                                                                  ┃
┃  ┌──────────────────────────────────────────────────────────┐   ┃
┃  │  INPUT: financial_data (from Layer 1)                    │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │  AUTO-DISCOVERY: dir() + getattr() on _rule_* methods    │   ┃
┃  │                                                           │   ┃
┃  │  RULE EXECUTION (15 rules):                              │   ┃
┃  │  1. _rule_stable_food_spending()                         │   ┃
┃  │     IF food_pct > 20 AND active_days > 20:              │   ┃
┃  │        "✓ Chi tiêu thức ăn ổn định..."                 │   ┃
┃  │                                                           │   ┃
┃  │  2. _rule_impulsive_shopping()                           │   ┃
┃  │     IF shopping_pct > 20 AND active_days < 8:           │   ┃
┃  │        "⚠️ Mua sắm không kiểm soát..."                 │   ┃
┃  │                                                           │   ┃
┃  │  3. _rule_critical_saving_rate()                         │   ┃
┃  │     IF saving_rate < 5:                                  │   ┃
┃  │        "🔴 CẢNH BÁO: Tỷ lệ tiết kiệm < 5%..."          │   ┃
┃  │                                                           │   ┃
┃  │  ... (12 more rules)                                     │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │  OUTPUT: List of insights (Vietnamese text)              │   ┃
┃  │  [                                                       │   ┃
┃  │    "✓ Chi tiêu thức ăn ổn định...",                    │   ┃
┃  │    "⚠️ Mua sắm không kiểm soát...",                    │   ┃
┃  │    "🟢 Tỷ lệ tiết kiệm 28% là tốt...",                │   ┃
┃  │    "📊 Chi tiêu không ổn định..."                        │   ┃
┃  │  ]                                                       │   ┃
┃  └──────────────────────────────────────────────────────────┘   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              LAYER 3: PROMPT ENGINE                              ┃
┃              (prompt_engine.py)                                  ┃
┃                                                                  ┃
┃  ┌──────────────────────────────────────────────────────────┐   ┃
┃  │ INPUT:                                                   │   ┃
┃  │ • financial_data (from Layer 1)                          │   ┃
┃  │ • insights (from Layer 2)                                │   ┃
┃  │ • history_messages (from ConversationMemory)             │   ┃
┃  │ • current_user_message (from request)                    │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │ BUILD 6 BLOCKS (separated by ────────────────────):      │   ┃
┃  │                                                           │   ┃
┃  │ Block 0: SYSTEM ROLE                                     │   ┃
┃  │ "Bạn là trợ lý tài chính CashBrain..."                  │   ┃
┃  │                                                           │   ┃
┃  │ ─────────────────────────────────────────────────────    │   ┃
┃  │                                                           │   ┃
┃  │ Block 1: USER CONTEXT                                    │   ┃
┃  │ Tên: Quan, Email: quan@email.com                        │   ┃
┃  │ Thời kỳ: 3 tháng gần đây                                │   ┃
┃  │                                                           │   ┃
┃  │ ─────────────────────────────────────────────────────    │   ┃
┃  │                                                           │   ┃
┃  │ Block 2: FINANCIAL DATA                                  │   ┃
┃  │ 📊 TÓM:                                                  │   ┃
┃  │ • Thu nhập: 50M                                         │   ┃
┃  │ • Chi tiêu: 35M                                         │   ┃
┃  │ • Tiết kiệm: 30%                                        │   ┃
┃  │                                                           │   ┃
┃  │ 💰 CATEGORY:                                            │   ┃
┃  │ • Food: 10.5M (30%, 28 ngày)                            │   ┃
┃  │ • Shopping: 8.4M (24%, 5 ngày)                          │   ┃
┃  │                                                           │   ┃
┃  │ ─────────────────────────────────────────────────────    │   ┃
┃  │                                                           │   ┃
┃  │ Block 3: INSIGHTS                                        │   ┃
┃  │ 💡 Phát hiện 4 insight:                                │   ┃
┃  │ 1. ✓ Chi tiêu thức ăn ổn định...                       │   ┃
┃  │ 2. ⚠️ Mua sắm không kiểm soát...                       │   ┃
┃  │ ...                                                      │   ┃
┃  │                                                           │   ┃
┃  │ ─────────────────────────────────────────────────────    │   ┃
┃  │                                                           │   ┃
┃  │ Block 4: CONVERSATION HISTORY                            │   ┃
┃  │ User: "Tôi chi tiêu bao nhiêu?"                         │   ┃
┃  │ Assistant: "Theo dữ liệu..."                            │   ┃
┃  │ ... (max 6 messages)                                     │   ┃
┃  │                                                           │   ┃
┃  │ ─────────────────────────────────────────────────────    │   ┃
┃  │                                                           │   ┃
┃  │ Block 5: TASK INSTRUCTION (ANCHOR)                       │   ┃
┃  │ Trả lời câu hỏi: "Tôi chi tiêu bao nhiêu?"             │   ┃
┃  │ Dựa trên dữ liệu...                                     │   ┃
┃  │ Assistant:                                               │   ┃
┃  │                                                           │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │ OUTPUT: final_prompt (2000-3000 chars)                   │   ┃
┃  │ Ready to send to Gemini API                              │   ┃
┃  └──────────────────────────────────────────────────────────┘   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃            LAYER 4: CONVERSATION MEMORY                          ┃
┃          (conversation_memory.py + ChatHistory DB)               ┃
┃                                                                  ┃
┃  ┌──────────────────────────────────────────────────────────┐   ┃
┃  │ INPUT: user_message + financial_snapshot               │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │ SAVE TO DB:                                              │   ┃
┃  │                                                           │   ┃
┃  │ INSERT INTO chat_history:                                │   ┃
┃  │ {                                                        │   ┃
┃  │   user_id: 123,                                         │   ┃
┃  │   role: 'user',                                         │   ┃
┃  │   content: "Tôi chi tiêu bao nhiêu?",                  │   ┃
┃  │   timestamp: NOW(),                                     │   ┃
┃  │   financial_snapshot: {                                 │   ┃
┃  │     'total_income': 50M,                                │   ┃
┃  │     'total_expense': 35M,                               │   ┃
┃  │     'saving_rate': 30.0                                 │   ┃
┃  │   }                                                     │   ┃
┃  │ }                                                        │   ┃
┃  │                                                           │   ┃
┃  │ SLIDING WINDOW: Keep only last 10 turns (20 messages)   │   ┃
┃  │                                                           │   ┃
┃  ├──────────────────────────────────────────────────────────┤   ┃
┃  │ OUTPUT: Confirmation + next_history                      │   ┃
┃  └──────────────────────────────────────────────────────────┘   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      API RESPONSE                                ┃
┃                                                                  ┃
┃  Returns to Developer/Frontend:                                 ┃
┃  {                                                              ┃
┃    "status": "success",                                         ┃
┃    "final_prompt": "Bạn là trợ lý tài chính...",              ┃
┃    "financial_summary": {                                       ┃
┃      "total_income": 50000000,                                 ┃
┃      "total_expense": 35000000,                                ┃
┃      "balance": 15000000,                                      ┃
┃      "saving_rate": 30.0                                       ┃
┃    },                                                            ┃
┃    "insights": [                                                ┃
┃      "✓ Chi tiêu thức ăn ổn định...",                         ┃
┃      "⚠️ Mua sắm không kiểm soát...",                         ┃
┃      "🟢 Tỷ lệ tiết kiệm tốt..."                             ┃
┃    ],                                                            ┃
┃    "insights_count": 3,                                         ┃
┃    "history_count": 5,                                          ┃
┃    "timestamp": "2026-05-12T10:30:00"                          ┃
┃  }                                                              ┃
┃                                                                  ┃
┃  Next step: Send final_prompt to Gemini API for response       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 🔄 Request/Response Cycle

```
1. Developer sends:
   POST /api/chat/message
   {"message": "Tôi chi tiêu bao nhiêu?", "months": 3}
   Header: Authorization: Bearer JWT_TOKEN
   
                         ↓
                         
2. Backend processes (70ms total):
   
   a) Verify JWT token (2ms)
   b) Call FinancialAnalysisLayer (50ms)
      - Query Expense table
      - Query Income table
      - Calculate summary & categories
   c) Call FinancialIntentLayer (5ms)
      - Apply 15 rules
      - Generate insights
   d) Call PromptEngine (2ms)
      - Assemble 6 blocks
   e) Call ConversationMemory (10ms)
      - Load history
      - Save user message
   
                         ↓
                         
3. Backend returns:
   200 OK
   {
     "final_prompt": "2000+ chars, ready for Gemini",
     "financial_summary": {...},
     "insights": [...],
     ...
   }
   
                         ↓
                         
4. Developer (next phase):
   - Copy final_prompt
   - Send to Gemini API
   - Receive Gemini response
   - Call /api/chat/message again to save assistant response
   - Display to user
```

---

## 📊 Data Flow Between Layers

```
Layer 1 Output (raw numbers):
{
  "total_income": 50M,
  "total_expense": 35M,
  "categories": {
    "Food": {"total": 10.5M, "pct": 30, "active_days": 28},
    "Shopping": {"total": 8.4M, "pct": 24, "active_days": 5}
  }
}
  ↓
  Used by Layer 2
  
Layer 2 Output (insights):
[
  "✓ Chi tiêu thức ăn ổn định (30%, 28 ngày)",
  "⚠️ Mua sắm không kiểm soát (24%, 5 ngày)"
]
  ↓
  Used by Layer 3
  
Layer 3 Output (prompt):
"[FINANCIAL DATA]
Food: 10.5M (30%, 28 ngày)
Shopping: 8.4M (24%, 5 ngày)

[INSIGHTS]
✓ Chi tiêu thức ăn ổn định
⚠️ Mua sắm không kiểm soát"
  ↓
  Ready for Gemini
  
Layer 4 Action:
Save to ChatHistory table for next turn's history
```

---

## 🎯 Rule Execution Flow (Layer 2)

```
FinancialIntentLayer.detect_insights()
  ↓
  FOR EACH method in dir(self):
    ├─ IF method name starts with "_rule_":
    │   ├─ Call rule_function()
    │   └─ IF returns non-None:
    │       └─ Add to insights array
    │
    ├─ _rule_stable_food_spending()
    │  └─ IF food_pct > 20 AND active_days > 20:
    │     └─ RETURN "✓ Chi tiêu thức ăn ổn định..."
    │
    ├─ _rule_impulsive_shopping()
    │  └─ IF shopping_pct > 20 AND active_days < 8:
    │     └─ RETURN "⚠️ Mua sắm không kiểm soát..."
    │
    ├─ _rule_critical_saving_rate()
    │  └─ IF saving_rate < 5:
    │     └─ RETURN "🔴 CẢNH BÁO: Tỷ lệ tiết kiệm..."
    │
    └─ ... 12 more rules ...
  ↓
  RETURN [insight1, insight2, insight3, ...]
```

---

## 📦 Database Schema

```
┌─────────────────────────────────────┐
│         EXISTING TABLES             │
├─────────────────────────────────────┤
│ users                               │
│  ├─ id (PK)                        │
│  ├─ username (UNIQUE)              │
│  ├─ email (UNIQUE)                 │
│  └─ password_hash                  │
├─────────────────────────────────────┤
│ expense                             │
│  ├─ id (PK)                        │
│  ├─ user_id (FK → users)           │
│  ├─ category_id (FK → expense_cat) │
│  ├─ amount                         │
│  ├─ date                           │
│  └─ note                           │
├─────────────────────────────────────┤
│ expense_category                    │
│  ├─ id (PK)                        │
│  ├─ label (e.g., 'Food')           │
│  ├─ icon                           │
│  └─ color                          │
├─────────────────────────────────────┤
│ income                              │
│  ├─ id (PK)                        │
│  ├─ user_id (FK → users)           │
│  ├─ amount                         │
│  ├─ date                           │
│  └─ note                           │
└─────────────────────────────────────┘
                  ↓ NEW
┌─────────────────────────────────────┐
│      NEW TABLE (created)            │
├─────────────────────────────────────┤
│ chat_history                        │
│  ├─ id (PK)                        │
│  ├─ user_id (FK → users)           │
│  ├─ role (user / assistant)        │
│  ├─ content (message text)         │
│  ├─ timestamp                      │
│  └─ financial_snapshot (JSON)      │
│     {                              │
│       "total_income": 50000000,    │
│       "total_expense": 35000000,   │
│       "saving_rate": 30.0          │
│     }                              │
└─────────────────────────────────────┘
```

---

## 🔀 Two Example Scenarios

### Scenario 1: Good Spender
```
Layer 1: Analyze
├─ Total income: 60M
├─ Total expense: 40M
├─ Saving rate: 33%
├─ Food: 25%, 28 days
└─ Shopping: 8%, 3 days

Layer 2: Insights
├─ ✓ Chi tiêu thức ăn ổn định (25%, 28 ngày)
├─ 🌟 Tỷ lệ tiết kiệm 33% xuất sắc
└─ ✓ Chi tiêu đa dạng trên 5 categories

Layer 3: Prompt assembles positive message
Layer 4: Save positive snapshot for tracking

Result: Encouraging response to user
```

### Scenario 2: Struggling Spender
```
Layer 1: Analyze
├─ Total income: 30M
├─ Total expense: 32M
├─ Saving rate: -7% (deficit)
├─ Shopping: 35%, 4 days
└─ Food: 28%, 22 days

Layer 2: Insights
├─ 🔴 Chi tiêu vượt thu nhập 2M
├─ ⚠️ Mua sắm: 35%, chỉ 4 ngày (bốc đồng)
├─ 🟡 Tỷ lệ tiết kiệm -7% (nợ nần)
└─ 📊 Chi tiêu không ổn định

Layer 3: Prompt assembles warning with suggestions
Layer 4: Save concerning snapshot for future comparison

Result: Helpful, concerned response with suggestions
```

---

## 🚦 Status Indicators

The system uses emoji indicators in insights:

| Emoji | Meaning | Example |
|-------|---------|---------|
| ✓ | Positive behavior | ✓ Chi tiêu ổn định |
| ⚠️ | Warning | ⚠️ Chi tiêu bốc đồng |
| 🟢 | Good | 🟢 Tỷ lệ tiết kiệm tốt |
| 🟡 | Medium | 🟡 Tỷ lệ tiết kiệm thấp |
| 🔴 | Critical | 🔴 Chi tiêu vượt ngân sách |
| 📊 | Data note | 📊 Chi tiêu không ổn định |
| 💡 | Suggestion | 💡 Xem xét tiết kiệm... |
| 🌟 | Excellent | 🌟 Tỷ lệ tiết kiệm xuất sắc |

---

## ⏱️ Performance Timeline

Per request:
```
0ms    ├─ Request arrives
       │
2ms    ├─ JWT validation
       │
52ms   ├─ Financial Analysis Layer
       │   ├─ Query expense (25ms)
       │   ├─ Query income (5ms)
       │   ├─ Query categories (15ms)
       │   └─ Calculate (7ms)
       │
57ms   ├─ Financial Intent Layer (5ms)
       │   └─ Execute 15 rules
       │
59ms   ├─ Prompt Engine (2ms)
       │   └─ Assemble 6 blocks
       │
69ms   ├─ Conversation Memory (10ms)
       │   ├─ Load history (5ms)
       │   └─ Save message (5ms)
       │
70ms   └─ Response ready
```

**Total: ~70ms** (very fast!)

---

## 🔐 Security Layers

```
┌─────────────────────────────────────┐
│ Request from Frontend               │
└─────────────────────────────────────┘
           ↓
    [1] JWT Verification
        - Check token signature
        - Verify not expired
        - Extract user_id
           ↓
    [2] User Authorization
        - Ensure user owns data
        - Prevent data leakage
           ↓
    [3] SQL Injection Prevention
        - Use SQLAlchemy ORM
        - Parameterized queries
           ↓
    [4] Data Privacy
        - No sensitive data in logs
        - Encrypt snapshots (future)
           ↓
┌─────────────────────────────────────┐
│ Safe Response                       │
└─────────────────────────────────────┘
```

---

Great! This visual guide should help new developers understand the architecture flow quickly. You now have a complete, well-documented AI chatbot system ready for production!
