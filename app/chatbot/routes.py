# chatbot/routes.py
"""
Chatbot Routes - API endpoints cho AI Chatbot

Endpoints:
1. POST /api/chat/message           - Gửi tin nhắn (lưu memory)
2. POST /api/chat/prompt-preview    - Preview prompt (không lưu memory)
3. GET  /api/chat/history           - Xem lịch sử hội thoại
4. DELETE /api/chat/history         - Xóa lịch sử
5. GET  /api/chat/financial-debug   - Debug: xem raw financial data
6. POST /api/chat/financial-debug   - Debug: xem raw financial data + insights
7. GET  /api/chat/insights          - Debug: chỉ xem insights
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.user import User
from .financial_analysis import FinancialAnalysisLayer
from .financial_intent import FinancialIntentLayer
from .prompt_engine import PromptEngine
from .conversation_memory import ConversationMemory

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chat')

# ============================================================================
# 1. MAIN ENDPOINT: /api/chat/message (POST)
# ============================================================================

@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def chat_message():
    """
    Main chat endpoint - Gửi tin nhắn, nhận final prompt, lưu memory
    
    Request:
    {
        "message": "Tôi chi tiêu bao nhiêu cho ăn uống?",
        "months": 3  (optional, default=3)
    }
    
    Response:
    {
        "status": "success",
        "message_id": "uuid",
        "final_prompt": "...",
        "financial_summary": {...},
        "insights": [...],
        "history_count": 5
    }
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # 1) Lấy thông tin user
        user_info = User.query.filter_by(id=user_id).first()
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
        
        # 2) Tải lịch sử hội thoại
        memory = ConversationMemory(user_id)
        history = memory.load_history()
        
        # 3) Financial Analysis
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        # 4) Financial Intent - tạo insights
        intent = FinancialIntentLayer(financial_data)
        insights = intent.detect_insights()
        
        # 5) Tạo prompt
        engine = PromptEngine(
            user_info={'username': user_info.username, 'email': user_info.email},
            financial_data=financial_data,
            insights=insights,
            history_messages=history
        )
        final_prompt = engine.build_prompt(user_message)
        
        # 6) Lưu user message vào memory (chưa có response từ Gemini)
        # Snapshot financial data để theo dõi thay đổi theo thời gian
        memory.add_message(
            role='user',
            content=user_message,
            snapshot=financial_data['summary']
        )
        
        # 7) Trả về response
        return jsonify({
            'status': 'success',
            'message': user_message,
            'final_prompt': final_prompt,
            'financial_summary': financial_data['summary'],
            'insights': insights,
            'insights_count': len(insights),
            'history_count': len(history) + 1,  # +1 vì vừa thêm user message
            'timestamp': datetime.today().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 2. PREVIEW ENDPOINT: /api/chat/prompt-preview (POST)
# ============================================================================

@chatbot_bp.route('/prompt-preview', methods=['POST'])
@jwt_required()
def prompt_preview():
    """
    Preview endpoint - Xem final prompt MỘT LẦN không lưu memory
    
    Dùng khi developer muốn test/fine-tune prompt mà không muốn pollute history
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        user_info = User.query.filter_by(id=user_id).first()
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
        
        memory = ConversationMemory(user_id)
        history = memory.load_history()
        
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        intent = FinancialIntentLayer(financial_data)
        insights = intent.detect_insights()
        
        engine = PromptEngine(
            user_info={'username': user_info.username, 'email': user_info.email},
            financial_data=financial_data,
            insights=insights,
            history_messages=history
        )
        final_prompt = engine.build_prompt(user_message)
        
        return jsonify({
            'status': 'preview_only',
            'message': user_message,
            'final_prompt': final_prompt,
            'prompt_length': len(final_prompt),
            'financial_summary': financial_data['summary'],
            'insights': insights,
            'insights_count': len(insights),
            'note': 'This preview does NOT save to conversation history'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 3. HISTORY ENDPOINTS
# ============================================================================

@chatbot_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    Xem lịch sử hội thoại (sliding window, tối đa 20 messages)
    """
    try:
        user_id = int(get_jwt_identity())
        memory = ConversationMemory(user_id)
        history = memory.load_history()
        
        return jsonify({
            'status': 'success',
            'message_count': len(history),
            'messages': history,
            'max_turns': ConversationMemory.MAX_TURNS
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/history', methods=['DELETE'])
@jwt_required()
def delete_history():
    """
    Xóa toàn bộ lịch sử hội thoại (reset conversation)
    """
    try:
        user_id = int(get_jwt_identity())
        memory = ConversationMemory(user_id)
        memory.clear_history()
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation history cleared'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 4. DEBUG ENDPOINTS
# ============================================================================

@chatbot_bp.route('/financial-debug', methods=['GET'])
@jwt_required()
def financial_debug_get():
    """
    DEBUG: Xem raw financial analysis data (không có insights)
    
    Giúp developer kiểm tra:
    - Tính toán tổng/trung bình có đúng không
    - Category breakdown
    - Time series data
    """
    try:
        user_id = int(get_jwt_identity())
        months = request.args.get('months', 3, type=int)
        
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        return jsonify({
            'status': 'debug',
            'user_id': user_id,
            'data': financial_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/financial-debug', methods=['POST'])
@jwt_required()
def financial_debug_with_insights():
    """
    DEBUG: Xem financial data + insights (không có prompt assembly)
    
    Giúp developer:
    - Kiểm tra insights được trigger đúng không
    - Verify rule logic
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        months = data.get('months', 3)
        
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        intent = FinancialIntentLayer(financial_data)
        insights = intent.detect_insights()
        
        return jsonify({
            'status': 'debug',
            'user_id': user_id,
            'financial_data': financial_data,
            'insights': insights,
            'insights_count': len(insights),
            'rules_executed': [m for m in dir(intent) if m.startswith('_rule_')]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    """
    DEBUG: Chỉ xem insights (không có financial data)
    
    Dùng khi bạn muốn tập trung vào logic các rules
    """
    try:
        user_id = int(get_jwt_identity())
        months = request.args.get('months', 3, type=int)
        
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        intent = FinancialIntentLayer(financial_data)
        insights = intent.detect_insights()
        
        return jsonify({
            'status': 'insights_only',
            'user_id': user_id,
            'insights': insights,
            'insights_count': len(insights)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 5. PROMPT PREVIEW BREAKDOWN (Advanced Debug)
# ============================================================================

@chatbot_bp.route('/prompt-blocks', methods=['POST'])
@jwt_required()
def prompt_blocks_debug():
    """
    ADVANCED DEBUG: Xem từng block của prompt riêng biệt
    
    Dùng khi fine-tune prompt để tắt/bật từng block:
    - Block 0: System role
    - Block 1: User context
    - Block 2: Financial data
    - Block 3: Insights
    - Block 4: Conversation history
    - Block 5: Task instruction
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        user_info = User.query.filter_by(id=user_id).first()
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
        
        memory = ConversationMemory(user_id)
        history = memory.load_history()
        
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        
        intent = FinancialIntentLayer(financial_data)
        insights = intent.detect_insights()
        
        engine = PromptEngine(
            user_info={'username': user_info.username, 'email': user_info.email},
            financial_data=financial_data,
            insights=insights,
            history_messages=history
        )
        
        # build_prompt_preview trả về dict các block riêng biệt
        blocks = engine.build_prompt_preview()
        
        return jsonify({
            'status': 'prompt_blocks_debug',
            'user_id': user_id,
            'message': user_message,
            'blocks': blocks,
            'full_prompt': engine.build_prompt(user_message),
            'full_prompt_length': len(engine.build_prompt(user_message))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 6. HEALTH CHECK
# ============================================================================

@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - không cần JWT
    """
    return jsonify({
        'status': 'healthy',
        'service': 'chatbot',
        'timestamp': datetime.today().isoformat()
    }), 200