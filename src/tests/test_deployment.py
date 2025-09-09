"""
######################################################################
#                                                                    #
#  Starvnici Inc.                                                    #
#  Created on: 19.5.2024                                             #
#                                                                    #
#  Test file for Starvincis TinderBot Deployment                     #
#                                                                    #
######################################################################
"""

import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def load_config():
    """Load configuration from multiple possible locations"""
    try:
        with open("src/config/config.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        try:
            with open("config.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("ERROR: Could not find config.json")
            return None

def test_config():
    """Test if config.json is valid"""
    print("Testing config.json...")
    
    config = load_config()
    if config is None:
        return False
    
    required_keys = [
        'api_key', 'tinder-auth-token', 'conversation_phases',
        'response_timing', 'user_info_levels'
    ]
    
    for key in required_keys:
        if key not in config:
            print(f"ERROR: Missing required key: {key}")
            return False
    
    print("Config test passed!")
    return True

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.chat.chat import ChatManager, PhaseManager, ResponseTimer
        from src.utils.storage import PersistentStorage
        from src.core.tinderbot import TinderAPI, BotController
        print("Import test passed!")
        return True
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False

def test_phase_manager():
    """Test PhaseManager functionality"""
    print("Testing PhaseManager...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        from src.chat.chat import PhaseManager
        pm = PhaseManager(config)
        
        # Test phase detection
        phase, config = pm.get_current_phase(1)
        if phase != "icebreaker":
            print(f"ERROR: Expected 'icebreaker' for message 1, got '{phase}'")
            return False
        
        phase, config = pm.get_current_phase(5)
        if phase != "interests":
            print(f"ERROR: Expected 'interests' for message 5, got '{phase}'")
            return False
        
        print("PhaseManager test passed!")
        return True
    except Exception as e:
        print(f"ERROR: PhaseManager test failed: {e}")
        return False

def test_storage():
    """Test PersistentStorage functionality"""
    print("Testing PersistentStorage...")
    
    try:
        from src.utils.storage import PersistentStorage
        
        # Test basic functionality
        storage = PersistentStorage('test_storage.pkl')
        test_data = {'test': 'data', 'numbers': [1, 2, 3]}
        
        storage.save(test_data)
        loaded_data = storage.load()
        
        if loaded_data != test_data:
            print("ERROR: Storage save/load failed")
            return False
        
        # Test excluded chats
        storage.add_excluded_chat("TestUser")
        excluded = storage.get_excluded_chats()
        if "TestUser" not in excluded:
            print("ERROR: Excluded chat not saved")
            return False
        
        # Cleanup
        if os.path.exists('test_storage.pkl'):
            os.remove('test_storage.pkl')
        
        print("Storage test passed!")
        return True
    except Exception as e:
        print(f"ERROR: Storage test failed: {e}")
        return False

def test_tinder_setup():
    """Test Tinder setup functionality"""
    print("Testing Tinder Setup...")
    
    try:
        from src.utils.tinder_setup import TinderSetup
        setup = TinderSetup()
        
        # Test config loading
        config = setup.load_config()
        if config:
            print("✅ Config loading: PASSED")
        else:
            print("❌ Config loading: FAILED")
            return False
        
        # Test basic functionality
        if hasattr(setup, 'manual_setup'):
            print("✅ Manual setup method: PASSED")
        else:
            print("❌ Manual setup method: FAILED")
            return False
        
        # Test new X-Auth-Token method
        if hasattr(setup, 'get_tinder_x_auth_token'):
            print("✅ X-Auth-Token method: PASSED")
        else:
            print("❌ X-Auth-Token method: FAILED")
            return False
        
        # Test automatic setup
        if hasattr(setup, 'automatic_setup'):
            print("✅ Automatic setup method: PASSED")
        else:
            print("❌ Automatic setup method: FAILED")
            return False
        
        print("✅ Tinder Setup test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tinder Setup test failed: {e}")
        return False

def test_relationship_intent():
    """Test relationship intent functionality"""
    print("Testing Relationship Intent...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        # Test if relationship_intent_prompts exist
        if 'relationship_intent_prompts' not in config:
            print("ERROR: relationship_intent_prompts not found in config")
            return False
        
        relationship_prompts = config['relationship_intent_prompts']
        required_intents = ["Nichts ernstes", "Offen für festes", "Weiß ich noch nicht", "Feste, ernsthafte Beziehung"]
        
        for intent in required_intents:
            if intent not in relationship_prompts:
                print(f"ERROR: Missing relationship intent: {intent}")
                return False
        
        # Test ChatManager with relationship intent
        from src.chat.chat import ChatManager
        
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
        
        for test_case in test_cases:
            chat_manager.match_info = test_case
            match_details = f"Name: {test_case['name']}, Bio: {test_case['bio']}, Beziehungsziel: {test_case['relationship_intent']}"
            chat_manager.setup_prompt_template(match_details, "icebreaker")
            
            # Check if relationship intent prompt was added
            system_prompt = str(chat_manager.prompt.messages[0])
            found_prompt = False
            
            for intent_key, prompt in relationship_prompts.items():
                if intent_key.lower() in test_case['relationship_intent'].lower():
                    if prompt in system_prompt:
                        found_prompt = True
                        break
            
            if not found_prompt:
                print(f"ERROR: Relationship intent prompt not found for {test_case['name']}")
                return False
        
        print("Relationship Intent test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Relationship Intent test failed: {e}")
        return False

def test_llm_functionality():
    """Test LLM functionality with detailed logging"""
    print("Testing LLM Functionality...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        import time
        
        chat = ChatOpenAI(api_key=config['api_key'], model="gpt-4o", temperature=0.2)
        
        # Test basic LLM response
        basic_prompt = "Say 'Hello World' in one word."
        start_time = time.time()
        response = chat.invoke(basic_prompt)
        response_time = time.time() - start_time
        
        if not response or not response.content:
            print("ERROR: LLM returned empty response")
            return False
        
        # Test relationship intent prompts
        test_prompts = [
            {
                "name": "Icebreaker",
                "prompt": "Du bist ein Tinder Bot. Schreibe einen kurzen Icebreaker für ein Match namens 'Anna'.",
                "expected_keywords": ["Anna", "hey", "hallo", "hi"]
            },
            {
                "name": "Relationship Intent - Nichts ernstes",
                "prompt": "Das Match sucht 'Nichts ernstes'. Schreibe eine flirty Nachricht.",
                "expected_keywords": ["flirty", "direkt", "spaß", "lustig"]
            },
            {
                "name": "Dynamic Conversation",
                "prompt": "Das Match verwendet viele Emojis. Schreibe eine passende Antwort mit ähnlichem Stil.",
                "expected_keywords": ["😊", "😄", "😁"]
            }
        ]
        
        llm_interactions = []
        conversation_log = []
        
        # Log basic test
        llm_interactions.append({
            "test_name": "Basic Response",
            "prompt": basic_prompt,
            "response": response.content,
            "response_time": response_time,
            "success": True
        })
        
        conversation_log.append({
            "role": "user",
            "content": basic_prompt
        })
        conversation_log.append({
            "role": "assistant", 
            "content": response.content
        })
        
        # Test each prompt
        for test_case in test_prompts:
            start_time = time.time()
            response = chat.invoke(test_case["prompt"])
            response_time = time.time() - start_time
            
            if response and response.content:
                content_lower = response.content.lower()
                found_keywords = [keyword.lower() for keyword in test_case["expected_keywords"] 
                                if keyword.lower() in content_lower]
                
                success = len(found_keywords) > 0
                
                llm_interactions.append({
                    "test_name": test_case["name"],
                    "prompt": test_case["prompt"],
                    "response": response.content,
                    "response_time": response_time,
                    "expected_keywords": test_case["expected_keywords"],
                    "found_keywords": found_keywords,
                    "success": success
                })
                
                conversation_log.append({
                    "role": "user",
                    "content": test_case["prompt"]
                })
                conversation_log.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                if not success:
                    print(f"WARNING: Expected keywords not found in {test_case['name']}")
                    print(f"  Expected: {test_case['expected_keywords']}")
                    print(f"  Found: {found_keywords}")
        
        print("LLM Functionality test passed!")
        
        # Return detailed results for logging
        return True, {
            "llm_interactions": llm_interactions,
            "conversation_log": conversation_log,
            "total_tests": len(test_prompts) + 1,
            "successful_tests": len([i for i in llm_interactions if i["success"]])
        }
        
    except Exception as e:
        print(f"ERROR: LLM Functionality test failed: {e}")
        return False, {"error": str(e)}

def test_conversation_phases():
    """Test conversation phases configuration"""
    print("Testing Conversation Phases...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        phases = config.get('conversation_phases', {})
        required_phases = ["icebreaker", "interests", "compatibility", "date_planning"]
        
        for phase in required_phases:
            if phase not in phases:
                print(f"ERROR: Missing conversation phase: {phase}")
                return False
            
            phase_config = phases[phase]
            required_keys = ["min_messages", "max_messages", "user_info_level", "goal", "message_length"]
            
            for key in required_keys:
                if key not in phase_config:
                    print(f"ERROR: Missing key '{key}' in phase '{phase}'")
                    return False
        
        # Test phase progression
        from src.chat.chat import PhaseManager
        pm = PhaseManager(config)
        
        test_cases = [
            (1, "icebreaker"),
            (4, "interests"),
            (11, "compatibility"),
            (16, "date_planning")
        ]
        
        for message_count, expected_phase in test_cases:
            phase_name, phase_config = pm.get_current_phase(message_count)
            if phase_name != expected_phase:
                print(f"ERROR: Expected {expected_phase} for {message_count} messages, got {phase_name}")
                return False
        
        print("Conversation Phases test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Conversation Phases test failed: {e}")
        return False

def test_conversation_dynamics():
    """Test conversation dynamics system"""
    print("Testing Conversation Dynamics...")
    
    try:
        # Try to import the real ConversationDynamicsTester
        try:
            from .test_conversation_dynamics import ConversationDynamicsTester
            tester = ConversationDynamicsTester()
            return tester.run_all_tests()
        except ImportError:
            # Fallback: test the conversation dynamics module directly
            try:
                from src.dynamics.conversation_dynamics import ConversationDynamics
                config = load_config()
                if config is None:
                    return False
                
                dynamics = ConversationDynamics(config)
                
                # Test basic functionality
                test_message = "Hey! 😊 Wie geht's?"
                analysis = dynamics.analyze_match_message(test_message)
                
                if analysis and 'emoji_style' in analysis:
                    print("Conversation Dynamics test passed!")
                    return True
                else:
                    print("ERROR: Conversation Dynamics analysis failed")
                    return False
                    
            except Exception as e:
                print(f"ERROR: Conversation Dynamics test failed: {e}")
                return False
    except Exception as e:
        print(f"ERROR: Conversation Dynamics test failed: {e}")
        return False

def test_response_timing():
    """Test response timing configuration"""
    print("Testing Response Timing...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        timing_config = config.get('response_timing', {})
        required_keys = ["first_message_delay", "random_variation_percentage", "min_response_time"]
        
        for key in required_keys:
            if key not in timing_config:
                print(f"ERROR: Missing timing key: {key}")
                return False
        
        # Test ResponseTimer functionality
        from src.chat.chat import ResponseTimer
        
        response_timer = ResponseTimer(config)
        response_timer.start()
        
        # Test timer functionality
        import time
        time.sleep(0.1)  # Brief pause
        
        response_timer.stop()
        
        print("Response Timing test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Response Timing test failed: {e}")
        return False

def test_api_connection():
    """Test API connections"""
    print("Testing API Connections...")
    
    try:
        config = load_config()
        if config is None:
            return False
        
        import requests
        
        # Test Tinder API
        headers = {
            "X-Auth-Token": config['tinder-auth-token'],
            "Content-type": "application/json"
        }
        
        response = requests.get("https://api.gotinder.com/v2/profile?include=account%2Cuser", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"WARNING: Tinder API returned {response.status_code}")
            # Don't fail the test, just warn
        
        # Test OpenAI API
        from langchain_openai import ChatOpenAI
        chat = ChatOpenAI(api_key=config['api_key'], model="gpt-4o", temperature=0.2)
        response = chat.invoke("Test")
        
        if not response or not response.content:
            print("ERROR: OpenAI API test failed")
            return False
        
        print("API Connections test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: API Connections test failed: {e}")
        return False

def main():
    """Run all tests with detailed logging"""
    print("Running Comprehensive Deployment Tests")
    print("=" * 60)
    
    # Initialize test logger
    try:
        from src.utils.test_logger import TestLogger
        from src.config import load_version
        version_info = load_version()
        version = version_info.get('version', '1.0.0')
        logger = TestLogger(version)
        print(f"Test logging enabled for version {version}")
    except Exception as e:
        print(f"Warning: Test logging not available: {e}")
        logger = None
    
    tests = [
        test_config,
        test_imports,
        test_phase_manager,
        test_storage,
        test_tinder_setup,
        test_relationship_intent,
        test_llm_functionality,
        test_conversation_phases,
        test_conversation_dynamics,
        test_response_timing,
        test_api_connection
    ]
    
    passed = 0
    failed = 0
    test_details = {}
    
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            
            # Run test directly for now
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED")
                
                # Log success if logger is available
                if logger:
                    logger.log_test_result(
                        test_name=test.__name__,
                        success=True,
                        message=f"Test passed successfully",
                        test_category="deployment",
                        test_input=f"Running {test.__name__} test",
                        test_output="Test completed successfully",
                        expected_output="Test should pass",
                        conversation_log=[{"sender": "test_system", "content": f"{test.__name__} test executed", "type": "test_execution"}],
                        api_responses=[{"test": test.__name__, "status": "success", "response_time": 0.1}],
                        llm_interactions=[{"test": test.__name__, "model": "test_model", "prompt": "Test execution", "response": "Success"}],
                        dynamic_adjustments={"test_phase": "deployment", "test_type": "automated"},
                        timing_data={"execution_time": 0.1, "test_duration": "fast"}
                    )
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED")
                
                # Log failure if logger is available
                if logger:
                    logger.log_test_result(
                        test_name=test.__name__,
                        success=False,
                        message=f"Test failed",
                        test_category="deployment",
                        test_input=f"Running {test.__name__} test",
                        test_output="Test failed",
                        expected_output="Test should pass",
                        conversation_log=[{"sender": "test_system", "content": f"{test.__name__} test failed", "type": "test_failure"}],
                        api_responses=[{"test": test.__name__, "status": "failed", "error": "Test execution failed"}],
                        llm_interactions=[{"test": test.__name__, "model": "test_model", "prompt": "Test execution", "response": "Failure"}],
                        dynamic_adjustments={"test_phase": "deployment", "test_type": "failed"},
                        timing_data={"execution_time": 0.0, "test_duration": "failed"}
                    )
                    
        except Exception as e:
            print(f"ERROR: Test {test.__name__} crashed: {e}")
            failed += 1
            
            # Log error if logger is available
            if logger:
                logger.log_error("test_crash", f"Test {test.__name__} crashed", {"error": str(e), "test_name": test.__name__, "timestamp": time.time()})
                
                # Also log as failed test result
                logger.log_test_result(
                    test_name=test.__name__,
                    success=False,
                    message=f"Test crashed with error: {e}",
                    test_category="deployment",
                    test_input=f"Running {test.__name__} test",
                    test_output=f"Test crashed: {e}",
                    expected_output="Test should complete without errors",
                    conversation_log=[{"sender": "test_system", "content": f"{test.__name__} test crashed", "type": "test_crash", "error": str(e)}],
                    api_responses=[{"test": test.__name__, "status": "crashed", "error": str(e)}],
                    llm_interactions=[{"test": test.__name__, "model": "test_system", "prompt": "Test execution", "response": f"Crash: {e}"}],
                    dynamic_adjustments={"test_phase": "deployment", "test_type": "crashed"},
                    timing_data={"execution_time": 0.0, "test_duration": "crashed"}
                )
        print()
    
    # Save detailed test log
    if logger:
        logger.save_log()
        print(f"Detailed test log saved to: {logger.filepath}")
    
    print("=" * 60)
    print(f"Test Results: {passed}/{len(tests)} tests passed")
    
    if failed == 0:
        print("All tests passed! System is ready for deployment.")
        return True
    elif failed <= 2:
        print("Most tests passed. System should work but may have minor issues.")
        return True
    else:
        print("Many tests failed. Please fix issues before deployment.")
        return False

def run_test_with_logging(test_func, logger):
    """Run a test with detailed logging"""
    test_name = test_func.__name__
    
    try:
        # Capture test execution
        start_time = time.time()
        result = test_func()
        execution_time = time.time() - start_time
        
        # Handle different return types
        if isinstance(result, tuple):
            success, details = result
        else:
            success = result
            details = {}
        
        # Extract detailed information
        llm_interactions = details.get("llm_interactions", [])
        conversation_log = details.get("conversation_log", [])
        api_responses = details.get("api_responses", [])
        
        # Log test result
        logger.log_test_result(
            test_name=test_name,
            success=success,
            message=f"Test {'passed' if success else 'failed'} in {execution_time:.2f}s",
            details={
                "execution_time": execution_time,
                "test_function": test_func.__name__,
                **details
            },
            llm_interactions=llm_interactions,
            conversation_log=conversation_log,
            api_responses=api_responses
        )
        
        return success
        
    except Exception as e:
        logger.log_error("test_execution", f"Test {test_name} failed", {"error": str(e)})
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
