#!/usr/bin/env python3
"""
Comprehensive tests for complete chat flow with 10 messages
"""

import sys
import os
import time
import random
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def create_mock_match(name="TestMatch", age=25, interests=None, bio="Test bio"):
    """Create a realistic mock match"""
    if interests is None:
        interests = ["Fitness", "Travel", "Music"]
    
    return {
        "_id": f"match_{random.randint(1000, 9999)}",
        "person": {
            "name": name,
            "birth_date": f"{datetime.now().year - age}-01-01T00:00:00.000Z",
            "interests": [{"name": interest} for interest in interests],
            "bio": bio,
            "distance_mi": random.randint(1, 50),
            "jobs": [{"title": {"name": "Software Developer"}}],
            "schools": [{"name": "University"}],
            "relationship_intent": random.choice([
                "Feste, ernsthafte Beziehung",
                "Nichts ernstes", 
                "Offen für festes",
                "Weiß ich noch nicht"
            ])
        },
        "messages": []
    }

def create_mock_messages(count=10):
    """Create realistic mock messages for testing"""
    message_templates = [
        "Hey, wie geht's? 😊",
        "Was machst du so?",
        "Ich liebe auch {interest}!",
        "Das klingt spannend!",
        "Was ist dein Lieblingsfilm?",
        "Bist du gerne unterwegs?",
        "Ich spiele auch gerne {activity}",
        "Das ist echt cool!",
        "Was machst du beruflich?",
        "Hast du Haustiere? 🐕",
        "Ich reise auch gerne!",
        "Was ist dein Lieblingsessen?",
        "Das ist interessant!",
        "Bist du sportlich?",
        "Ich höre auch gerne {music_type}",
        "Das klingt nach Spaß!",
        "Was sind deine Hobbys?",
        "Ich bin auch {personality_type}",
        "Das ist toll!",
        "Was machst du am Wochenende?"
    ]
    
    interests = ["Fitness", "Travel", "Music", "Movies", "Cooking", "Sports"]
    activities = ["Schach", "Fitness", "Reisen", "Lesen", "Gaming"]
    music_types = ["Rock", "Pop", "Jazz", "Electronic", "Classical"]
    personality_types = ["extrovertiert", "introvertiert", "abenteuerlustig", "ruhig"]
    
    messages = []
    for i in range(count):
        template = random.choice(message_templates)
        message = template.format(
            interest=random.choice(interests),
            activity=random.choice(activities),
            music_type=random.choice(music_types),
            personality_type=random.choice(personality_types)
        )
        
        messages.append({
            "_id": f"msg_{random.randint(10000, 99999)}",
            "message": message,
            "from": "match" if i % 2 == 0 else "bot",
            "timestamp": time.time() - (count - i) * 60  # Messages spread over time
        })
    
    return messages

