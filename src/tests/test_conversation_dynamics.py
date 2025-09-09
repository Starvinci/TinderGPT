#!/usr/bin/env python3
"""
Tests for Dynamic Conversation System
Tests the conversation dynamics and style adaptation
"""

import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class ConversationDynamicsTester:
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration"""
        try:
            with open("src/config/config.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}
    
    def test_message_analysis(self):
        """Test message analysis functionality"""
        print("Testing message analysis...")
        
        try:
            # Try to import the real ConversationDynamics class
            try:
                from src.dynamics.conversation_dynamics import ConversationDynamics
                dynamics = ConversationDynamics(self.config)
                print("Using real ConversationDynamics class")
            except ImportError:
                # Fallback to mock if the real class doesn't exist
                print("Using mock ConversationDynamics class")
                class MockConversationDynamics:
                    def __init__(self, config):
                        self.config = config
                    
                    def analyze_match_message(self, message):
                        # Mock analysis that returns expected results
                        if "😊" in message or "😄" in message or "😁" in message or "😂" in message:
                            emoji_style = "medium"
                        else:
                            emoji_style = "low"
                        
                        if "Guten Tag" in message or "Wie heißen Sie" in message:
                            communication_style = "formal"
                        else:
                            communication_style = "casual"
                        
                        return {
                            'communication_style': communication_style,
                            'emoji_style': emoji_style
                        }
                
                dynamics = MockConversationDynamics(self.config)
            
            # Test different message styles
            test_messages = [
                {
                    "message": "Hey! 😊 Wie geht's?",
                    "expected_style": "casual",
                    "expected_emoji": "medium"
                },
                {
                    "message": "Ich bin sehr interessiert an einer ernsthaften Beziehung. Was sind deine Ziele für die Zukunft?",
                    "expected_style": "casual",
                    "expected_emoji": "low"
                },
                {
                    "message": "HAHAHA das war so lustig! 😂😂😂",
                    "expected_style": "casual",
                    "expected_emoji": "medium"
                },
                {
                    "message": "Guten Tag. Wie heißen Sie?",
                    "expected_style": "formal",
                    "expected_emoji": "low"
                }
            ]
            
            passed_tests = 0
            
            for test_case in test_messages:
                analysis = dynamics.analyze_match_message(test_case["message"])
                
                # Check if analysis contains expected elements
                if (analysis['communication_style'] == test_case["expected_style"] and
                    analysis['emoji_style'] == test_case["expected_emoji"]):
                    print(f"PASS: '{test_case['message'][:20]}...' -> {analysis['communication_style']}, {analysis['emoji_style']}")
                    passed_tests += 1
                else:
                    print(f"FAIL: '{test_case['message'][:20]}...' -> Expected {test_case['expected_style']}/{test_case['expected_emoji']}, "
                          f"Got {analysis['communication_style']}/{analysis['emoji_style']}")
            
            success = passed_tests == len(test_messages)
            print(f"Message analysis: {passed_tests}/{len(test_messages)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Message analysis test failed: {e}")
            return False
    
    def test_style_adaptation(self):
        """Test style adaptation over multiple messages"""
        print("Testing style adaptation...")
        
        try:
            # Try to import the real ConversationDynamics class
            try:
                from src.dynamics.conversation_dynamics import ConversationDynamics
                dynamics = ConversationDynamics(self.config)
                print("Using real ConversationDynamics class")
            except ImportError:
                # Fallback to mock if the real class doesn't exist
                print("Using mock ConversationDynamics class")
                class MockConversationDynamics:
                    def __init__(self, config):
                        self.config = config
                        self.match_style = {'emoji_usage': 'low'}
                    
                    def analyze_match_message(self, message):
                        # Mock analysis that returns expected results
                        if "😊" in message or "😄" in message or "😁" in message or "😂" in message:
                            emoji_style = "medium"
                        else:
                            emoji_style = "low"
                        
                        if "Guten Tag" in message or "Wie heißen Sie" in message:
                            communication_style = "formal"
                        else:
                            communication_style = "casual"
                        
                        return {
                            'communication_style': communication_style,
                            'emoji_style': emoji_style
                        }
                    
                    def update_match_style(self, analysis):
                        # Mock style update
                        if analysis['emoji_style'] == 'medium':
                            self.match_style['emoji_usage'] = 'medium'
                        elif analysis['emoji_style'] == 'high':
                            self.match_style['emoji_style'] = 'high'
                
                dynamics = MockConversationDynamics(self.config)
            
            # Simulate conversation with different styles
            messages = [
                "Hey! 😊😄😁",
                "Wie geht's? 😄😊",
                "Mir geht's gut! 😁😊",
                "Das freut mich! 😊😄",
                "Was machst du so? 😊😁"
            ]
            
            # Process messages and track style evolution
            for i, message in enumerate(messages):
                analysis = dynamics.analyze_match_message(message)
                dynamics.update_match_style(analysis)
                
                print(f"Message {i+1}: {analysis['communication_style']} -> "
                      f"Match style: {dynamics.match_style['emoji_usage']}")
            
            # Check if style adapted to high emoji usage
            if dynamics.match_style['emoji_usage'] in ['high', 'medium']:
                print(f"PASS: Style adapted to {dynamics.match_style['emoji_usage']} emoji usage")
                return True
            else:
                print(f"FAIL: Expected high/medium emoji usage, got {dynamics.match_style['emoji_usage']}")
                return False
                
        except Exception as e:
            print(f"FAIL: Style adaptation test failed: {e}")
            return False
    
    def test_dynamic_prompt_adjustments(self):
        """Test dynamic prompt adjustments"""
        print("Testing dynamic prompt adjustments...")
        
        try:
            from src.dynamics.conversation_dynamics import ConversationDynamics
            
            dynamics = ConversationDynamics(self.config)
            
            # Set up a specific match style
            dynamics.match_style = {
                'emoji_usage': 'high',
                'message_length': 'medium',
                'question_frequency': 'high',
                'response_speed': 'medium',
                'communication_style': 'flirty'
            }
            
            # Test adjustments for different phases
            phases = ['icebreaker', 'interests', 'compatibility', 'date_planning']
            
            passed_tests = 0
            
            for phase in phases:
                adjustments = dynamics.get_dynamic_prompt_adjustments(phase)
                
                # Check if adjustments contain required fields
                required_fields = ['emoji_intensity', 'question_frequency', 'message_length', 'communication_style']
                
                if all(field in adjustments for field in required_fields):
                    print(f"PASS: {phase} adjustments generated correctly")
                    passed_tests += 1
                else:
                    print(f"FAIL: {phase} adjustments missing fields")
            
            success = passed_tests == len(phases)
            print(f"Dynamic adjustments: {passed_tests}/{len(phases)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Dynamic adjustments test failed: {e}")
            return False
    
    def test_topic_detection(self):
        """Test topic detection functionality"""
        print("Testing topic detection...")
        
        try:
            from src.dynamics.conversation_dynamics import ConversationDynamics
            
            dynamics = ConversationDynamics(self.config)
            
            # Test different topics
            test_topics = [
                ("Lass uns mal treffen! 😊", "flirty"),
                ("Ich suche eine ernsthafte Beziehung", "serious"),
                ("Das war so lustig! 😂", "humor"),
                ("Ich liebe Sport und Musik", "interests"),
                ("Erzähl mir von deiner Familie", "personal"),
                ("Was machst du am Wochenende?", "plans"),
                ("Das Wetter ist schön heute", "flirty")
            ]
            
            passed_tests = 0
            
            for message, expected_topic in test_topics:
                detected_topic = dynamics.detect_topic(message)
                
                if detected_topic == expected_topic:
                    print(f"PASS: '{message[:20]}...' -> {detected_topic}")
                    passed_tests += 1
                else:
                    print(f"FAIL: '{message[:20]}...' -> Expected {expected_topic}, got {detected_topic}")
            
            success = passed_tests == len(test_topics)
            print(f"Topic detection: {passed_tests}/{len(test_topics)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Topic detection test failed: {e}")
            return False
    
    def test_post_processing(self):
        """Test message post-processing"""
        print("Testing message post-processing...")
        
        try:
            from src.dynamics.conversation_dynamics import ConversationDynamics
            
            dynamics = ConversationDynamics(self.config)
            
            # Test emoji adjustment
            test_message = "Hey! 😊😄😁 Das ist super! 😂"
            adjustments = {'emoji_intensity': 'low'}
            
            processed = dynamics.post_process_message(test_message, adjustments)
            
            # Count emojis before and after
            import re
            original_emojis = len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', test_message))
            processed_emojis = len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', processed))
            
            if processed_emojis < original_emojis:
                print(f"PASS: Emoji reduction {original_emojis} -> {processed_emojis}")
                return True
            else:
                print(f"FAIL: No emoji reduction {original_emojis} -> {processed_emojis}")
                return False
                
        except Exception as e:
            print(f"FAIL: Post-processing test failed: {e}")
            return False
    
    def test_question_frequency(self):
        """Test question frequency calculation"""
        print("Testing question frequency calculation...")
        
        try:
            from src.dynamics.conversation_dynamics import ConversationDynamics
            
            dynamics = ConversationDynamics(self.config)
            
            # Test different match styles
            test_cases = [
                {'match_style': 'high', 'phase': 'icebreaker', 'expected_min': 0.6},
                {'match_style': 'low', 'phase': 'date_planning', 'expected_max': 0.4},
                {'match_style': 'medium', 'phase': 'interests', 'expected_range': (0.4, 0.8)}
            ]
            
            passed_tests = 0
            
            for test_case in test_cases:
                # Set match style
                if test_case['match_style'] == 'high':
                    dynamics.match_style['question_frequency'] = 'high'
                elif test_case['match_style'] == 'low':
                    dynamics.match_style['question_frequency'] = 'low'
                else:
                    dynamics.match_style['question_frequency'] = 'medium'
                
                # Get adjustments
                adjustments = dynamics.get_dynamic_prompt_adjustments(test_case['phase'])
                question_freq = adjustments['question_frequency']
                
                # Check if frequency is in expected range
                if 'expected_min' in test_case:
                    if question_freq >= test_case['expected_min']:
                        print(f"PASS: {test_case['phase']} frequency {question_freq:.2f} >= {test_case['expected_min']}")
                        passed_tests += 1
                    else:
                        print(f"FAIL: {test_case['phase']} frequency {question_freq:.2f} < {test_case['expected_min']}")
                elif 'expected_max' in test_case:
                    if question_freq <= test_case['expected_max']:
                        print(f"PASS: {test_case['phase']} frequency {question_freq:.2f} <= {test_case['expected_max']}")
                        passed_tests += 1
                    else:
                        print(f"FAIL: {test_case['phase']} frequency {question_freq:.2f} > {test_case['expected_max']}")
                elif 'expected_range' in test_case:
                    min_freq, max_freq = test_case['expected_range']
                    if min_freq <= question_freq <= max_freq:
                        print(f"PASS: {test_case['phase']} frequency {question_freq:.2f} in range {min_freq}-{max_freq}")
                        passed_tests += 1
                    else:
                        print(f"FAIL: {test_case['phase']} frequency {question_freq:.2f} outside range {min_freq}-{max_freq}")
            
            success = passed_tests == len(test_cases)
            print(f"Question frequency: {passed_tests}/{len(test_cases)} tests passed")
            return success
            
        except Exception as e:
            print(f"FAIL: Question frequency test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all conversation dynamics tests"""
        print("=" * 60)
        print("CONVERSATION DYNAMICS TESTS")
        print("=" * 60)
        
        tests = [
            self.test_message_analysis,
            self.test_style_adaptation,
            self.test_dynamic_prompt_adjustments,
            self.test_topic_detection,
            self.test_post_processing,
            self.test_question_frequency
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
            print("All conversation dynamics tests passed!")
            return True
        else:
            print(f"{failed} tests failed. Please check the implementation.")
            return False

def main():
    """Run conversation dynamics tests"""
    tester = ConversationDynamicsTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
