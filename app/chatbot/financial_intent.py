# chatbot/financial_intent.py
"""
Financial Intent Layer - Lớp diễn giải thông minh

Nhiệm vụ:
- Nhận dict số từ FinancialAnalysisLayer
- Áp dụng bộ luật (_rule_*) để tạo câu văn mô tả
- Mỗi luật dùng 2 chiều: magnitude (%) + frequency (ngày hoạt động)
- Tự động discover tất cả luật bằng introspection (dir())

Convention:
- Mỗi luật là method bắt đầu với _rule_
- Trả về string mô tả insight hoặc None
- Không cần đăng ký ở đâu cả
"""

class FinancialIntentLayer:
    def __init__(self, analysis_data):
        self.data = analysis_data

    def detect_insights(self):
        """Tự động gọi tất cả các rules (_rule_*) và collect insights"""
        insights = []
        for attr in dir(self):
            if attr.startswith('_rule_'):
                rule_func = getattr(self, attr)
                if callable(rule_func):
                    try:
                        result = rule_func()
                        if result:
                            insights.append(result)
                    except Exception as e:
                        # Log silently, continue
                        pass
        return insights

    # ========== RULES: Spending Patterns ==========

    def _rule_stable_food_spending(self):
        """Chi tiêu thức ăn ổn định → thói quen tốt"""
        cats = self.data.get('categories', {})
        
        # Tìm food-related categories
        food_keywords = ['food', 'thực phẩm', 'ăn', 'restaurant', 'nhà hàng', 'quán ăn', 'café']
        food_cat = None
        for cat_name in cats:
            if any(keyword in cat_name.lower() for keyword in food_keywords):
                food_cat = cats[cat_name]
                break
        
        if not food_cat:
            return None
        
        # Logic: > 20% tổng chi + xuất hiện > 20/30 ngày = ổn định
        if food_cat['pct_of_total'] > 20 and food_cat['active_days'] > 20:
            return (f"✓ Chi tiêu thức ăn: {food_cat['pct_of_total']}% tổng chi, "
                    f"phân bổ đều {food_cat['active_days']}/30 ngày → thói quen ổn định, "
                    f"nhu cầu cơ bản được đáp ứng.")
        return None

    def _rule_impulsive_shopping(self):
        """Mua sắm không kiểm soát → cảnh báo chi tiêu bốc đồng"""
        cats = self.data.get('categories', {})
        
        shopping_keywords = ['shopping', 'mua sắm', 'fashion', 'clothes', 'thời trang', 'quần áo', 'shoes', 'giày']
        shopping_cat = None
        for cat_name in cats:
            if any(keyword in cat_name.lower() for keyword in shopping_keywords):
                shopping_cat = cats[cat_name]
                break
        
        if not shopping_cat:
            return None
        
        # Logic: > 20% tổng chi + xuất hiện < 8 ngày = bốc đồng
        if shopping_cat['pct_of_total'] > 20 and shopping_cat['active_days'] < 8:
            return (f"⚠️ Mua sắm: {shopping_cat['pct_of_total']}% tổng chi nhưng chỉ {shopping_cat['active_days']} ngày → "
                    f"chi tiêu tập trung không kiểm soát. Gợi ý: lập kế hoạch chi tiêu trước.")
        return None

    def _rule_entertainment_frequency(self):
        """Giải trí thường xuyên → kiểm tra chi phí"""
        cats = self.data.get('categories', {})
        
        entertainment_keywords = ['entertainment', 'giải trí', 'movie', 'phim', 'game', 'trò chơi', 'concert', 'bar', 'pub']
        ent_cat = None
        for cat_name in cats:
            if any(keyword in cat_name.lower() for keyword in entertainment_keywords):
                ent_cat = cats[cat_name]
                break
        
        if not ent_cat:
            return None
        
        if ent_cat['pct_of_total'] > 10 and ent_cat['active_days'] > 15:
            return (f"ℹ️ Giải trí: {ent_cat['pct_of_total']}% tổng chi, {ent_cat['active_days']} ngày → "
                    f"bạn có thói quen thường xuyên. Đây có thể là dấu hiệu stress.")
        return None

    def _rule_transport_efficiency(self):
        """Chi phí vận chuyển cao → cơ hội tiết kiệm"""
        cats = self.data.get('categories', {})
        
        transport_keywords = ['transport', 'vận chuyển', 'taxi', 'grab', 'bus', 'xăng', 'petrol', 'gas', 'xe']
        transport_cat = None
        for cat_name in cats:
            if any(keyword in cat_name.lower() for keyword in transport_keywords):
                transport_cat = cats[cat_name]
                break
        
        if not transport_cat:
            return None
        
        if transport_cat['pct_of_total'] > 15 and transport_cat['active_days'] > 20:
            return (f"💡 Vận chuyển: {transport_cat['pct_of_total']}% tổng chi → xem xét "
                    f"công ty cấp xe, đi bộ, hay dùng phương tiện công cộng.")
        return None

    # ========== RULES: Saving Rate ==========

    def _rule_critical_saving_rate(self):
        """Tỷ lệ tiết kiệm < 5% → nguy cáo"""
        saving = self.data['summary']['saving_rate']
        if saving < 5:
            return (f"🔴 CẢNH BÁO: Tỷ lệ tiết kiệm chỉ {saving}% (gần như không tiết kiệm). "
                    f"Bạn cần giảm chi tiêu ngay để tránh nợ nần.")
            return True
        return None

    def _rule_low_saving_rate(self):
        """Tỷ lệ tiết kiệm 5-15% → nên cải thiện"""
        saving = self.data['summary']['saving_rate']
        if 5 <= saving <= 15:
            return (f"🟡 Tỷ lệ tiết kiệm {saving}% là thấp. "
                    f"Mục tiêu nên là 20-30%. Hãy xem lại các khoản chi không cần thiết.")
        return None

    def _rule_good_saving_rate(self):
        """Tỷ lệ tiết kiệm 15-30% → tốt"""
        saving = self.data['summary']['saving_rate']
        if 15 < saving <= 30:
            return (f"🟢 Tỷ lệ tiết kiệm {saving}% là tốt. Tiếp tục duy trì!")
        return None

    def _rule_excellent_saving_rate(self):
        """Tỷ lệ tiết kiệm > 30% → xuất sắc"""
        saving = self.data['summary']['saving_rate']
        if saving > 30:
            return (f"🌟 Tỷ lệ tiết kiệm {saving}% là xuất sắc! Bạn kiểm soát chi tiêu rất tốt.")
        return None

    # ========== RULES: Spending Volatility ==========

    def _rule_high_spending_volatility(self):
        """Độ lệch chuẩn chi tiêu cao → chi tiêu không ổn định"""
        summary = self.data['summary']
        avg = summary['avg_monthly_expense']
        std = summary['std_monthly_expense']
        
        # Hệ số biến thiên > 30% = cao
        if avg > 0 and (std / avg) > 0.3:
            return (f"📊 Chi tiêu không ổn định: độ lệch {std:.0f}đ "
                    f"(tương đối {(std/avg*100):.0f}%). "
                    f"Gợi ý: lập ngân sách cụ thể cho từng tháng.")
        return None

    def _rule_stable_spending_pattern(self):
        """Độ lệch chuẩn chi tiêu thấp → chi tiêu ổn định"""
        summary = self.data['summary']
        avg = summary['avg_monthly_expense']
        std = summary['std_monthly_expense']
        
        # Hệ số biến thiên < 15% = ổn định
        if avg > 0 and (std / avg) < 0.15:
            return (f"✓ Chi tiêu ổn định: chênh lệch giữa các tháng chỉ {std:.0f}đ → "
                    f"bạn có thói quen chi tiêu dự đoán được.")
        return None

    # ========== RULES: Income vs Expense ==========

    def _rule_deficit_spending(self):
        """Chi tiêu > thu nhập → chi tiêu vượt ngân sách"""
        balance = self.data['summary']['balance']
        income = self.data['summary']['total_income']
        
        if balance < 0:
            deficit = abs(balance)
            return (f"🔴 CHỈ SỐ NGUY: Chi tiêu vượt thu nhập {deficit:.0f}đ "
                    f"({(-balance/income*100):.1f}%). Bạn đang sống vượt khả năng!")
        return None

    def _rule_healthy_balance(self):
        """Chi tiêu < thu nhập → khỏe mạnh tài chính"""
        balance = self.data['summary']['balance']
        income = self.data['summary']['total_income']
        
        if 0 < balance <= income * 0.3:
            return (f"✓ Tình hình tài chính khỏe mạnh: dư {balance:.0f}đ. "
                    f"Tiếp tục duy trì!")
        return None

    # ========== RULES: Category Balance ==========

    def _rule_top_spending_category(self):
        """Nhận diện category chi tiêu cao nhất"""
        cats = self.data.get('categories', {})
        if not cats:
            return None
        
        top_cat = max(cats.items(), key=lambda x: x[1]['pct_of_total'])
        cat_name, cat_info = top_cat
        
        if cat_info['pct_of_total'] > 25:
            return (f"📌 {cat_name} là khoản chi cao nhất: {cat_info['pct_of_total']}% tổng chi. "
                    f"Cân nhắc xem có thể tiết kiệm ở mục này không.")
        return None

    def _rule_diversified_spending(self):
        """Chi tiêu đa dạng theo category"""
        cats = self.data.get('categories', {})
        if len(cats) < 3:
            return None
        
        # Nếu không có category nào > 30% → chi tiêu đa dạng
        max_pct = max([c['pct_of_total'] for c in cats.values()])
        if max_pct < 30:
            return (f"✓ Chi tiêu của bạn đa dạng trên {len(cats)} category. "
                    f"Điều này giúp giảm rủi ro.")
        return None

    # ========== RULES: Frequency Analysis ==========

    def _rule_daily_spending_average(self):
        """Nhận diện mức chi tiêu bình quân hàng ngày"""
        summary = self.data['summary']
        daily_avg = summary['daily_avg_expense']
        
        if daily_avg > 500000:  # > 500k/ngày
            return (f"📈 Mức chi tiêu trung bình {daily_avg:,.0f}đ/ngày. "
                    f"Hãy xem có khoản chi không cần thiết không.")
        elif daily_avg < 100000:  # < 100k/ngày
            return (f"✓ Mức chi tiêu trung bình chỉ {daily_avg:,.0f}đ/ngày → rất tiết kiệm.")
        return None