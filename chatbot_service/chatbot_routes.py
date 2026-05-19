"""
Chatbot Routes - API endpoints cho AI Chatbot có tích hợp Gemini API

Endpoints:
1. POST /api/chat/message           - Gửi tin nhắn (gọi Gemini + lưu memory)
2. POST /api/chat/prompt-preview    - Preview prompt & test Gemini (không lưu memory)
3. GET  /api/chat/history           - Xem lịch sử hội thoại
4. DELETE /api/chat/history         - Xóa lịch sử
5. GET  /api/chat/financial-debug   - Debug: xem raw financial data
6. POST /api/chat/financial-debug   - Debug: xem raw financial data + insights
7. GET  /api/chat/insights          - Debug: chỉ xem insights
"""

# chatbot/routes.py
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from google import genai
from google.genai import types

from auth_service.user_model import User   # Giả định User đã chuyển sang MongoEngine
from .financial_analysis import FinancialAnalysisLayer
from .financial_intent import FinancialIntentLayer
from .prompt_engine import PromptEngine
from .conversation_memory import ConversationMemory
from dotenv import load_dotenv

load_dotenv()


chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chat')

# Gemini config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)  # Hoặc dùng key từ env
GEMINI_MODEL = "gemini-2.5-flash"

# ============================================================================
# 1. MAIN ENDPOINT: /api/chat/message (POST)
# ============================================================================

@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def chat_message():
    try:
        if not GEMINI_API_KEY:
            return jsonify({'error': 'Gemini API Key is missing'}), 500

        user_id = get_jwt_identity()
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Lấy user info (MongoEngine)
        user_info = User.objects(id=user_id).first()
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

        # Lưu tin nhắn user trước
        memory.add_message('user', user_message, snapshot=financial_data['summary'])

        # Gọi Gemini
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=final_prompt,
            config=types.GenerateContentConfig(temperature=0.6)
        )
        ai_response = response.text

        memory.add_message('assistant', ai_response, snapshot=financial_data['summary'])

        return jsonify({
            'status': 'success',
            'user_message': user_message,
            'ai_response': ai_response,
            'financial_summary': financial_data['summary'],
            'insights': insights,
            'insights_count': len(insights),
            'history_count': len(history) + 2,
            'timestamp': datetime.today().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 2. PREVIEW ENDPOINT
# ============================================================================

@chatbot_bp.route('/prompt-preview', methods=['POST'])
@jwt_required()
def prompt_preview():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        user_info = User.objects(id=user_id).first()
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

        ai_preview_response = "Gemini Key Not Configured"
        if GEMINI_API_KEY:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=final_prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            ai_preview_response = response.text

        return jsonify({
            'status': 'preview_only',
            'message': user_message,
            'final_prompt': final_prompt,
            'ai_preview_response': ai_preview_response,
            'prompt_length': len(final_prompt),
            'financial_summary': financial_data['summary'],
            'insights': insights,
            'insights_count': len(insights),
            'note': 'This preview does NOT save to conversation history'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ============================================================================
# 3. HISTORY ENDPOINTS
# ============================================================================

@chatbot_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    try:
        user_id = get_jwt_identity()
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
    try:
        user_id = get_jwt_identity()
        memory = ConversationMemory(user_id)
        memory.clear_history()
        return jsonify({'status': 'success', 'message': 'Conversation history cleared'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 4. DEBUG ENDPOINTS (giữ nguyên logic, chỉ sửa truy vấn user nếu cần)
# ============================================================================

@chatbot_bp.route('/financial-debug', methods=['GET'])
@jwt_required()
def financial_debug_get():
    try:
        user_id = get_jwt_identity()
        months = request.args.get('months', 3, type=int)
        analysis = FinancialAnalysisLayer(user_id, months=months)
        financial_data = analysis.compute()
        return jsonify({'status': 'debug', 'user_id': user_id, 'data': financial_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/financial-debug', methods=['POST'])
@jwt_required()
def financial_debug_with_insights():
    try:
        user_id = get_jwt_identity()
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
            'insights_count': len(insights)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    try:
        user_id = get_jwt_identity()
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


@chatbot_bp.route('/prompt-blocks', methods=['POST'])
@jwt_required()
def prompt_blocks_debug():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        months = data.get('months', 3)

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        user_info = User.objects(id=user_id).first()
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

        blocks = engine.build_prompt_preview()
        full_prompt = engine.build_prompt(user_message)

        return jsonify({
            'status': 'prompt_blocks_debug',
            'user_id': user_id,
            'message': user_message,
            'blocks': blocks,
            'full_prompt': full_prompt,
            'full_prompt_length': len(full_prompt)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'chatbot',
        'gemini_configured': GEMINI_API_KEY is not None,
        'timestamp': datetime.today().isoformat()
    }), 200