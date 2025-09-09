#!/usr/bin/env python3
"""
Comprehensive Test Suite for TinderBot
Tests everything including manual LLM interactions and debug functionality
"""

import json
import time
import sys
import os
import subprocess
import threading
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class ComprehensiveTester:
    def __init__(self):
        self.test_results = {}
        self.current_test = ""
        self.config = None
        self.load_config()
        
    def load_config(self):
        """Load configuration"""
        try:
            # Try multiple possible config locations
            config_paths = [
                'config.json',
                'src/config/config.json',
                '../config/config.json'
            ]
            
            for config_path in config_paths:
                try:
                    with open(config_path, 'r') as f:
                        self.config = json.load(f)
                    return True
                except FileNotFoundError:
                    continue
                    
            print(f"❌ Failed to load config: No config.json found in any expected location")
            return False
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            return False
    
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_config_loading(self):
        """Test configuration loading"""
        self.current_test = "Config Loading"
        success = self.load_config()
        self.log_test(self.current_test, success, "Configuration loaded successfully" if success else "Failed to load config")
        return success
    
    def test_imports(self):
        """Test all critical imports"""
        self.current_test = "Import Tests"
        imports_to_test = [
            ("langchain_openai", "ChatOpenAI"),
            ("langchain_core", "prompts"),
            ("langchain", "memory"),
            ("requests", ""),
            ("json", ""),
            ("threading", ""),
            ("subprocess", "")
        ]
        
        failed_imports = []
        for module, item in imports_to_test:
            try:
                if item:
                    exec(f"from {module} import {item}")
                else:
                    exec(f"import {module}")
            except ImportError as e:
                failed_imports.append(f"{module}.{item}: {e}")
        
        success = len(failed_imports) == 0
        message = "All imports successful" if success else f"Failed imports: {', '.join(failed_imports)}"
        self.log_test(self.current_test, success, message)
        return success
    
    def test_api_connection(self):
        """Test API connectivity"""
        self.current_test = "API Connection"
        try:
            import requests
            headers = {
                "X-Auth-Token": self.config['tinder-auth-token'],
                "Content-type": "application/json"
            }
            response = requests.get("https://api.gotinder.com/v2/profile?include=account%2Cuser", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.log_test(self.current_test, True, "Tinder API connection successful")
                return True
            else:
                self.log_test(self.current_test, False, f"Tinder API returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test(self.current_test, False, f"API connection failed: {e}")
            return False
    
    def test_openai_connection(self):
        """Test OpenAI API connection"""
        self.current_test = "OpenAI Connection"
        try:
            from langchain_openai import ChatOpenAI
            chat = ChatOpenAI(api_key=self.config['api_key'], model="gpt-4o", temperature=0.2)
            response = chat.invoke("Say 'Hello World' in one word.")
            
            if response and response.content:
                self.log_test(self.current_test, True, "OpenAI API connection successful")
                return True
            else:
                self.log_test(self.current_test, False, "OpenAI API returned empty response")
                return False
        except Exception as e:
            self.log_test(self.current_test, False, f"OpenAI connection failed: {e}")
            return False
    
    def test_llm_response_generation(self):
        """Test LLM response generation with different prompts"""
        self.current_test = "LLM Response Generation"
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            chat = ChatOpenAI(api_key=self.config['api_key'], model="gpt-4o", temperature=0.2)
            
            # Test different prompt scenarios
            test_cases = [
                {
                    "name": "Icebreaker",
                    "prompt": "Du bist ein Tinder Bot. Schreibe einen kurzen, humorvollen Icebreaker für ein Match namens 'Anna' das Reisen und Fitness mag.",
                    "expected_keywords": ["Anna", "Reisen", "Fitness"]
                },
                {
                    "name": "Relationship Intent - Nichts ernstes",
                    "prompt": "Das Match sucht 'Nichts ernstes'. Schreibe eine flirty, direkte Nachricht.",
                    "expected_keywords": ["flirty", "direkt"]
                },
                {
                    "name": "Relationship Intent - Ernsthaft",
                    "prompt": "Das Match sucht eine 'Feste, ernsthafte Beziehung'. Schreibe eine romantische, ernsthafte Nachricht.",
                    "expected_keywords": ["ernst", "romantisch"]
                }
            ]
            
            passed_tests = 0
            for test_case in test_cases:
                try:
                    response = chat.invoke(test_case["prompt"])
                    if response and response.content:
                        # Check if response contains expected keywords (basic check)
                        content_lower = response.content.lower()
                        keyword_found = any(keyword.lower() in content_lower for keyword in test_case["expected_keywords"])
                        if keyword_found:
                            passed_tests += 1
                        print(f"  - {test_case['name']}: {'✅' if keyword_found else '⚠️'}")
                    else:
                        print(f"  - {test_case['name']}: ❌ Empty response")
                except Exception as e:
                    print(f"  - {test_case['name']}: ❌ Error: {e}")
            
            success = passed_tests >= len(test_cases) * 0.8  # 80% success rate
            message = f"{passed_tests}/{len(test_cases)} prompt tests passed"
            self.log_test(self.current_test, success, message)
            return success
            
        except Exception as e:
            self.log_test(self.current_test, False, f"LLM test failed: {e}")
            return False
    
    def test_phase_manager(self):
        """Test conversation phase management"""
        self.current_test = "Phase Manager"
        try:
            from src.chat.chat import PhaseManager
            
            phase_manager = PhaseManager(self.config)
            
            # Test phase determination
            test_cases = [
                (1, "icebreaker"),
                (5, "interests"),
                (12, "compatibility"),
                (20, "date_planning")
            ]
            
            passed_tests = 0
            for message_count, expected_phase in test_cases:
                phase_name, phase_config = phase_manager.get_current_phase(message_count)
                if phase_name == expected_phase:
                    passed_tests += 1
                else:
                    print(f"  - Expected {expected_phase} for {message_count} messages, got {phase_name}")
            
            success = passed_tests == len(test_cases)
            message = f"{passed_tests}/{len(test_cases)} phase tests passed"
            self.log_test(self.current_test, success, message)
            return success
            
        except Exception as e:
            self.log_test(self.current_test, False, f"Phase manager test failed: {e}")
            return False
    
    def test_relationship_intent_prompts(self):
        """Test relationship intent prompt generation"""
        self.current_test = "Relationship Intent Prompts"
        try:
            from src.chat.chat import ChatManager
            
            # Create mock API
            class MockAPI:
                def __init__(self):
                    self.user_profile = None
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test different relationship intents
            test_cases = [
                {
                    "name": "Anna",
                    "relationship_intent": "Nichts ernstes",
                    "bio": "Spaß haben und neue Leute kennenlernen 😊",
                    "interests": ["Reisen", "Fitness", "Kochen"]
                },
                {
                    "name": "Lisa",
                    "relationship_intent": "Feste, ernsthafte Beziehung",
                    "bio": "Suche nach einer echten Verbindung",
                    "interests": ["Lesen", "Kochen", "Familie"]
                }
            ]
            
            passed_tests = 0
            for test_case in test_cases:
                chat_manager.match_info = test_case
                match_details = f"Name: {test_case['name']}, Bio: {test_case['bio']}, Beziehungsziel: {test_case['relationship_intent']}"
                chat_manager.setup_prompt_template(match_details, "icebreaker")
                
                # Check if relationship intent prompt was added
                # The prompt is a ChatPromptTemplate, so we need to access it differently
                system_prompt = str(chat_manager.prompt.messages[0])
                relationship_prompts = self.config.get('relationship_intent_prompts', {})
                
                found_prompt = False
                for intent_key, prompt in relationship_prompts.items():
                    if intent_key.lower() in test_case['relationship_intent'].lower():
                        if prompt in system_prompt:
                            found_prompt = True
                            break
                
                if found_prompt:
                    passed_tests += 1
                else:
                    print(f"  - {test_case['name']}: Relationship intent prompt not found")
            
            success = passed_tests == len(test_cases)
            message = f"{passed_tests}/{len(test_cases)} relationship intent tests passed"
            self.log_test(self.current_test, success, message)
            return success
            
        except Exception as e:
            self.log_test(self.current_test, False, f"Relationship intent test failed: {e}")
            return False
    
    def test_storage_functionality(self):
        """Test persistent storage"""
        self.current_test = "Storage Functionality"
        try:
            from src.utils.storage import PersistentStorage
            
            # Test basic storage
            test_storage = PersistentStorage('test_storage.pkl')
            test_data = {
                'known_match_ids': {'test_match_1', 'test_match_2'},
                'known_message_ids': {'test_message_1'},
                'chats': {'test_chat': []},
                'excluded_chat_names': {'TestUser'}
            }
            
            # Test save and load
            test_storage.save(test_data)
            loaded_data = test_storage.load()
            
            if loaded_data == test_data:
                # Test extended storage methods
                test_storage.add_excluded_chat("NewUser")
                excluded_chats = test_storage.get_excluded_chats()
                
                if "NewUser" in excluded_chats:
                    test_storage.remove_excluded_chat("NewUser")
                    final_excluded = test_storage.get_excluded_chats()
                    
                    if "NewUser" not in final_excluded:
                        self.log_test(self.current_test, True, "Storage functionality working correctly")
                        
                        # Cleanup
                        if os.path.exists('test_storage.pkl'):
                            os.remove('test_storage.pkl')
                        return True
            
            self.log_test(self.current_test, False, "Storage data mismatch")
            return False
            
        except Exception as e:
            self.log_test(self.current_test, False, f"Storage test failed: {e}")
            return False
    
    def test_response_timing(self):
        """Test response timing calculations"""
        self.current_test = "Response Timing"
        try:
            from src.chat.chat import ResponseTimer
            
            response_timer = ResponseTimer(self.config)
            
            # Test timing configuration
            timing_config = self.config.get('response_timing', {})
            required_keys = ['first_message_delay', 'random_variation_percentage', 'min_response_time']
            
            config_valid = all(key in timing_config for key in required_keys)
            
            if config_valid:
                # Test timer functionality
                response_timer.start()
                time.sleep(0.1)  # Brief pause
                response_timer.stop()
                
                self.log_test(self.current_test, True, "Response timing configured and functional")
                return True
            else:
                self.log_test(self.current_test, False, "Missing timing configuration")
                return False
                
        except Exception as e:
            self.log_test(self.current_test, False, f"Response timing test failed: {e}")
            return False
    
    def test_connection_monitoring(self):
        """Test connection monitoring functionality"""
        self.current_test = "Connection Monitoring"
        try:
            # Test connection test method (if available)
            import requests
            
            headers = {
                "X-Auth-Token": self.config['tinder-auth-token'],
                "Content-type": "application/json"
            }
            
            # Test successful connection
            response = requests.get("https://api.gotinder.com/v2/profile?include=account%2Cuser", 
                                  headers=headers, timeout=5)
            
            if response.status_code == 200:
                self.log_test(self.current_test, True, "Connection monitoring functional")
                return True
            else:
                self.log_test(self.current_test, False, f"Connection test returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(self.current_test, False, f"Connection monitoring test failed: {e}")
            return False
    
    def test_debug_functionality(self):
        """Test debug functionality"""
        self.current_test = "Debug Functionality"
        try:
            # Test if debug mode can be started
            from src.chat.chat import ChatManager
            
            class MockAPI:
                def __init__(self):
                    self.user_profile = None
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test debug mode setup
            test_match_info = {
                "name": "TestUser",
                "bio": "Test bio",
                "interests": ["Test"],
                "relationship_intent": "Weiß ich noch nicht"
            }
            
            chat_manager.match_info = test_match_info
            match_details = f"Name: {test_match_info['name']}, Bio: {test_match_info['bio']}"
            chat_manager.setup_prompt_template(match_details, "icebreaker")
            
            if chat_manager.prompt and chat_manager.chain:
                self.log_test(self.current_test, True, "Debug functionality setup successful")
                return True
            else:
                self.log_test(self.current_test, False, "Debug setup failed")
                return False
                
        except Exception as e:
            self.log_test(self.current_test, False, f"Debug functionality test failed: {e}")
            return False
    
    def test_manual_llm_interaction(self):
        """Manual LLM interaction test"""
        self.current_test = "Manual LLM Interaction"
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            chat = ChatOpenAI(api_key=self.config['api_key'], model="gpt-4o", temperature=0.2)
            
            # Test a realistic conversation scenario
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.config['goals_to_be_achieved']),
                ("human", "Das Match hat geschrieben: 'Hey, wie geht's? Ich sehe du stehst auf Star Wars! 🚀'")
            ])
            
            chain = prompt_template | chat
            response = chain.invoke({})
            
            if response and response.content:
                # Basic validation
                content = response.content.lower()
                has_response = len(content) > 10
                has_question = "?" in content or "was" in content or "wie" in content
                
                if has_response:
                    self.log_test(self.current_test, True, f"Manual LLM interaction successful (Response length: {len(content)} chars)")
                    return True
                else:
                    self.log_test(self.current_test, False, "LLM response too short")
                    return False
            else:
                self.log_test(self.current_test, False, "Empty LLM response")
                return False
                
        except Exception as e:
            self.log_test(self.current_test, False, f"Manual LLM test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🧪 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_config_loading,
            self.test_imports,
            self.test_api_connection,
            self.test_openai_connection,
            self.test_llm_response_generation,
            self.test_phase_manager,
            self.test_relationship_intent_prompts,
            self.test_storage_functionality,
            self.test_response_timing,
            self.test_connection_monitoring,
            self.test_debug_functionality,
            self.test_manual_llm_interaction
        ]
        
        # Add complete chat flow tests
        try:
            from .test_complete_chat_flow import (
                test_complete_chat_flow,
                test_multiple_matches_conversation,
                test_message_cancellation_in_flow
            )
            
            # Create wrapper methods for the new tests
            def test_complete_chat_flow_wrapper():
                result = test_complete_chat_flow()
                self.log_test("Complete Chat Flow", result.get('success', False), 
                             f"Messages: {result.get('total_messages', 0)}, Success: {result.get('successful_responses', 0)}")
                return result.get('success', False)
            
            def test_multiple_matches_wrapper():
                result = test_multiple_matches_conversation()
                self.log_test("Multiple Matches", result.get('success', False),
                             f"Success Rate: {result.get('overall_success_rate', 0):.1%}")
                return result.get('success', False)
            
            def test_message_cancellation_wrapper():
                result = test_message_cancellation_in_flow()
                self.log_test("Message Cancellation", result.get('success', False),
                             f"Cancellation: {'Working' if result.get('cancellation_working') else 'Not Working'}")
                return result.get('success', False)
            
            tests.extend([
                test_complete_chat_flow_wrapper,
                test_multiple_matches_wrapper,
                test_message_cancellation_wrapper
            ])
            print("   ✅ Complete chat flow tests integrated")
        except ImportError as e:
            print(f"   ⚠️  Could not import complete chat flow tests: {e}")
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_test(self.current_test, False, f"Test crashed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready for deployment.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. System should work but may have issues.")
        else:
            print("❌ Many tests failed. System needs attention before deployment.")
        
        return passed == total
    
    def get_test_results(self):
        """Get detailed test results"""
        return self.test_results

def main():
    """Main test runner"""
    tester = ComprehensiveTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    main()
