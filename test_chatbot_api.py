#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_chatbot_api.py

Script để test API chatbot - chạy trước khi deploy

Usage:
    python test_chatbot_api.py <jwt_token> <user_id> [months]

Example:
    python test_chatbot_api.py "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." 1 3

Prerequisites:
    - Backend running on http://localhost:5000
    - User có ít nhất 10 expense entries
    - JWT token có trong environment hoặc pass as argument
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:5000"
API_VERSION = "v1"

# ANSI colors for pretty printing
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(msg: str):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def print_info(msg: str):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


class ChatbotTester:
    def __init__(self, jwt_token: str, user_id: int, months: int = 3):
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.months = months
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to API"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed: {e}")
            return None

    def test_health_check(self):
        """Test: Health check endpoint"""
        print_section("TEST 1: Health Check")
        
        response = requests.get(f"{BASE_URL}/api/chat/health")
        
        if response.status_code == 200:
            print_success("Health check passed")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print_error(f"Health check failed: {response.status_code}")

    def test_financial_debug(self):
        """Test: GET /api/chat/financial-debug"""
        print_section("TEST 2: Financial Analysis Debug (GET)")
        
        print_info(f"Fetching financial data for user {self.user_id} ({self.months} months)")
        
        response = self._make_request("GET", f"/api/chat/financial-debug?months={self.months}")
        
        if response:
            print_success("Financial data retrieved")
            
            data = response.get('data', {})
            summary = data.get('summary', {})
            
            print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
            print(f"  • Total Income: {summary.get('total_income', 0):,.0f} VND")
            print(f"  • Total Expense: {summary.get('total_expense', 0):,.0f} VND")
            print(f"  • Balance: {summary.get('balance', 0):,.0f} VND")
            print(f"  • Saving Rate: {summary.get('saving_rate', 0):.1f}%")
            print(f"  • Daily Average: {summary.get('daily_avg_expense', 0):,.0f} VND")
            
            categories = data.get('categories', {})
            if categories:
                print(f"\n{Colors.BOLD}Categories:{Colors.ENDC}")
                for cat_name, cat_info in sorted(categories.items(), 
                                               key=lambda x: x[1]['pct_of_total'], 
                                               reverse=True)[:5]:
                    print(f"  • {cat_name}: {cat_info['total']:,.0f} VND "
                          f"({cat_info['pct_of_total']}%, {cat_info['active_days']} days)")
        else:
            print_error("Failed to fetch financial data")

    def test_insights(self):
        """Test: GET /api/chat/insights"""
        print_section("TEST 3: Insights Only")
        
        print_info("Fetching insights...")
        
        response = self._make_request("GET", f"/api/chat/insights?months={self.months}")
        
        if response:
            insights = response.get('insights', [])
            print_success(f"{len(insights)} insights detected")
            
            if insights:
                print(f"\n{Colors.BOLD}Insights:{Colors.ENDC}")
                for i, insight in enumerate(insights, 1):
                    print(f"  {i}. {insight}")
            else:
                print_warning("No insights detected - data might be too sparse")
        else:
            print_error("Failed to fetch insights")

    def test_message_endpoint(self, message: str):
        """Test: POST /api/chat/message"""
        print_section("TEST 4: Main Chat Endpoint (Message)")
        
        print_info(f"Sending message: '{message}'")
        
        payload = {
            "message": message,
            "months": self.months
        }
        
        response = self._make_request("POST", "/api/chat/message", payload)
        
        if response:
            print_success("Message sent and processed")
            
            status = response.get('status')
            print(f"\n  Status: {status}")
            print(f"  Insights: {response.get('insights_count', 0)}")
            print(f"  History: {response.get('history_count', 0)}")
            print(f"  Timestamp: {response.get('timestamp')}")
            
            # Show final prompt (truncated)
            final_prompt = response.get('final_prompt', '')
            print(f"\n{Colors.BOLD}Final Prompt (first 500 chars):{Colors.ENDC}")
            print(f"  {final_prompt[:500]}...")
            print(f"  [Total length: {len(final_prompt)} characters]")
            
            # Show insights
            insights = response.get('insights', [])
            if insights:
                print(f"\n{Colors.BOLD}Insights:{Colors.ENDC}")
                for i, insight in enumerate(insights, 1):
                    print(f"  {i}. {insight}")
        else:
            print_error("Failed to send message")

    def test_prompt_preview(self, message: str):
        """Test: POST /api/chat/prompt-preview"""
        print_section("TEST 5: Prompt Preview (No Save)")
        
        print_info(f"Previewing prompt for: '{message}'")
        
        payload = {
            "message": message,
            "months": self.months
        }
        
        response = self._make_request("POST", "/api/chat/prompt-preview", payload)
        
        if response:
            print_success("Prompt preview retrieved")
            
            status = response.get('status')
            print(f"\n  Status: {status}")
            print(f"  Note: {response.get('note', 'N/A')}")
            print(f"  Prompt Length: {response.get('prompt_length', 0)} chars")
            
            # This should match /message response
            final_prompt = response.get('final_prompt', '')
            print(f"\n{Colors.BOLD}Prompt Structure:{Colors.ENDC}")
            
            # Count blocks
            block_count = final_prompt.count('─' * 60)
            print(f"  Blocks detected: {block_count}")
        else:
            print_error("Failed to preview prompt")

    def test_prompt_blocks(self, message: str):
        """Test: POST /api/chat/prompt-blocks (Advanced Debug)"""
        print_section("TEST 6: Prompt Blocks Debug")
        
        print_info("Breaking down prompt into individual blocks...")
        
        payload = {
            "message": message,
            "months": self.months
        }
        
        response = self._make_request("POST", "/api/chat/prompt-blocks", payload)
        
        if response:
            print_success("Prompt blocks retrieved")
            
            blocks = response.get('blocks', {})
            print(f"\n{Colors.BOLD}Block Breakdown:{Colors.ENDC}")
            
            for block_name, block_content in blocks.items():
                char_count = len(block_content) if block_content else 0
                print(f"  • {block_name}: {char_count} chars")
            
            total_length = response.get('full_prompt_length', 0)
            print(f"\n  Total Prompt Length: {total_length} chars")
        else:
            print_error("Failed to retrieve prompt blocks")

    def test_history(self):
        """Test: GET /api/chat/history"""
        print_section("TEST 7: Conversation History")
        
        print_info("Fetching conversation history...")
        
        response = self._make_request("GET", "/api/chat/history")
        
        if response:
            messages = response.get('messages', [])
            max_turns = response.get('max_turns', 10)
            
            print_success(f"History retrieved")
            print(f"\n  Message Count: {len(messages)}")
            print(f"  Max Turns: {max_turns}")
            
            if messages:
                print(f"\n{Colors.BOLD}Recent Messages:{Colors.ENDC}")
                for i, msg in enumerate(messages[-4:], 1):  # Show last 4
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:80]
                    print(f"  {i}. [{role.upper()}] {content}...")
            else:
                print_warning("No messages in history yet")
        else:
            print_error("Failed to fetch history")

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════╗")
        print("║   CashBrain AI Chatbot - Test Suite   ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        print(f"Base URL: {BASE_URL}")
        print(f"User ID: {self.user_id}")
        print(f"Period: {self.months} months")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Run tests
            self.test_health_check()
            self.test_financial_debug()
            self.test_insights()
            self.test_message_endpoint("Tôi chi tiêu bao nhiêu cho ăn uống?")
            self.test_prompt_preview("Tôi chi tiêu bao nhiêu cho ăn uống?")
            self.test_prompt_blocks("Tôi chi tiêu bao nhiêu cho ăn uống?")
            self.test_history()
            
            # Summary
            print_section("TEST SUMMARY")
            print_success("All tests completed!")
            print_info("Check output above for any failures")
            
        except Exception as e:
            print_error(f"Test suite error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <jwt_token> <user_id> [months]")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} 'eyJ0eXAi...' 1 3")
        sys.exit(1)
    
    jwt_token = sys.argv[1]
    user_id = int(sys.argv[2])
    months = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    tester = ChatbotTester(jwt_token, user_id, months)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
