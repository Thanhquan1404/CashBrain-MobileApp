# chatbot/prompt_engine.py
"""
Prompt Engine - Kiến trúc sư của prompt

Nhiệm vụ:
- Nhận 5 nguồn input khác nhau
- Ghép thành 6 block rõ ràng ngăn cách bởi separator ───
- Mỗi block có thể tắt độc lập để fine-tune

Lý do dùng block separator:
- Khi fine-tune, có thể tắt từng block (ví dụ tắt history nếu muốn stateless)
- Dễ debug: biết prompt stop ở đâu
- Dễ maintain: mỗi block trách nhiệm rõ ràng

Block cuối cùng (Task Instruction) luôn là anchor - kéo AI về đúng nhiệm vụ
"""
from datetime import datetime
import json

class PromptEngine:
    # Separator để dễ debug và fine-tune
    SEPARATOR = "─" * 60
    
    def __init__(self, user_info, financial_data, insights, history_messages):
        """
        Args:
            user_info: dict với 'username', 'email'
            financial_data: dict từ FinancialAnalysisLayer.compute()
            insights: list từ FinancialIntentLayer.detect_insights()
            history_messages: list của {'role': 'user'/'assistant', 'content': str}
        """
        self.user_info = user_info
        self.financial_data = financial_data
        self.insights = insights or []
        self.history_messages = history_messages or []

    def build_prompt(self, current_user_message):
        """
        Xây dựng final prompt bằng cách ghép 6 blocks
        Returns: string chứa full prompt sẵn sàng gửi Gemini
        """
        blocks = []

        # === BLOCK 0: System Role ===
        blocks.append(self._build_system_role_block())

        # === BLOCK 1: User Context ===
        blocks.append(self._build_user_context_block())

        # === BLOCK 2: Financial Data (Raw Numbers) ===
        blocks.append(self._build_financial_data_block())

        # === BLOCK 3: Insights (Interpretations) ===
        blocks.append(self._build_insights_block())

        # === BLOCK 4: Conversation History ===
        blocks.append(self._build_history_block())

        # === BLOCK 5: Task Instruction (Anchor) ===
        blocks.append(self._build_task_instruction_block(current_user_message))

        # Ghép tất cả bằng separator
        full_prompt = f"\n\n{self.SEPARATOR}\n\n".join(blocks)
        return full_prompt

    def _build_system_role_block(self):
        """Block 0: Định nghĩa vai trò của AI"""
        return (
            "SYSTEM ROLE & INSTRUCTIONS:\n"
            "Bạn là 'CashBrain' - trợ lý tài chính cá nhân thân thiện và chuyên nghiệp.\n"
            "Bạn am hiểu quản lý chi tiêu, lập kế hoạch tài chính, và giúp người dùng đạt mục tiêu tiết kiệm.\n\n"
            "Hướng dẫn hành vi:\n"
            "- Nói chuyện bằng tiếng Việt, tự nhiên và thân thiện\n"
            "- Luôn dựa vào dữ liệu thực tế (financial_data) để trả lời\n"
            "- Nếu hỏi về con số không có, hãy lịch sự thông báo 'tôi không có dữ liệu này'\n"
            "- Đưa ra lời khuyên xây dựng nếu phù hợp với ngữ cảnh\n"
            "- Nếu người dùng hỏi ngoài lĩnh vực tài chính, hãy duyệt chối lịch sự\n"
            f"- Hôm nay là {datetime.today().strftime('%d/%m/%Y %H:%M')}"
        )

    def _build_user_context_block(self):
        """Block 1: Thông tin người dùng"""
        username = self.user_info.get('username', 'Bạn')
        email = self.user_info.get('email', 'N/A')
        
        return (
            "[USER CONTEXT]\n"
            f"Tên: {username}\n"
            f"Email: {email}\n"
            f"Thời kỳ phân tích: {self.financial_data.get('period_months', 6)} tháng gần đây"
        )

    def _build_financial_data_block(self):
        """Block 2: Dữ liệu tài chính thô (con số)"""
        summary = self.financial_data.get('summary', {})
        categories = self.financial_data.get('categories', {})
        
        lines = ["[FINANCIAL DATA - RAW NUMBERS]"]
        
        # Summary stats
        lines.append("📊 TÓMED:\n")
        lines.append(f"  • Thu nhập: {summary.get('total_income', 0):,.0f}đ")
        lines.append(f"  • Chi tiêu: {summary.get('total_expense', 0):,.0f}đ")
        lines.append(f"  • Dư/Nợ: {summary.get('balance', 0):,.0f}đ")
        lines.append(f"  • Tỷ lệ tiết kiệm: {summary.get('saving_rate', 0):.1f}%")
        lines.append(f"  • Chi trung bình/tháng: {summary.get('avg_monthly_expense', 0):,.0f}đ")
        lines.append(f"  • Độ lệch chuẩn: {summary.get('std_monthly_expense', 0):,.0f}đ")
        lines.append(f"  • Chi trung bình/ngày: {summary.get('daily_avg_expense', 0):,.0f}đ")
        
        # Category breakdown
        if categories:
            lines.append("\n💰 CHI TIÊU THEO CATEGORY:\n")
            for cat_name, cat_info in sorted(categories.items(), 
                                             key=lambda x: x[1]['pct_of_total'], 
                                             reverse=True):
                lines.append(
                    f"  • {cat_name}: {cat_info['total']:,.0f}đ "
                    f"({cat_info['pct_of_total']}%, {cat_info['active_days']} ngày hoạt động)"
                )
        
        # Top transactions
        top_txns = self.financial_data.get('top_transactions', [])
        if top_txns:
            lines.append("\n🔝 TOP TRANSACTIONS:\n")
            for i, txn in enumerate(top_txns[:5], 1):
                lines.append(
                    f"  {i}. {txn.get('category', 'N/A')}: {txn.get('amount', 0):,.0f}đ "
                    f"({txn.get('date', 'N/A')})"
                )
        
        return "\n".join(lines)

    def _build_insights_block(self):
        """Block 3: Insights - diễn giải thông minh"""
        lines = ["[INSIGHTS - INTELLIGENT INTERPRETATIONS]"]
        
        if not self.insights:
            lines.append("💭 Chưa có insights đặc biệt. Dữ liệu tài chính bình thường.")
        else:
            lines.append(f"💡 Phát hiện {len(self.insights)} insight:\n")
            for i, insight in enumerate(self.insights, 1):
                lines.append(f"  {i}. {insight}")
        
        return "\n".join(lines)

    def _build_history_block(self):
        """Block 4: Lịch sử hội thoại (sliding window)"""
        lines = ["[CONVERSATION HISTORY]"]
        
        if not self.history_messages:
            lines.append("Đây là tin nhắn đầu tiên trong cuộc hội thoại.")
        else:
            # Lấy tối đa 6 tin nhắn gần nhất (3 cặp user-assistant)
            history_window = self.history_messages[-6:]
            lines.append(f"Lịch sử {len(history_window)} tin nhắn gần nhất:\n")
            
            for msg in history_window:
                role = "👤 User" if msg['role'] == 'user' else "🤖 Assistant"
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                lines.append(f"{role}: {content}")
        
        return "\n".join(lines)

    def _build_task_instruction_block(self, current_user_message):
        """Block 5: Task Instruction - Anchor để kéo AI về đúng hướng"""
        lines = [
            "[TASK INSTRUCTION - RESPOND NOW]",
            "",
            "Dựa trên tất cả thông tin trên, hãy:",
            "1. Trả lời câu hỏi của người dùng một cách tự nhiên và hữu ích",
            "2. Tham khảo dữ liệu và insights nếu liên quan",
            "3. Nếu không có dữ liệu, hãy thay thế = 'không tìm thấy dữ liệu'",
            "4. Nếu hỏi ngoài lĩnh vực tài chính, duyệt chối lịch sự",
            "5. Trả lời NGẮN GỌN (1-3 câu nếu có thể), tránh dài dòng",
            "6. Sử dụng emoji để làm cho response sinh động",
            "",
            f"Câu hỏi của người dùng:\n\"{current_user_message}\"",
            "",
            "🤖 Câu trả lời:"
        ]
        
        return "\n".join(lines)

    def build_prompt_preview(self):
        """
        Trả về dict chứa từng block riêng biệt (hữu ích cho debugging)
        """
        return {
            'system_role': self._build_system_role_block(),
            'user_context': self._build_user_context_block(),
            'financial_data': self._build_financial_data_block(),
            'insights': self._build_insights_block(),
            'history': self._build_history_block(),
            'timestamp': datetime.today().isoformat()
        }