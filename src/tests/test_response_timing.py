#!/usr/bin/env python3
"""
Response Timing Tests for TinderBot
Tests the response timing system with various short response times
"""

import json
import time
import random
import threading
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class ResponseTimingTester:
    def __init__(self):
        self.config = self.load_config()
        
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
                        return json.load(f)
                except FileNotFoundError:
                    continue
                    
            print(f"Failed to load config: No config.json found in any expected location")
            return {}
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}
    
    def test_response_timer_basic(self):
        """Test basic ResponseTimer functionality"""
        print("Testing basic ResponseTimer functionality...")
        
        try:
            from src.chat.chat import ResponseTimer
            
            timer = ResponseTimer(self.config)
            timer.start()
            
            # Test scheduling a response
            test_match_id = "test_match_123"
            test_message = "Test message"
            test_delay = 2  # 2 seconds
            
            timer.schedule_response(test_match_id, test_delay, test_message, None)
            
            # Wait for response to be processed
            time.sleep(test_delay + 1)
            
            # Check if response was processed
            if test_match_id not in timer.scheduled_responses:
                print("PASS: Response was processed correctly")
                timer.stop()
                return True
            else:
                print("FAIL: Response was not processed")
                timer.stop()
                return False
                
        except Exception as e:
            print(f"FAIL: Basic timer test failed: {e}")
            return False
    
    def test_calculate_response_delay(self):
        """Test response delay calculation with various times"""
        print("Testing response delay calculation...")
        
        try:
            from src.chat.chat import ChatManager
            
            # Mock API
            class MockAPI:
                def send_message(self, match_id, message):
                    pass
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test cases with different response times
            test_cases = [
                {"match_time": 10, "expected_min": 8, "expected_max": 12, "description": "10 seconds"},
                {"match_time": 30, "expected_min": 24, "expected_max": 36, "description": "30 seconds"},
                {"match_time": 60, "expected_min": 48, "expected_max": 72, "description": "1 minute"},
                {"match_time": 120, "expected_min": 96, "expected_max": 144, "description": "2 minutes"},
                {"match_time": 300, "expected_min": 240, "expected_max": 360, "description": "5 minutes"},
            ]
            
            passed_tests = 0
            
            for test_case in test_cases:
                # Simulate match response time
                chat_manager.last_match_message_time = time.time() - test_case["match_time"]
                
                # Calculate delay
                delay = chat_manager.calculate_response_delay()
                
                # Check if delay is within expected range (±20% variation)
                min_expected = test_case["expected_min"]
                max_expected = test_case["expected_max"]
                
                # Check if delay is within expected range (±20% variation)
                min_expected = test_case["expected_min"]
                max_expected = test_case["expected_max"]
                
                # For very short response times (< 10s), minimum time should be enforced
                min_response_time = self.config.get('response_timing', {}).get('min_response_time', 30)
                if test_case["match_time"] < 10 and delay < min_response_time:
                    print(f"FAIL: {test_case['description']} - Delay {delay:.1f}s is below minimum {min_response_time}s")
                    continue
                
                if min_expected <= delay <= max_expected:
                    print(f"PASS: {test_case['description']} - Delay {delay:.1f}s (expected {min_expected}-{max_expected}s)")
                    passed_tests += 1
                else:
                    print(f"FAIL: {test_case['description']} - Delay {delay:.1f}s outside expected range {min_expected}-{max_expected}s")
            
            success = passed_tests == len(test_cases)
            print(f"Response delay calculation: {passed_tests}/{len(test_cases)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Response delay calculation test failed: {e}")
            return False
    
    def test_first_message_immediate(self):
        """Test that first message is sent immediately"""
        print("Testing first message immediate sending...")
        
        try:
            from src.chat.chat import ChatManager
            
            # Mock API
            class MockAPI:
                def send_message(self, match_id, message):
                    self.last_sent = message
                    self.sent_count = getattr(self, 'sent_count', 0) + 1
            
            api = MockAPI()
            chat_manager = ChatManager(api, "src/config/config.json")
            
            # Simulate first message (no last_match_message_time)
            chat_manager.last_match_message_time = None
            
            # Calculate delay
            delay = chat_manager.calculate_response_delay()
            
            if delay == 0:
                print("PASS: First message delay is 0 (immediate)")
                return True
            else:
                print(f"FAIL: First message delay is {delay}s, should be 0")
                return False
                
        except Exception as e:
            print(f"FAIL: First message test failed: {e}")
            return False
    
    def test_minimum_response_time(self):
        """Test that minimum response time is only enforced for very quick responses"""
        print("Testing minimum response time enforcement...")
        
        try:
            from src.chat.chat import ChatManager
            
            # Mock API
            class MockAPI:
                def send_message(self, match_id, message):
                    pass
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test with very short match response time (< 10 seconds)
            chat_manager.last_match_message_time = time.time() - 5  # 5 seconds ago
            
            # Calculate delay
            delay = chat_manager.calculate_response_delay()
            
            # Get minimum response time from config
            min_response_time = self.config.get('response_timing', {}).get('min_response_time', 30)
            
            if delay >= min_response_time:
                print(f"PASS: Very quick response (5s) -> delay {delay:.1f}s (enforced minimum)")
            else:
                print(f"FAIL: Very quick response (5s) -> delay {delay:.1f}s (below minimum {min_response_time}s)")
                return False
            
            # Test with moderate response time (should not enforce minimum)
            chat_manager.last_match_message_time = time.time() - 15  # 15 seconds ago
            delay = chat_manager.calculate_response_delay()
            
            if delay < min_response_time:
                print(f"PASS: Moderate response (15s) -> delay {delay:.1f}s (natural timing)")
                return True
            else:
                print(f"FAIL: Moderate response (15s) -> delay {delay:.1f}s (unnecessarily enforced minimum)")
                return False
                
        except Exception as e:
            print(f"FAIL: Minimum response time test failed: {e}")
            return False
    
    def test_random_variation(self):
        """Test that random variation is applied correctly"""
        print("Testing random variation application...")
        
        try:
            from src.chat.chat import ChatManager
            
            # Mock API
            class MockAPI:
                def send_message(self, match_id, message):
                    pass
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test multiple calculations with same input
            base_time = 60  # 60 seconds
            chat_manager.last_match_message_time = time.time() - base_time
            
            delays = []
            for _ in range(10):
                delay = chat_manager.calculate_response_delay()
                delays.append(delay)
            
            # Check that delays vary (not all the same)
            if len(set(delays)) > 1:
                print(f"PASS: Delays vary between {min(delays):.1f}s and {max(delays):.1f}s")
                
                # Check that variation is reasonable (±20%)
                expected_min = base_time * 0.8
                expected_max = base_time * 1.2
                
                if all(expected_min <= delay <= expected_max for delay in delays):
                    print(f"PASS: All delays within expected range {expected_min:.1f}-{expected_max:.1f}s")
                    return True
                else:
                    print(f"FAIL: Some delays outside expected range")
                    return False
            else:
                print("FAIL: Delays do not vary")
                return False
                
        except Exception as e:
            print(f"FAIL: Random variation test failed: {e}")
            return False
    
    def test_short_response_times(self):
        """Test with various response times to verify natural timing"""
        print("Testing various response times...")
        
        try:
            from src.chat.chat import ChatManager
            
            # Mock API
            class MockAPI:
                def send_message(self, match_id, message):
                    pass
            
            chat_manager = ChatManager(MockAPI(), "src/config/config.json")
            
            # Test cases with different response times
            test_cases = [
                {"time": 5, "should_enforce_min": True, "description": "Very quick"},
                {"time": 8, "should_enforce_min": True, "description": "Quick"},
                {"time": 12, "should_enforce_min": False, "description": "Moderate"},
                {"time": 20, "should_enforce_min": False, "description": "Normal"},
                {"time": 45, "should_enforce_min": False, "description": "Slow"},
            ]
            
            passed_tests = 0
            min_response_time = self.config.get('response_timing', {}).get('min_response_time', 30)
            
            for test_case in test_cases:
                chat_manager.last_match_message_time = time.time() - test_case["time"]
                delay = chat_manager.calculate_response_delay()
                
                if test_case["should_enforce_min"]:
                    if delay >= min_response_time:
                        print(f"PASS: {test_case['description']} ({test_case['time']}s) -> delay {delay:.1f}s (enforced minimum)")
                        passed_tests += 1
                    else:
                        print(f"FAIL: {test_case['description']} ({test_case['time']}s) -> delay {delay:.1f}s (should enforce minimum)")
                else:
                    # For longer response times, we expect natural timing
                    # The delay should be close to the original time with variation
                    expected_min = test_case["time"] * 0.8
                    expected_max = test_case["time"] * 1.2
                    
                    if expected_min <= delay <= expected_max:
                        print(f"PASS: {test_case['description']} ({test_case['time']}s) -> delay {delay:.1f}s (natural timing)")
                        passed_tests += 1
                    else:
                        print(f"FAIL: {test_case['description']} ({test_case['time']}s) -> delay {delay:.1f}s (outside natural range {expected_min:.1f}-{expected_max:.1f}s)")
            
            success = passed_tests == len(test_cases)
            print(f"Response time variations: {passed_tests}/{len(test_cases)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Response time variations test failed: {e}")
            return False
    
    def test_timer_threading(self):
        """Test that timer works correctly in threaded environment"""
        print("Testing timer threading...")
        
        try:
            from src.chat.chat import ResponseTimer
            
            timer = ResponseTimer(self.config)
            timer.start()
            
            # Schedule multiple responses
            responses = []
            for i in range(3):
                match_id = f"test_match_{i}"
                message = f"Test message {i}"
                delay = 1 + i  # 1, 2, 3 seconds
                
                timer.schedule_response(match_id, delay, message, None)
                responses.append((match_id, delay))
            
            # Wait for all responses to be processed
            time.sleep(5)
            
            # Check that all responses were processed
            unprocessed = [match_id for match_id, _ in responses if match_id in timer.scheduled_responses]
            
            if not unprocessed:
                print("PASS: All responses processed in threaded environment")
                timer.stop()
                return True
            else:
                print(f"FAIL: Unprocessed responses: {unprocessed}")
                timer.stop()
                return False
                
        except Exception as e:
            print(f"FAIL: Timer threading test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all response timing tests"""
        print("=" * 60)
        print("RESPONSE TIMING TESTS")
        print("=" * 60)
        
        tests = [
            self.test_response_timer_basic,
            self.test_calculate_response_delay,
            self.test_first_message_immediate,
            self.test_minimum_response_time,
            self.test_random_variation,
            self.test_short_response_times,
            self.test_timer_threading
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"ERROR: Test {test.__name__} crashed: {e}")
                failed += 1
            print()
        
        print("=" * 60)
        print(f"Test Results: {passed}/{len(tests)} tests passed")
        
        if failed == 0:
            print("All response timing tests passed!")
            return True
        else:
            print(f"{failed} tests failed. Please check the implementation.")
            return False

def main():
    """Run response timing tests"""
    tester = ResponseTimingTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
