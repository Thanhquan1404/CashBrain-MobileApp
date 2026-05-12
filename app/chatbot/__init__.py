# chatbot/__init__.py
"""
CashBrain AI Chatbot Module

Kiến trúc 4 lớp:
1. FinancialAnalysisLayer: Tính toán số học thuần túy
2. FinancialIntentLayer: Áp dụng luật để tạo insights
3. PromptEngine: Ghép insights thành prompt 6 blocks
4. ConversationMemory: Lưu trữ lịch sử với sliding window

API Endpoints:
- POST /api/chat/message: Gửi tin nhắn (lưu memory)
- POST /api/chat/prompt-preview: Xem prompt (không lưu)
- GET /api/chat/history: Xem lịch sử
- DELETE /api/chat/history: Xóa lịch sử
- GET /api/chat/financial-debug: Debug financial data
- POST /api/chat/prompt-blocks: Debug prompt blocks
"""