def test_complete_chat_flow():
    """Test complete chat flow with 10 messages"""
    print("🧪 Testing Complete Chat Flow (10 messages)...")
    
    try:
        from src.chat.chat import ChatManager
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Create mock API
        mock_api = Mock()
        mock_api.user_id = "bot_user_id"
        mock_api.send_message = Mock(return_value=True)
        
        # Create realistic mock match
        mock_match = create_mock_match("Anna", 24, ["Fitness", "Travel", "Photography"])
        mock_messages = create_mock_messages(10)
        
        # Create chat manager
        chat_manager = ChatManager(mock_api)
        chat_manager.match_id = mock_match["_id"]
        chat_manager.match_name = mock_match["person"]["name"]
        chat_manager.match_info = mock_match["person"]
        chat_manager.active = True
        
        print(f"   📝 Starting chat with {mock_match['person']['name']}")
        print(f"   🎯 Match interests: {', '.join([i['name'] for i in mock_match['person']['interests']])}")
        print(f"   💕 Relationship intent: {mock_match['person']['relationship_intent']}")
        
        # Simulate complete conversation
        conversation_results = []
        
        for i, msg in enumerate(mock_messages):
            print(f"\n   📨 Message {i+1}/10: {msg['message'][:50]}...")
            
            if msg['from'] == 'match':
                # Handle incoming message from match
                try:
                    chat_manager.handle_message(msg['message'], debug=True)
                    
                    # Check if response was generated
                    if len(chat_manager.chat_history.messages) > i:
                        last_message = chat_manager.chat_history.messages[-1]
                        if hasattr(last_message, 'content'):
                            response = last_message.content
                        else:
                            response = str(last_message)
                        
                        # Check if this is actually a bot response (AI message)
                        if hasattr(last_message, 'type') and last_message.type == 'ai':
                            conversation_results.append({
                                'message_number': i + 1,
                                'match_message': msg['message'],
                                'bot_response': response[:100] + "..." if len(response) > 100 else response,
                                'response_length': len(response.split()),
                                'status': 'success'
                            })
                            print(f"   ✅ Bot responded: {response[:50]}...")
                        else:
                            conversation_results.append({
                                'message_number': i + 1,
                                'match_message': msg['message'],
                                'bot_response': 'No AI response generated',
                                'response_length': 0,
                                'status': 'error'
                            })
                            print(f"   ❌ No AI response generated")
                    else:
                        conversation_results.append({
                            'message_number': i + 1,
                            'match_message': msg['message'],
                            'bot_response': 'No response generated',
                            'response_length': 0,
                            'status': 'error'
                        })
                        print(f"   ❌ No response generated")
                        
                except Exception as e:
                    conversation_results.append({
                        'message_number': i + 1,
                        'match_message': msg['message'],
                        'bot_response': f'Error: {str(e)}',
                        'response_length': 0,
                        'status': 'error'
                    })
                    print(f"   ❌ Error handling message: {e}")
            else:
                # Bot message - add to history
                chat_manager.chat_history.add_ai_message(AIMessage(content=msg['message']))
                conversation_results.append({
                    'message_number': i + 1,
                    'match_message': 'Bot message',
                    'bot_response': msg['message'],
                    'response_length': len(msg['message'].split()),
                    'status': 'bot_message'
                })
                print(f"   🤖 Bot message: {msg['message'][:50]}...")
                
                # Skip response generation for bot messages
                continue
        
        # Analyze results
        successful_responses = [r for r in conversation_results if r['status'] == 'success']
        error_responses = [r for r in conversation_results if r['status'] == 'error']
        bot_messages = [r for r in conversation_results if r['status'] == 'bot_message']
        
        avg_response_length = sum(r['response_length'] for r in successful_responses) / len(successful_responses) if successful_responses else 0
        
        print(f"\n   📊 CONVERSATION ANALYSIS:")
        print(f"   ✅ Successful responses: {len(successful_responses)}")
        print(f"   ❌ Errors: {len(error_responses)}")
        print(f"   🤖 Bot messages: {len(bot_messages)}")
        print(f"   📏 Average response length: {avg_response_length:.1f} words")
        
        return {
            'success': len(error_responses) == 0,
            'total_messages': len(conversation_results),
            'successful_responses': len(successful_responses),
            'error_responses': len(error_responses),
            'avg_response_length': avg_response_length,
            'conversation_results': conversation_results
        }
        
    except Exception as e:
        print(f"❌ Error in complete chat flow test: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def test_multiple_matches_conversation():
    """Test conversations with multiple different matches"""
    print("🧪 Testing Multiple Matches Conversation...")
    
    try:
        from src.chat.chat import ChatManager
        
        # Create multiple mock matches
        matches = [
            create_mock_match("Lisa", 23, ["Fitness", "Cooking"]),
            create_mock_match("Sarah", 26, ["Travel", "Photography"]),
            create_mock_match("Emma", 25, ["Music", "Art"])
        ]
        
        results = []
        
        for i, match in enumerate(matches):
            print(f"\n   👤 Testing conversation with {match['person']['name']} ({i+1}/{len(matches)})")
            
            # Create mock API for this match
            mock_api = Mock()
            mock_api.user_id = "bot_user_id"
            mock_api.send_message = Mock(return_value=True)
            
            # Create chat manager
            chat_manager = ChatManager(mock_api)
            chat_manager.match_id = match["_id"]
            chat_manager.match_name = match["person"]["name"]
            chat_manager.match_info = match["person"]
            chat_manager.active = True
            
            # Simulate 3 messages for each match
            match_messages = create_mock_messages(3)
            match_successful = 0
            match_errors = 0
            
            for j, msg in enumerate(match_messages):
                if msg['from'] == 'match':
                    try:
                        chat_manager.handle_message(msg['message'], debug=True)
                        match_successful += 1
                    except Exception as e:
                        match_errors += 1
                        print(f"   ❌ Error with {match['person']['name']}: {e}")
            
            results.append({
                'match_name': match['person']['name'],
                'match_interests': [i['name'] for i in match['person']['interests']],
                'relationship_intent': match['person']['relationship_intent'],
                'successful_responses': match_successful,
                'errors': match_errors,
                'success_rate': match_successful / (match_successful + match_errors) if (match_successful + match_errors) > 0 else 0
            })
        
        total_successful = sum(r['successful_responses'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        overall_success_rate = total_successful / (total_successful + total_errors) if (total_successful + total_errors) > 0 else 0
        
        print(f"\n   📊 MULTIPLE MATCHES ANALYSIS:")
        for result in results:
            print(f"   👤 {result['match_name']}: {result['successful_responses']}✅ {result['errors']}❌ ({result['success_rate']:.1%})")
        print(f"   📈 Overall success rate: {overall_success_rate:.1%}")
        
        return {
            'success': overall_success_rate > 0.8,  # 80% success rate threshold
            'total_matches': len(matches),
            'total_successful': total_successful,
            'total_errors': total_errors,
            'overall_success_rate': overall_success_rate,
            'match_results': results
        }
        
    except Exception as e:
        print(f"❌ Error in multiple matches test: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def test_message_cancellation_in_flow():
    """Test message cancellation during conversation flow"""
    print("🧪 Testing Message Cancellation in Flow...")
    
    try:
        from src.chat.chat import ChatManager
        
        # Create mock API
        mock_api = Mock()
        mock_api.user_id = "bot_user_id"
        mock_api.send_message = Mock(return_value=True)
        
        # Create chat manager
        chat_manager = ChatManager(mock_api)
        chat_manager.match_id = "test_match_cancel"
        chat_manager.match_name = "CancelTest"
        chat_manager.active = True
        
        # Start conversation
        chat_manager.handle_message("Hey, wie geht's?", debug=True)
        
        # Check if response is scheduled
        if chat_manager.match_id in chat_manager.response_timer.scheduled_responses:
            print("   ✅ Initial response scheduled")
            
            # Send another message quickly (should cancel previous response)
            chat_manager.handle_message("Was machst du so?", debug=True)
            
            # Check if previous response was cancelled
            if chat_manager.match_id not in chat_manager.response_timer.scheduled_responses:
                print("   ✅ Previous response was cancelled")
                return {'success': True, 'cancellation_working': True}
            else:
                print("   ❌ Previous response was not cancelled")
                return {'success': False, 'cancellation_working': False}
        else:
            print("   ❌ No response was scheduled")
            return {'success': False, 'cancellation_working': False}
        
    except Exception as e:
        print(f"❌ Error in message cancellation test: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Run all complete chat flow tests"""
    print("🚀 Starting Complete Chat Flow Tests")
    print("=" * 60)
    
    tests = [
        test_complete_chat_flow,
        test_multiple_matches_conversation,
        test_message_cancellation_in_flow
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append({'success': False, 'error': str(e)})
        
        print("-" * 40)
    
    # Generate professional summary
    print("\n" + "=" * 60)
    print("📊 PROFESSIONAL TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('success', False))
    failed_tests = total_tests - successful_tests
    
    print(f"🎯 OVERALL RESULTS:")
    print(f"   ✅ Successful Tests: {successful_tests}/{total_tests}")
    print(f"   ❌ Failed Tests: {failed_tests}/{total_tests}")
    print(f"   📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETAILED BREAKDOWN:")
    
    for i, result in enumerate(results):
        test_name = tests[i].__name__.replace('test_', '').replace('_', ' ').title()
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        
        print(f"   {i+1}. {test_name}: {status}")
        
        if 'error' in result:
            print(f"      Error: {result['error']}")
        elif 'conversation_results' in result:
            print(f"      Messages: {result['total_messages']}, Success: {result['successful_responses']}, Errors: {result['error_responses']}")
        elif 'match_results' in result:
            print(f"      Matches: {result['total_matches']}, Success Rate: {result['overall_success_rate']:.1%}")
        elif 'cancellation_working' in result:
            print(f"      Cancellation: {'Working' if result['cancellation_working'] else 'Not Working'}")
    
    print(f"\n🔍 KEY FINDINGS:")
    
    # Analyze conversation quality
    chat_flow_result = next((r for r in results if 'conversation_results' in r), None)
    if chat_flow_result and chat_flow_result.get('success'):
        avg_length = chat_flow_result.get('avg_response_length', 0)
        print(f"   💬 Average response length: {avg_length:.1f} words")
        if avg_length > 0:
            print(f"   📝 Response quality: {'Good' if 5 <= avg_length <= 20 else 'Needs adjustment'}")
    
    # Analyze multiple matches performance
    multi_match_result = next((r for r in results if 'match_results' in r), None)
    if multi_match_result:
        success_rate = multi_match_result.get('overall_success_rate', 0)
        print(f"   👥 Multi-match success rate: {success_rate:.1%}")
        print(f"   🎯 Performance: {'Excellent' if success_rate >= 0.9 else 'Good' if success_rate >= 0.8 else 'Needs improvement'}")
    
    # Analyze cancellation functionality
    cancellation_result = next((r for r in results if 'cancellation_working' in r), None)
    if cancellation_result:
        print(f"   🔄 Message cancellation: {'Working correctly' if cancellation_result.get('cancellation_working') else 'Not working'}")
    
    print(f"\n📊 FINAL ASSESSMENT:")
    if successful_tests == total_tests:
        print("   🎉 ALL TESTS PASSED - System is working excellently!")
        print("   ✅ Chat flow is robust and reliable")
        print("   ✅ Message cancellation is functioning properly")
        print("   ✅ Multi-match handling is working correctly")
    elif successful_tests >= total_tests * 0.8:
        print("   👍 MOST TESTS PASSED - System is working well with minor issues")
        print("   ⚠️  Some areas may need attention")
    else:
        print("   ⚠️  MANY TESTS FAILED - System needs significant attention")
        print("   🔧 Review failed tests and fix issues")
    
    print("=" * 60)
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
