#!/usr/bin/env python3
"""
Test Logger for TinderBot
Saves comprehensive test results to structured JSON logs
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

class TestLogger:
    def __init__(self, version="1.0.0"):
        self.version = version
        self.testlogs_dir = Path("testlogs")
        self.testlogs_dir.mkdir(exist_ok=True)
        
        # Create log structure
        self.log_data = {
            "test_session": {
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            },
            "test_results": {},
            "api_tests": {},
            "llm_tests": {},
            "performance_metrics": {},
            "errors": [],
            "warnings": []
        }
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f"{timestamp}_v{version}_testlog.json"
        self.filepath = self.testlogs_dir / self.filename
    
    def log_test_result(self, test_name, success, message="", details=None, 
                       test_input="", test_output="", expected_output="",
                       conversation_log=None, api_responses=None, llm_interactions=None,
                       dynamic_adjustments=None, timing_data=None, test_category="general"):
        """Log detailed test result with comprehensive information"""
        test_entry = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "test_category": test_category,
            "details": details or {},
            "test_input": test_input,
            "test_output": test_output,
            "expected_output": expected_output,
            "conversation_log": conversation_log or [],
            "api_responses": api_responses or [],
            "llm_interactions": llm_interactions or [],
            "dynamic_adjustments": dynamic_adjustments or {},
            "timing_data": timing_data or {},
            "analysis": {
                "input_analysis": self._analyze_input(test_input),
                "output_analysis": self._analyze_output(test_output),
                "conversation_analysis": self._analyze_conversation(conversation_log),
                "dynamic_analysis": self._analyze_dynamics(dynamic_adjustments),
                "timing_analysis": self._analyze_timing(timing_data)
            }
        }
        
        self.log_data["test_results"][test_name] = test_entry
        
        # Also log to console with detailed information
        status = "PASS" if success else "FAIL"
        print(f"\n{status} {test_name}: {message}")
        print(f"  Category: {test_category}")
        
        # Log detailed information if available
        if test_input:
            print(f"  Input: {test_input[:100]}...")
        if test_output:
            print(f"  Output: {test_output[:100]}...")
        if conversation_log:
            print(f"  Conversation: {len(conversation_log)} messages logged")
        if api_responses:
            print(f"  API Calls: {len(api_responses)} responses logged")
        if dynamic_adjustments:
            print(f"  Dynamic Adjustments: {len(dynamic_adjustments)} parameters adjusted")
        if timing_data:
            print(f"  Timing: {len(timing_data)} timing measurements")
    
    def _analyze_input(self, test_input):
        """Analyze test input for patterns and characteristics"""
        if not test_input:
            return {"status": "no_input", "length": 0, "type": "none"}
        
        analysis = {
            "status": "analyzed",
            "length": len(str(test_input)),
            "type": type(test_input).__name__,
            "characteristics": {}
        }
        
        if isinstance(test_input, str):
            analysis["characteristics"] = {
                "word_count": len(test_input.split()),
                "char_count": len(test_input),
                "has_emoji": any(ord(c) > 127 for c in test_input),
                "has_question": "?" in test_input,
                "has_exclamation": "!" in test_input,
                "avg_word_length": sum(len(word) for word in test_input.split()) / max(len(test_input.split()), 1)
            }
        
        return analysis
    
    def _analyze_output(self, test_output):
        """Analyze test output for patterns and characteristics"""
        if not test_output:
            return {"status": "no_output", "length": 0, "type": "none"}
        
        analysis = {
            "status": "analyzed",
            "length": len(str(test_output)),
            "type": type(test_output).__name__,
            "characteristics": {}
        }
        
        if isinstance(test_output, str):
            analysis["characteristics"] = {
                "word_count": len(test_output.split()),
                "char_count": len(test_output),
                "has_emoji": any(ord(c) > 127 for c in test_output),
                "has_question": "?" in test_output,
                "has_exclamation": "!" in test_output,
                "avg_word_length": sum(len(word) for word in test_output.split()) / max(len(test_output.split()), 1),
                "response_style": self._classify_response_style(test_output)
            }
        
        return analysis
    
    def _analyze_conversation(self, conversation_log):
        """Analyze conversation log for patterns and flow"""
        if not conversation_log:
            return {"status": "no_conversation", "message_count": 0, "flow": "none"}
        
        analysis = {
            "status": "analyzed",
            "message_count": len(conversation_log),
            "flow": "conversation",
            "participants": set(),
            "message_types": {},
            "conversation_phases": [],
            "engagement_metrics": {}
        }
        
        for msg in conversation_log:
            if isinstance(msg, dict):
                # Extract participant
                if "sender" in msg:
                    analysis["participants"].add(msg["sender"])
                
                # Analyze message type
                msg_type = msg.get("type", "unknown")
                analysis["message_types"][msg_type] = analysis["message_types"].get(msg_type, 0) + 1
                
                # Analyze content
                content = msg.get("content", "")
                if "?" in content:
                    analysis["message_types"]["question"] = analysis["message_types"].get("question", 0) + 1
                if any(ord(c) > 127 for c in content):
                    analysis["message_types"]["emoji"] = analysis["message_types"].get("emoji", 0) + 1
        
        analysis["participants"] = list(analysis["participants"])
        return analysis
    
    def _analyze_dynamics(self, dynamic_adjustments):
        """Analyze dynamic adjustments for patterns and effectiveness"""
        if not dynamic_adjustments:
            return {"status": "no_adjustments", "parameter_count": 0, "types": []}
        
        analysis = {
            "status": "analyzed",
            "parameter_count": len(dynamic_adjustments),
            "types": list(dynamic_adjustments.keys()),
            "adjustment_values": {},
            "effectiveness_metrics": {}
        }
        
        for param, value in dynamic_adjustments.items():
            if isinstance(value, (int, float)):
                analysis["adjustment_values"][param] = {
                    "value": value,
                    "type": "numeric",
                    "range": "normal" if 0 <= value <= 100 else "extreme"
                }
            elif isinstance(value, str):
                analysis["adjustment_values"][param] = {
                    "value": value,
                    "type": "categorical",
                    "category": self._categorize_dynamic_value(value)
                }
        
        return analysis
    
    def _analyze_timing(self, timing_data):
        """Analyze timing data for patterns and performance"""
        if not timing_data:
            return {"status": "no_timing", "measurement_count": 0, "metrics": {}}
        
        analysis = {
            "status": "analyzed",
            "measurement_count": len(timing_data),
            "metrics": {},
            "performance_analysis": {}
        }
        
        if isinstance(timing_data, dict):
            for metric, value in timing_data.items():
                if isinstance(value, (int, float)):
                    analysis["metrics"][metric] = {
                        "value": value,
                        "unit": "seconds" if "time" in metric.lower() else "unknown",
                        "performance": "fast" if value < 1.0 else "normal" if value < 5.0 else "slow"
                    }
        
        return analysis
    
    def _classify_response_style(self, text):
        """Classify response style based on content"""
        if not text:
            return "empty"
        
        text_lower = text.lower()
        
        if len(text) < 20:
            return "short"
        elif len(text) < 100:
            return "medium"
        else:
            return "long"
        
        if "?" in text:
            return "questioning"
        elif "!" in text:
            return "enthusiastic"
        elif any(word in text_lower for word in ["danke", "thanks", "merci"]):
            return "grateful"
        else:
            return "informative"
    
    def _categorize_dynamic_value(self, value):
        """Categorize dynamic adjustment values"""
        value_lower = value.lower()
        
        if any(word in value_lower for word in ["low", "niedrig", "min"]):
            return "low"
        elif any(word in value_lower for word in ["high", "hoch", "max"]):
            return "high"
        elif any(word in value_lower for word in ["medium", "mittel", "normal"]):
            return "medium"
        else:
            return "custom"
    
    def log_api_test(self, api_name, success, response_time=None, status_code=None, details=None):
        """Log API test results"""
        self.log_data["api_tests"][api_name] = {
            "success": success,
            "response_time": response_time,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
    
    def log_llm_test(self, test_name, success, prompt="", response="", response_time=None, details=None,
                     model_used="", tokens_used=None, cost_estimate=None, conversation_context=None):
        """Log comprehensive LLM test results"""
        llm_entry = {
            "success": success,
            "prompt": prompt,
            "response": response,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat(),
            "model_used": model_used,
            "tokens_used": tokens_used,
            "cost_estimate": cost_estimate,
            "conversation_context": conversation_context or [],
            "details": details or {},
            "analysis": {
                "prompt_analysis": self._analyze_input(prompt),
                "response_analysis": self._analyze_output(response),
                "performance_metrics": {
                    "response_time_category": "fast" if response_time and response_time < 2.0 else "normal" if response_time and response_time < 10.0 else "slow",
                    "response_quality": self._assess_response_quality(response),
                    "prompt_complexity": self._assess_prompt_complexity(prompt)
                }
            }
        }
        
        self.log_data["llm_tests"][test_name] = llm_entry
        
        # Log to console with detailed information
        status = "PASS" if success else "FAIL"
        print(f"\n{status} LLM Test {test_name}:")
        print(f"  Model: {model_used}")
        print(f"  Response Time: {response_time:.2f}s" if response_time else "  Response Time: N/A")
        print(f"  Tokens: {tokens_used}" if tokens_used else "  Tokens: N/A")
        print(f"  Cost: {cost_estimate}" if cost_estimate else "  Cost: N/A")
        print(f"  Prompt Length: {len(prompt)} chars")
        print(f"  Response Length: {len(response)} chars")
    
    def _assess_response_quality(self, response):
        """Assess the quality of an LLM response"""
        if not response:
            return "empty"
        
        # Check for common quality indicators
        response_lower = response.lower()
        
        if len(response) < 10:
            return "too_short"
        elif len(response) > 1000:
            return "too_long"
        elif "sorry" in response_lower or "error" in response_lower:
            return "error_response"
        elif "?" in response:
            return "questioning"
        elif "!" in response:
            return "enthusiastic"
        elif any(word in response_lower for word in ["danke", "thanks", "merci", "appreciate"]):
            return "grateful"
        else:
            return "informative"
    
    def _assess_prompt_complexity(self, prompt):
        """Assess the complexity of a prompt"""
        if not prompt:
            return "empty"
        
        word_count = len(prompt.split())
        char_count = len(prompt)
        
        if word_count < 5:
            return "very_simple"
        elif word_count < 20:
            return "simple"
        elif word_count < 50:
            return "moderate"
        elif word_count < 100:
            return "complex"
        else:
            return "very_complex"
    
    def log_performance_metric(self, metric_name, value, unit=""):
        """Log performance metrics"""
        self.log_data["performance_metrics"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_error(self, error_type, message, details=None):
        """Log errors"""
        error_entry = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.log_data["errors"].append(error_entry)
    
    def log_warning(self, warning_type, message, details=None):
        """Log warnings"""
        warning_entry = {
            "type": warning_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.log_data["warnings"].append(warning_entry)
    
    def save_log(self):
        """Save log to file"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.log_data, f, indent=2, ensure_ascii=False)
            
            print(f"Test log saved: {self.filepath}")
            return True
        except Exception as e:
            print(f"Failed to save test log: {e}")
            return False
    
    def get_summary(self):
        """Get test summary"""
        total_tests = len(self.log_data["test_results"])
        passed_tests = sum(1 for test in self.log_data["test_results"].values() if test["success"])
        failed_tests = total_tests - passed_tests
        
        total_apis = len(self.log_data["api_tests"])
        passed_apis = sum(1 for api in self.log_data["api_tests"].values() if api["success"])
        
        total_llms = len(self.log_data["llm_tests"])
        passed_llms = sum(1 for llm in self.log_data["llm_tests"].values() if llm["success"])
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_apis": total_apis,
            "passed_apis": passed_apis,
            "total_llms": total_llms,
            "passed_llms": passed_llms,
            "errors": len(self.log_data["errors"]),
            "warnings": len(self.log_data["warnings"])
        }
    
    def print_summary(self):
        """Print comprehensive test summary with categorization"""
        summary = self.get_summary()
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
        print(f"APIs: {summary['passed_apis']}/{summary['total_apis']} working")
        print(f"LLMs: {summary['passed_llms']}/{summary['total_llms']} working")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Log file: {self.filepath}")
        
        # Show test results by category
        if self.log_data["test_results"]:
            print("\n" + "=" * 80)
            print("DETAILED TEST RESULTS BY CATEGORY")
            print("=" * 80)
            
            categories = {}
            for test_name, test_data in self.log_data["test_results"].items():
                category = test_data.get("test_category", "general")
                if category not in categories:
                    categories[category] = []
                categories[category].append((test_name, test_data))
            
            for category, tests in categories.items():
                print(f"\n📁 {category.upper()} CATEGORY:")
                passed = sum(1 for _, test in tests if test["success"])
                total = len(tests)
                print(f"  Status: {passed}/{total} tests passed")
                
                for test_name, test_data in tests:
                    status = "✅ PASS" if test_data["success"] else "❌ FAIL"
                    print(f"    {status} {test_name}: {test_data['message']}")
                    
                    # Show key metrics
                    if test_data.get("dynamic_adjustments"):
                        print(f"      🔄 Dynamic Adjustments: {len(test_data['dynamic_adjustments'])} parameters")
                    if test_data.get("timing_data"):
                        print(f"      ⏱️  Timing: {len(test_data['timing_data'])} measurements")
                    if test_data.get("conversation_log"):
                        print(f"      💬 Conversation: {len(test_data['conversation_log'])} messages")
                    if test_data.get("llm_interactions"):
                        print(f"      🤖 LLM: {len(test_data['llm_interactions'])} interactions")
        
        # Show API test results
        if self.log_data["api_tests"]:
            print("\n" + "=" * 80)
            print("API TEST RESULTS")
            print("=" * 80)
            for api_name, api_data in self.log_data["api_tests"].items():
                status = "✅ PASS" if api_data["success"] else "❌ FAIL"
                response_time = f"{api_data['response_time']:.2f}s" if api_data.get("response_time") else "N/A"
                print(f"  {status} {api_name}: Response time: {response_time}")
        
        # Show LLM test results
        if self.log_data["llm_tests"]:
            print("\n" + "=" * 80)
            print("LLM TEST RESULTS")
            print("=" * 80)
            for llm_name, llm_data in self.log_data["llm_tests"].items():
                status = "✅ PASS" if llm_data["success"] else "❌ FAIL"
                model = llm_data.get("model_used", "Unknown")
                response_time = f"{llm_data['response_time']:.2f}s" if llm_data.get("response_time") else "N/A"
                tokens = llm_data.get("tokens_used", "N/A")
                print(f"  {status} {llm_name}: Model: {model}, Time: {response_time}, Tokens: {tokens}")
        
        # Show errors and warnings
        if summary['errors'] > 0:
            print("\n" + "=" * 80)
            print("❌ ERRORS")
            print("=" * 80)
            for error in self.log_data["errors"]:
                print(f"  - {error['type']}: {error['message']}")
                if error.get("details"):
                    print(f"    Details: {error['details']}")
        
        if summary['warnings'] > 0:
            print("\n" + "=" * 80)
            print("⚠️  WARNINGS")
            print("=" * 80)
            for warning in self.log_data["warnings"]:
                print(f"  - {warning['type']}: {warning['message']}")
                if warning.get("details"):
                    print(f"    Details: {warning['details']}")
        
        print("\n" + "=" * 80)
        print("END OF TEST SUMMARY")
        print("=" * 80)

def get_latest_testlog():
    """Get the most recent test log file"""
    testlogs_dir = Path("testlogs")
    if not testlogs_dir.exists():
        return None
    
    log_files = list(testlogs_dir.glob("*_testlog.json"))
    if not log_files:
        return None
    
    # Sort by modification time (newest first)
    latest_file = max(log_files, key=lambda f: f.stat().st_mtime)
    return latest_file

def load_testlog(filepath):
    """Load test log from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load test log: {e}")
        return None
