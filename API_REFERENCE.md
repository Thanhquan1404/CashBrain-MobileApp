# API REFERENCE - CashBrain Chatbot

## Base URL
```
http://localhost:5000/api/chat
```

## Authentication
All endpoints except `/health` require JWT token in header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Endpoints

### 1. Health Check
**No authentication required**

```
GET /health
```

**Response (200 OK):**
```json
{
    "status": "healthy",
    "service": "chatbot",
    "timestamp": "2026-05-12T10:30:00.123456"
}
```

---

### 2. Send Message & Get Prompt
**Main endpoint - persists to history**

```
POST /message
```

**Request:**
```json
{
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "months": 3
}
```

**Parameters:**
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| message | string | Yes | - | User's question/message |
| months | integer | No | 3 | Analysis period in months |

**Response (200 OK):**
```json
{
    "status": "success",
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "final_prompt": "Bạn là trợ lý tài chính...\n\n────\n\n...",
    "financial_summary": {
        "total_income": 50000000.0,
        "total_expense": 35000000.0,
        "balance": 15000000.0,
        "saving_rate": 30.0,
        "avg_monthly_expense": 5833333.33,
        "std_monthly_expense": 458333.33,
        "daily_avg_expense": 194444.44
    },
    "insights": [
        "✓ Chi tiêu ổn định: chênh lệch giữa các tháng chỉ 450k đ",
        "⚠️ Mua sắm: 24.0% tổng chi nhưng chỉ 5 ngày",
        "🟢 Tỷ lệ tiết kiệm 28% là tốt"
    ],
    "insights_count": 3,
    "history_count": 5,
    "timestamp": "2026-05-12T10:30:00.123456"
}
```

**Error (400 Bad Request):**
```json
{
    "error": "Message is required"
}
```

**Error (404 Not Found):**
```json
{
    "error": "User not found"
}
```

---

### 3. Prompt Preview (No Save)
**Preview prompt without persisting message to history**

```
POST /prompt-preview
```

**Request:**
```json
{
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "months": 3
}
```

**Response (200 OK):**
```json
{
    "status": "preview_only",
    "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
    "final_prompt": "...",
    "prompt_length": 2456,
    "financial_summary": {...},
    "insights": [...],
    "insights_count": 3,
    "note": "This preview does NOT save to conversation history"
}
```

---

### 4. Get Conversation History

```
GET /history
```

**Query Parameters:** None

**Response (200 OK):**
```json
{
    "status": "success",
    "message_count": 5,
    "messages": [
        {
            "role": "user",
            "content": "Tôi chi tiêu bao nhiêu?"
        },
        {
            "role": "assistant",
            "content": "Theo dữ liệu của bạn..."
        }
    ],
    "max_turns": 10
}
```

**Note:** Returns sliding window of max 20 messages (10 turns × 2)

---

### 5. Clear Conversation History

```
DELETE /history
```

**Response (200 OK):**
```json
{
    "status": "success",
    "message": "Conversation history cleared"
}
```

---

### 6. Financial Analysis Debug (GET)
**Raw financial numbers without insights**

```
GET /financial-debug?months=3
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| months | integer | 3 | Analysis period |

**Response (200 OK):**
```json
{
    "status": "debug",
    "user_id": 1,
    "data": {
        "user_id": 1,
        "period_months": 3,
        "analysis_date": "2026-05-12T10:30:00.123456",
        "summary": {
            "total_income": 50000000.0,
            "total_expense": 35000000.0,
            "balance": 15000000.0,
            "saving_rate": 30.0,
            "avg_monthly_expense": 5833333.33,
            "std_monthly_expense": 458333.33,
            "daily_avg_expense": 194444.44
        },
        "categories": {
            "Food": {
                "total": 10500000.0,
                "count": 180,
                "active_days": 28,
                "pct_of_total": 30.0,
                "avg_per_day": 375000.0
            },
            "Shopping": {
                "total": 8400000.0,
                "count": 12,
                "active_days": 5,
                "pct_of_total": 24.0,
                "avg_per_day": 1680000.0
            }
        },
        "monthly_breakdown": [
            {
                "year": 2026,
                "month": 3,
                "total": 5800000.0,
                "active_days": 31
            }
        ],
        "top_transactions": [
            {
                "amount": 850000.0,
                "category": "Shopping",
                "date": "2026-05-10",
                "note": "Laptop bag"
            }
        ]
    }
}
```

---

### 7. Financial Analysis + Insights
**Raw numbers with detected insights**

```
POST /financial-debug
```

**Request:**
```json
{
    "months": 3
}
```

**Response (200 OK):**
```json
{
    "status": "debug",
    "user_id": 1,
    "financial_data": {
        ...same as GET /financial-debug...
    },
    "insights": [
        "✓ Chi tiêu ổn định...",
        "⚠️ Mua sắm không kiểm soát..."
    ],
    "insights_count": 2,
    "rules_executed": [
        "_rule_stable_food_spending",
        "_rule_impulsive_shopping",
        "_rule_high_spending_volatility",
        ...
    ]
}
```

---

### 8. Insights Only
**Get only insights without full financial data**

```
GET /insights?months=3
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| months | integer | 3 | Analysis period |

**Response (200 OK):**
```json
{
    "status": "insights_only",
    "user_id": 1,
    "insights": [
        "✓ Chi tiêu ổn định: chênh lệch giữa các tháng chỉ 450k đ",
        "⚠️ Mua sắm: 24.0% tổng chi nhưng chỉ 5 ngày",
        "🟢 Tỷ lệ tiết kiệm 28% là tốt",
        "📊 Chi tiêu không ổn định: độ lệch 450k đ (tương đối 30%)"
    ],
    "insights_count": 4
}
```

---

### 9. Prompt Blocks Debug
**View individual prompt blocks**

```
POST /prompt-blocks
```

**Request:**
```json
{
    "message": "Tôi chi tiêu bao nhiêu?",
    "months": 3
}
```

**Response (200 OK):**
```json
{
    "status": "prompt_blocks_debug",
    "user_id": 1,
    "message": "Tôi chi tiêu bao nhiêu?",
    "blocks": {
        "system_role": "Bạn là trợ lý tài chính cá nhân...",
        "user_context": "[USER CONTEXT]\nTên: Quan\nEmail: quan@...",
        "financial_data": "[FINANCIAL DATA - RAW NUMBERS]\n📊 TÓM:\n...",
        "insights": "[INSIGHTS - INTELLIGENT INTERPRETATIONS]\n💡 Phát hiện 3 insight:\n...",
        "history": "[CONVERSATION HISTORY]\nLịch sử 4 tin nhắn gần nhất:\n...",
        "timestamp": "2026-05-12T10:30:00.123456"
    },
    "full_prompt": "Bạn là trợ lý tài chính...\n────────...",
    "full_prompt_length": 2456
}
```

---

## Response Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Request successful |
| 400 | Bad Request | Missing required params (e.g., message) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | User not found or endpoint doesn't exist |
| 500 | Server Error | Unexpected error (check server logs) |

---

## Data Types

### Financial Summary Object
```typescript
{
    total_income: number,           // VND
    total_expense: number,          // VND
    balance: number,                // VND (can be negative)
    saving_rate: number,            // % (e.g., 30.5)
    avg_monthly_expense: number,    // VND
    std_monthly_expense: number,    // VND (standard deviation)
    daily_avg_expense: number       // VND
}
```

### Category Info Object
```typescript
{
    total: number,                  // VND
    count: number,                  // Transaction count
    active_days: number,            // Days with transactions
    pct_of_total: number,           // % of total expense
    avg_per_day: number             // VND per active day
}
```

### Message Object
```typescript
{
    role: "user" | "assistant",
    content: string,
    timestamp?: string,             // ISO format
    financial_snapshot?: object     // Financial data at time
}
```

---

## Common Use Cases

### UC1: Get final prompt to send Gemini
```bash
curl -X POST "http://localhost:5000/api/chat/message" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "...", "months": 3}'

# Extract: response.final_prompt
# Send to Gemini API
```

### UC2: Check what insights trigger
```bash
curl -X GET "http://localhost:5000/api/chat/insights?months=3" \
  -H "Authorization: Bearer TOKEN"

# See: response.insights array
```

### UC3: Debug why prompt looks wrong
```bash
curl -X POST "http://localhost:5000/api/chat/prompt-blocks" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "..."}'

# See: response.blocks (each block separately)
```

### UC4: Test without polluting history
```bash
curl -X POST "http://localhost:5000/api/chat/prompt-preview" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "..."}'

# Note: This doesn't save to history
```

### UC5: Get raw financial numbers
```bash
curl -X GET "http://localhost:5000/api/chat/financial-debug?months=6" \
  -H "Authorization: Bearer TOKEN"

# See: response.data (no insights, just numbers)
```

---

## Rate Limiting
Currently: **No rate limiting** (add if needed)

---

## Pagination
Currently: **No pagination** (all results returned)

---

## Versioning
Current API Version: **v1** (implicit, not in URL)

---

## Future Endpoints (Planned)

```
POST /gemini-response       # Save Gemini response
POST /feedback              # User feedback on response
GET /analytics              # Analytics dashboard
POST /settings              # User chatbot settings
```

