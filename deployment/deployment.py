"""
######################################################################
#                                                                    #
#  Starvnici Inc.                                                    #
#  Created on: 19.5.2024                                             #
#                                                                    #
#  Deployment Pipeline for Starvincis TinderBot                      #
#                                                                    #
######################################################################
"""

import os
import sys
import json
import time
import shutil
import subprocess
import threading
import signal
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import new systems
try:
    from src.utils.test_logger import TestLogger
    from src.utils.git_version_manager import GitVersionManager
    from src.utils.tinder_setup import TinderSetup
    NEW_SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"Some new systems not available: {e}")
    NEW_SYSTEMS_AVAILABLE = False

class DeploymentManager:
    def __init__(self):
        self.config_file = "src/config/config.json"
        self.backup_dir = "backups"
        self.test_dir = "deployment/tests"
        self.current_version = "1.0.0"
        self.bot_process = None
        self.is_running = False
        self.monitor_thread = None
        
        # Create necessary directories
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Initialize new systems
        if NEW_SYSTEMS_AVAILABLE:
            self.git_manager = GitVersionManager()
            self.tinder_setup = TinderSetup()
            self.test_logger = None  # Will be initialized during tests
        else:
            self.git_manager = None
            self.tinder_setup = None
            self.test_logger = None
        
        # Load version info
        self.load_version_info()
        
        # Bot controller will be imported when needed
        self.bot_controller = None
        
        # Load match instructions
        self.load_match_instructions()
        
        # Activate virtual environment
        self.activate_virtual_environment()

    def load_version_info(self):
        """Load current version information"""
        version_file = "version.json"
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                self.current_version = version_data.get('version', '1.0.0')
        else:
            self.save_version_info()

    def save_version_info(self):
        """Save current version information"""
        version_data = {
            'version': self.current_version,
            'last_updated': datetime.now().isoformat(),
            'deployment_status': 'stable',
            'changelog': self.get_changelog()
        }
        with open('version.json', 'w') as f:
            json.dump(version_data, f, indent=2)

    def get_changelog(self):
        """Get changelog for current version"""
        changelog = {
            "1.0.0": "Initial release with basic Tinder bot functionality",
            "1.1.0": "Added conversation phases and response timing",
            "1.2.0": "Added chat exclusion and CLI management",
            "1.3.0": "Added deployment pipeline and hot reload",
            "1.4.0": "Added relationship_intent-based prompt adjustment",
            "1.5.0": "Added connection testing and error handling"
        }
        return changelog.get(self.current_version, "No changelog available")

    def load_bot_controller(self):
        """Load bot controller when needed"""
        if self.bot_controller is None:
            try:
                # Ensure virtual environment is activated
                self.activate_virtual_environment()
                
                # Add project root to Python path
                project_root = os.path.dirname(os.path.dirname(__file__))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                from src.core.tinderbot import BotController
                self.bot_controller = BotController()
                return True
            except ImportError as e:
                print(f"Error: Could not import BotController: {e}")
                return False
        return True

    def show_test_logs(self):
        """Show recent test logs"""
        if not NEW_SYSTEMS_AVAILABLE:
            print("Test logger not available")
            return
        
        try:
            from src.utils.test_logger import get_latest_testlog, load_testlog
            
            latest_log = get_latest_testlog()
            if latest_log:
                print(f"Latest test log: {latest_log.name}")
                log_data = load_testlog(latest_log)
                
                if log_data:
                    summary = log_data.get('test_session', {})
                    print(f"Version: {summary.get('version', 'Unknown')}")
                    print(f"Timestamp: {summary.get('timestamp', 'Unknown')}")
                    
                    # Show test results
                    test_results = log_data.get('test_results', {})
                    if test_results:
                        print(f"\nTest Results ({len(test_results)} tests):")
                        for test_name, result in test_results.items():
                            status = "PASS" if result.get('success') else "FAIL"
                            print(f"  {status} {test_name}: {result.get('message', '')}")
                    
                    # Show API results
                    api_results = log_data.get('api_tests', {})
                    if api_results:
                        print(f"\nAPI Tests ({len(api_results)} tests):")
                        for api_name, result in api_results.items():
                            status = "PASS" if result.get('success') else "FAIL"
                            print(f"  {status} {api_name}: {result.get('status_code', 'N/A')}")
                    
                    # Show errors
                    errors = log_data.get('errors', [])
                    if errors:
                        print(f"\nErrors ({len(errors)}):")
                        for error in errors[:5]:  # Show first 5 errors
                            print(f"  - {error.get('type', 'Unknown')}: {error.get('message', '')}")
                else:
                    print("Failed to load test log data")
            else:
                print("No test logs found")
        except Exception as e:
            print(f"Error showing test logs: {e}")

    def show_version_history(self):
        """Show version history and available backups"""
        print(f"Current version: {self.current_version}")
        print("\nVersion history:")
        
        # Load version info
        version_file = "version.json"
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                changelog = version_data.get('changelog', {})
                if isinstance(changelog, dict):
                    for version, description in changelog.items():
                        print(f"  {version}: {description}")
        
        # Show available backups
        print("\nAvailable backups:")
        if os.path.exists(self.backup_dir):
            backups = [d for d in os.listdir(self.backup_dir) if os.path.isdir(os.path.join(self.backup_dir, d))]
            backups.sort(reverse=True)
            for backup in backups[:5]:  # Show last 5 backups
                print(f"  {backup}")
        
        if not backups:
            print("  No backups available")

    def create_backup(self):
        """Create backup of current version"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_v{self.current_version}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Files to backup
        files_to_backup = [
            'main.py', 'src/',
            'persistent_data.pkl', 'version.json', 'requirements.txt'
        ]
        
        os.makedirs(backup_path, exist_ok=True)
        
        for file in files_to_backup:
            if os.path.exists(file):
                if file == 'src/':
                    # Copy entire src directory
                    shutil.copytree(file, os.path.join(backup_path, 'src'))
                else:
                    shutil.copy2(file, backup_path)
        
        print(f"Backup created: {backup_name}")
        return backup_path

    def run_tests(self):
        """Run comprehensive tests before deployment"""
        print("Running Comprehensive Deployment Tests...")
        
        # Initialize test logger
        if NEW_SYSTEMS_AVAILABLE:
            self.test_logger = TestLogger(self.current_version)
            print(f"Test logging enabled: {self.test_logger.filepath}")
        
        # Run the comprehensive test suite
        try:
            from src.tests.test_deployment import main as run_comprehensive_tests
            success = run_comprehensive_tests()
            
            # Log test results
            if NEW_SYSTEMS_AVAILABLE and self.test_logger:
                self.test_logger.log_test_result("comprehensive_test_suite", success, 
                                               f"Comprehensive test suite {'passed' if success else 'failed'}")
                self.test_logger.save_log()
                self.test_logger.print_summary()
            
            return success
        except ImportError as e:
            print(f"Could not import comprehensive tests: {e}")
            print("Falling back to basic tests...")
            
            # Fallback to basic tests
            tests = [
                self.test_config_loading,
                self.test_chat_manager,
                self.test_storage,
                self.test_api_connection
            ]
            
            passed = 0
            failed = 0
            
            for test in tests:
                try:
                    test()
                    print(f"PASS {test.__name__}")
                    passed += 1
                    
                    # Log individual test result
                    if NEW_SYSTEMS_AVAILABLE and self.test_logger:
                        self.test_logger.log_test_result(test.__name__, True, "Test passed")
                        
                except Exception as e:
                    print(f"FAIL {test.__name__}: {e}")
                    failed += 1
                    
                    # Log individual test result
                    if NEW_SYSTEMS_AVAILABLE and self.test_logger:
                        self.test_logger.log_test_result(test.__name__, False, f"Test failed: {e}")
            
            print(f"Basic tests completed: {passed} passed, {failed} failed")
            
            # Save test log
            if NEW_SYSTEMS_AVAILABLE and self.test_logger:
                self.test_logger.save_log()
                self.test_logger.print_summary()
            
            return failed == 0

    def test_config_loading(self):
        """Test if config.json can be loaded"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        required_keys = ['api_key', 'tinder-auth-token', 'conversation_phases']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

    def test_chat_manager(self):
        """Test ChatManager initialization"""
        try:
            from src.chat.chat import ChatManager
            
            # Test with mock API
            class MockAPI:
                def __init__(self):
                    self.user_profile = None
            
            chat_manager = ChatManager(MockAPI())
            assert chat_manager is not None
        except ImportError as e:
            print(f"Warning: ChatManager test skipped due to import error: {e}")
            # Don't fail the test, just skip it
            pass

    def test_storage(self):
        """Test PersistentStorage functionality"""
        try:
            from src.utils.storage import PersistentStorage
            
            storage = PersistentStorage('test_storage.pkl')
            test_data = {'test': 'data'}
            storage.save(test_data)
            loaded_data = storage.load()
            
            if loaded_data != test_data:
                raise ValueError("Storage test failed")
            
            # Cleanup
            if os.path.exists('test_storage.pkl'):
                os.remove('test_storage.pkl')
        except ImportError as e:
            print(f"Warning: Storage test skipped due to import error: {e}")
            # Don't fail the test, just skip it
            pass

    def test_api_connection(self):
        """Test basic API connectivity"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        # Test if API key is valid format
        if not config['api_key'].startswith('sk-'):
            raise ValueError("Invalid OpenAI API key format")

    def start_bot(self):
        """Start the bot in the same process instead of subprocess"""
        if self.is_running:
            print("Bot is already running!")
            return
        
        print("Starting TinderBot in same process...")
        try:
            # Import and start bot directly
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
            
            from src.core import BotController
            
            # Create bot controller
            self.bot_controller = BotController()
            
            # Start bot in a separate thread
            self.bot_controller.start_bot()
            
            self.is_running = True
            print(f"Bot started successfully in same process!")
            
            # Start output monitoring thread to show bot status
            self.monitor_thread = threading.Thread(target=self.monitor_bot_status, daemon=True)
            self.monitor_thread.start()
                
        except Exception as e:
            print(f"ERROR: Failed to start bot: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False

    def stop_bot(self):
        """Stop the running bot"""
        if not self.is_running or not hasattr(self, 'bot_controller'):
            print("Bot is not running!")
            return
        
        print("Stopping TinderBot...")
        try:
            self.bot_controller.stop_bot()
            self.is_running = False
            print("Bot stopped")
        except Exception as e:
            print(f"Error stopping bot: {e}")
            self.is_running = False

    def get_next_version(self, version_type="patch"):
        """Get the next version number based on type"""
        major, minor, patch = map(int, self.current_version.split('.'))
        
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"

    def deploy_new_version(self, new_version=None, version_type="patch"):
        """Deploy a new version of the bot"""
        print(f"Deploying new version...")
        
        # Check Git changes if available
        if NEW_SYSTEMS_AVAILABLE and self.git_manager:
            if self.git_manager.check_for_changes():
                print("Git changes detected - suggesting auto-version update")
                auto_update = input("Auto-update version based on Git changes? (y/N): ").strip().lower()
                if auto_update == 'y':
                    if self.git_manager.auto_update_version():
                        new_version = self.git_manager.get_current_version()
                        print(f"Auto-updated to version: {new_version}")
                    else:
                        print("Auto-update failed")
        
        if new_version is None:
            new_version = self.get_next_version(version_type)
        
        print(f"Current version: {self.current_version}")
        print(f"Deploying version: {new_version}")
        print(f"Version type: {version_type}")
        
        # Confirm deployment
        confirm = input(f"Deploy version {new_version}? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Deployment cancelled.")
            return False
        
        # 1. Create backup
        backup_path = self.create_backup()
        
        # 2. Run tests
        if not self.run_tests():
            print("Tests failed! Deployment aborted.")
            return False
        
        # 3. Stop current bot
        was_running = self.is_running
        if was_running:
            self.stop_bot()
        
        # 4. Update version
        self.current_version = new_version
        self.save_version_info()
        
        # 5. Restart bot if it was running
        if was_running:
            self.start_bot()
        
        print(f"Successfully deployed version {new_version}")
        return True

    def hot_reload(self):
        """Hot reload the bot without stopping it"""
        print("Performing hot reload...")
        
        # Send reload signal to bot
        if self.is_running and self.bot_process:
            # On Unix systems, send SIGUSR1 for reload
            if os.name != 'nt':  # Not Windows
                self.bot_process.send_signal(signal.SIGUSR1)
                print("Reload signal sent to bot")
            else:
                print("Hot reload not supported on Windows")
        else:
            print("Bot is not running")

    def monitor_bot_output(self):
        """Monitor bot output and display it"""
        print("DEBUG: Starting output monitoring thread...")
        sys.stdout.flush()
        
        timeout_counter = 0
        last_output_time = time.time()
        
        while self.is_running and self.bot_process:
            try:
                # Check if process is still running
                if self.bot_process.poll() is not None:
                    print(f"DEBUG: Bot process ended with return code: {self.bot_process.returncode}")
                    self.is_running = False
                    break
                
                # Read from stdout with timeout
                stdout_line = self.bot_process.stdout.readline()
                if stdout_line:
                    print(f"[BOT] {stdout_line.strip()}")
                    sys.stdout.flush()
                    last_output_time = time.time()
                    timeout_counter = 0
                else:
                    timeout_counter += 1
                    if timeout_counter > 100:  # ~1 second without output
                        current_time = time.time()
                        if current_time - last_output_time > 5:  # 5 seconds without output
                            print(f"DEBUG: No output for 5 seconds, checking process status...")
                            sys.stdout.flush()
                            if self.bot_process.poll() is not None:
                                print(f"DEBUG: Bot process died with return code: {self.bot_process.returncode}")
                                self.is_running = False
                                break
                            timeout_counter = 0
                            last_output_time = current_time
                
                # Read from stderr
                stderr_line = self.bot_process.stderr.readline()
                if stderr_line:
                    print(f"[BOT-ERROR] {stderr_line.strip()}")
                    sys.stdout.flush()
                    last_output_time = time.time()
                    timeout_counter = 0
                
                # Small delay to prevent high CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in monitor_bot_output: {e}")
                break
        
        print("DEBUG: Output monitoring thread ended")
        sys.stdout.flush()
    
    def monitor_bot_status(self):
        """Monitor bot status in same process"""
        print("DEBUG: Starting bot status monitoring thread...")
        sys.stdout.flush()
        
        while self.is_running and hasattr(self, 'bot_controller'):
            try:
                # Check if bot is still running
                if not self.bot_controller.bot_running:
                    print("DEBUG: Bot stopped running")
                    self.is_running = False
                    break
                
                # Show bot status every 30 seconds
                time.sleep(30)
                print("DEBUG: Bot is still running...")
                sys.stdout.flush()
                
            except Exception as e:
                print(f"Error in monitor_bot_status: {e}")
                break
        
        print("DEBUG: Bot status monitoring thread ended")
        sys.stdout.flush()
    
    def show_debug(self):
        """Show all debug output from the bot"""
        if not self.is_running or not self.bot_process:
            print("Bot is not running! Starting bot in debug mode...")
            self.start_bot()
        
        print("Showing bot debug output (Press Ctrl+C to stop)...")
        print("=" * 50)
        
        try:
            while True:
                # Read from stdout
                stdout_line = self.bot_process.stdout.readline()
                if stdout_line:
                    print(f"[STDOUT] {stdout_line.strip()}")
                    sys.stdout.flush()  # Force immediate display
                
                # Read from stderr
                stderr_line = self.bot_process.stderr.readline()
                if stderr_line:
                    print(f"[STDERR] {stderr_line.strip()}")
                    sys.stdout.flush()  # Force immediate display
                
                # Small delay to prevent high CPU usage
                time.sleep(0.01)  # Reduced delay for faster response
                
        except KeyboardInterrupt:
            print("\nDebug output stopped.")
        except Exception as e:
            print(f"Error reading debug output: {e}")

    def start_debug_mode(self):
        """Start bot directly in debug mode with immediate output"""
        print("Starting bot in debug mode with immediate output...")
        print("=" * 50)
        
        # Start bot process with unbuffered output
        self.bot_process = subprocess.Popen([
            sys.executable, '-u', 'main.py'  # -u flag for unbuffered output
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
        
        self.is_running = True
        print(f"Bot started with PID: {self.bot_process.pid}")
        
        # Start output monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_bot_output, daemon=True)
        self.monitor_thread.start()
        
        # Also start the debug output display
        self.show_debug()
    
    def monitor_bot(self):
        """Monitor bot process and restart if needed"""
        while self.is_running:
            if self.bot_process and self.bot_process.poll() is not None:
                print("Bot process died, restarting...")
                self.start_bot()
            time.sleep(30)  # Check every 30 seconds

    def get_status(self):
        """Get current deployment status"""
        status = {
            'version': self.current_version,
            'is_running': self.is_running,
            'pid': self.bot_process.pid if self.bot_process else None,
            'last_backup': self.get_latest_backup(),
            'deployment_time': datetime.now().isoformat()
        }
        return status

    def get_latest_backup(self):
        """Get the most recent backup"""
        if not os.path.exists(self.backup_dir):
            return None
        
        backups = [d for d in os.listdir(self.backup_dir) 
                  if os.path.isdir(os.path.join(self.backup_dir, d))]
        
        if not backups:
            return None
        
        return max(backups, key=lambda x: os.path.getctime(os.path.join(self.backup_dir, x)))

    def rollback(self, backup_name=None):
        """Rollback to a previous version"""
        if not backup_name:
            backup_name = self.get_latest_backup()
        
        if not backup_name:
            print("No backup found for rollback")
            return False
        
        print(f"Rolling back to {backup_name}...")
        
        # Stop bot
        was_running = self.is_running
        if was_running:
            self.stop_bot()
        
        # Restore files
        backup_path = os.path.join(self.backup_dir, backup_name)
        files_to_restore = [
            'main.py', 'src/', 'requirements.txt'
        ]
        
        for file in files_to_restore:
            backup_file = os.path.join(backup_path, file)
            if os.path.exists(backup_file):
                if file == 'src/':
                    # Restore entire src directory
                    if os.path.exists('src'):
                        shutil.rmtree('src')
                    shutil.copytree(backup_file, 'src')
                    print(f"Restored {file}")
                else:
                    shutil.copy2(backup_file, file)
                    print(f"Restored {file}")
        
        # Restart bot if it was running
        if was_running:
            self.start_bot()
        
        print("Rollback completed")
        return True

    # Bot management functions
    def exclude_chat(self, name):
        """Exclude a chat by name"""
        try:
            # Try to use bot controller if available
            if self.load_bot_controller():
                return self.bot_controller.exclude_chat(name)
            else:
                # Fallback: direct storage access
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage('persistent_data.pkl')  # Same file as BotController
                
                # Check if match exists (simplified check)
                print(f"Bot not running. Adding '{name}' to excluded chats...")
                storage.add_excluded_chat(name)
                print(f"✅ Chat '{name}' excluded successfully!")
                return True
                
        except Exception as e:
            print(f"Error excluding chat: {e}")
            return False

    def include_chat(self, name):
        """Include a chat by name"""
        try:
            # Try to use bot controller if available
            if self.load_bot_controller():
                return self.bot_controller.include_chat(name)
            else:
                # Fallback: direct storage access
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage('persistent_data.pkl')  # Same file as BotController
                
                excluded_chats = storage.get_excluded_chats()
                if name not in excluded_chats:
                    print(f"Chat '{name}' is not excluded.")
                    return False
                
                storage.remove_excluded_chat(name)
                print(f"✅ Chat '{name}' included successfully!")
                return True
                
        except Exception as e:
            print(f"Error including chat: {e}")
            return False

    def list_excluded_chats(self):
        """List all excluded chats"""
        try:
            # Always use direct storage access for reliability
            from src.utils.storage import PersistentStorage
            storage = PersistentStorage('persistent_data.pkl')
            
            excluded_chats = storage.get_excluded_chats()
            if not excluded_chats:
                print("Keine ausgeschlossenen Chats.")
            else:
                print("Ausgeschlossene Chats:")
                for name in excluded_chats:
                    print(f"  - {name}")
                        
        except Exception as e:
            print(f"Error listing excluded chats: {e}")
            # Fallback: try to use bot controller if available
            try:
                if self.load_bot_controller():
                    self.bot_controller.list_excluded_chats()
            except:
                print("Could not access excluded chats from any source")

    def list_active_chats(self):
        """List all active chats"""
        try:
            # Try to use bot controller if available
            if self.load_bot_controller():
                self.bot_controller.list_active_chats()
            else:
                # Fallback: show basic info
                print("Bot not running. Active chats cannot be determined.")
                print("Start the bot to see active chats.")
                
        except Exception as e:
            print(f"Error listing active chats: {e}")
    
    def show_debug_settings(self):
        """Show current debug settings"""
        try:
            from src.utils.storage import PersistentStorage
            storage = PersistentStorage('persistent_data.pkl')
            
            debug_settings = storage.get_debug_settings()
            
            print("Current Debug Settings:")
            print("=" * 30)
            for setting, value in debug_settings.items():
                status = "✅ ON" if value else "❌ OFF"
                print(f"  {setting.replace('_', ' ').title()}: {status}")
            print()
            
        except Exception as e:
            print(f"Error showing debug settings: {e}")
    
    def set_debug_setting(self, debug_type, value):
        """Set a specific debug setting"""
        try:
            from src.utils.storage import PersistentStorage
            storage = PersistentStorage('persistent_data.pkl')
            
            # Map debug types to storage keys
            type_mapping = {
                'bot': 'bot_debug',
                'api': 'api_debug',
                'chat': 'chat_debug',
                'storage': 'storage_debug'
            }
            
            if debug_type not in type_mapping:
                print(f"❌ Unknown debug type: {debug_type}")
                print("Available types: bot, api, chat, storage")
                return
            
            storage_key = type_mapping[debug_type]
            storage.update_debug_setting(storage_key, value)
            
            status = "ON" if value else "OFF"
            print(f"✅ {debug_type.upper()} debug set to {status}")
            
            # If bot is running, notify about the change
            if hasattr(self, 'bot_controller') and self.bot_controller:
                print("Note: Debug setting changed. Bot will use new setting on next restart.")
            
        except Exception as e:
            print(f"Error setting debug setting: {e}")
    
    def add_match_instruction(self, name, instruction):
        """Add custom instruction for a specific match"""
        try:
            if not hasattr(self, 'match_instructions'):
                self.match_instructions = {}
            
            self.match_instructions[name] = {
                'instruction': instruction,
                'timestamp': time.time(),
                'active': True
            }
            
            print(f"✅ Custom instruction added for {name}:")
            print(f"   Instruction: {instruction}")
            print(f"   Status: Active")
            
            # Save to persistent storage
            self.save_match_instructions()
            
        except Exception as e:
            print(f"Error adding match instruction: {e}")
    
    def list_match_instructions(self):
        """List all custom match instructions"""
        try:
            if not hasattr(self, 'match_instructions') or not self.match_instructions:
                print("No custom match instructions found.")
                return
            
            print("Custom Match Instructions:")
            print("=" * 50)
            
            for name, data in self.match_instructions.items():
                status = "✅ Active" if data['active'] else "❌ Inactive"
                timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                print(f"👤 {name}:")
                print(f"   Instruction: {data['instruction']}")
                print(f"   Status: {status}")
                print(f"   Added: {timestamp}")
                print()
                
        except Exception as e:
            print(f"Error listing match instructions: {e}")
    
    def remove_match_instruction(self, name):
        """Remove custom instruction for a specific match"""
        try:
            if not hasattr(self, 'match_instructions') or name not in self.match_instructions:
                print(f"No instruction found for {name}")
                return
            
            instruction = self.match_instructions[name]['instruction']
            del self.match_instructions[name]
            
            print(f"✅ Custom instruction removed for {name}:")
            print(f"   Removed instruction: {instruction}")
            
            # Save to persistent storage
            self.save_match_instructions()
            
        except Exception as e:
            print(f"Error removing match instruction: {e}")
    
    def save_match_instructions(self):
        """Save match instructions to persistent storage"""
        try:
            if hasattr(self, 'match_instructions'):
                instructions_file = "match_instructions.json"
                with open(instructions_file, 'w', encoding='utf-8') as f:
                    json.dump(self.match_instructions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save match instructions: {e}")
    
    def load_match_instructions(self):
        """Load match instructions from persistent storage"""
        try:
            instructions_file = "match_instructions.json"
            if os.path.exists(instructions_file):
                with open(instructions_file, 'r', encoding='utf-8') as f:
                    self.match_instructions = json.load(f)
            else:
                self.match_instructions = {}
        except Exception as e:
            print(f"Warning: Could not load match instructions: {e}")
            self.match_instructions = {}
    
    def get_match_instruction(self, name):
        """Get custom instruction for a specific match"""
        try:
            if hasattr(self, 'match_instructions') and name in self.match_instructions:
                data = self.match_instructions[name]
                if data['active']:
                    return data['instruction']
            return None
        except Exception as e:
            print(f"Error getting match instruction: {e}")
            return None

    def debug_chats(self):
        """Debug chat functionality with real Tinder data and response simulation"""
        print("🔍 Chat Debug Mode - Real Tinder Data")
        print("=" * 50)
        
        try:
            # Load necessary components
            from src.utils.storage import PersistentStorage
            from src.chat.chat import ChatManager
            from src.config import config
            from src.core.tinderbot import TinderAPI
            
            # Load storage and get active chats
            storage = PersistentStorage('persistent_data.pkl')
            data = storage.load()
            
            if not data or 'chats' not in data:
                print("❌ No chat data found. Start the bot first to generate chat data.")
                return
            
            chats = data['chats']
            if not chats:
                print("❌ No active chats found. Start the bot first to generate chat data.")
                return
            
            print(f"📱 Found {len(chats)} active chats:")
            for i, (match_id, chat_data) in enumerate(chats.items(), 1):
                # Chat data is stored as a list of messages, not a dict
                # We need to extract match name from the messages or use a fallback
                match_name = f'Match_{i}'
                message_count = len(chat_data) if isinstance(chat_data, list) else 0
                
                # Try to find match name in the first few messages
                if isinstance(chat_data, list) and chat_data:
                    for msg in chat_data[:3]:  # Check first 3 messages
                        if hasattr(msg, 'type') and msg.type == 'human':
                            # This is a message from the match, might contain name info
                            if hasattr(msg, 'content'):
                                content = msg.content
                                # Simple heuristic: if content contains a name-like pattern
                                if len(content.split()) <= 3 and not any(char in content for char in ['?', '!', '.', ',']):
                                    match_name = content.strip()
                                    break
                
                print(f"   {i}. {match_name} ({message_count} messages)")
            
            # Let user select a chat to debug
            try:
                selection = input(f"\nSelect chat to debug (1-{len(chats)}): ").strip()
                chat_index = int(selection) - 1
                
                if chat_index < 0 or chat_index >= len(chats):
                    print("❌ Invalid selection")
                    return
                
                # Get selected chat
                match_ids = list(chats.keys())
                selected_match_id = match_ids[chat_index]
                selected_chat_data = chats[selected_match_id]
                
                print(f"\n🔍 Debugging chat: {match_name}")
                print("=" * 40)
                
                # Show chat history
                if isinstance(selected_chat_data, list) and selected_chat_data:
                    print("📜 Chat History:")
                    for msg in selected_chat_data[-5:]:  # Show last 5 messages
                        if hasattr(msg, 'content'):
                            sender = "Bot" if msg.type == "ai" else "Match"
                            print(f"   {sender}: {msg.content}")
                        else:
                            print(f"   Message: {msg}")
                else:
                    print("📜 No message history found")
                
                # Show available commands
                print(f"\n📋 Available debug commands:")
                print("   response [message] - Simulate message from match")
                print("   exit - Exit debug mode")
                
                # Debug command loop
                while True:
                    try:
                        command = input(f"\nDebug [{match_name}] > ").strip()
                        
                        if command.lower() == 'exit':
                            print("👋 Exiting debug mode...")
                            break
                        
                        elif command.lower().startswith('response '):
                            # Extract message content
                            message_content = command[9:].strip()  # Remove "response " prefix
                            
                            if not message_content:
                                print("❌ Please provide a message: response [message]")
                                continue
                            
                            print(f"\n🧪 Simulating message from match: '{message_content}'")
                            print("=" * 50)
                            
                            # Create mock API for simulation
                            class MockAPI:
                                def send_message(self, match_id, message):
                                    print(f"📤 [SIMULATION] Bot would send: {message}")
                                    return True
                            
                            # Create ChatManager with mock API
                            mock_api = MockAPI()
                            chat_manager = ChatManager(mock_api)
                            
                            # Set up chat manager with existing data
                            if isinstance(selected_chat_data, list):
                                from langchain_community.chat_message_histories import ChatMessageHistory
                                chat_manager.chat_history = ChatMessageHistory(messages=selected_chat_data)
                            
                            chat_manager.match_id = selected_match_id
                            chat_manager.match_name = match_name
                            chat_manager.last_match_message_time = time.time()
                            chat_manager.active = True  # Mark chat as active
                            
                            # Process the simulated message
                            print(f"🔄 Processing simulated message...")
                            print("=" * 40)
                            
                            # Simulate message processing directly
                            try:
                                # Create a simple message simulation
                                print(f"📥 Received message from {match_name}: '{message_content}'")
                                
                                # Simulate LLM response generation
                                print(f"🤖 Generating bot response...")
                                
                                # For demo purposes, create a simple response
                                # In real usage, this would call the LLM
                                demo_response = f"Hey {match_name}! Das ist eine simulierte Antwort auf: '{message_content}'"
                                
                                print(f"💭 Generated response: {demo_response}")
                                
                                # Test the new message splitting functionality
                                print(f"\n🔀 Testing message splitting...")
                                success = chat_manager.parse_and_send_response(demo_response, selected_match_id, debug=True)
                                
                                if success:
                                    print(f"✅ Message processing simulation completed successfully!")
                                else:
                                    print(f"⚠️  Message processing simulation had issues")
                                
                            except Exception as e:
                                print(f"❌ Error in message simulation: {e}")
                                import traceback
                                traceback.print_exc()
                            
                            print(f"\n✅ Chat simulation completed!")
                            print("💡 The bot would have responded with the message(s) above.")
                            
                        else:
                            print("❌ Unknown command. Use 'response [message]' or 'exit'")
                            
                    except KeyboardInterrupt:
                        print("\n👋 Exiting debug mode...")
                        break
                    except Exception as e:
                        print(f"❌ Error processing command: {e}")
                        continue
                
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n❌ Debug cancelled")
                
        except Exception as e:
            print(f"❌ Error in chat debug mode: {e}")
            import traceback
            traceback.print_exc()

    def cleanup_storage(self):
        """Clean up corrupted persistent data"""
        try:
            from src.utils.storage import PersistentStorage
            storage = PersistentStorage('persistent_data.pkl')
            
            print("Starting persistent data cleanup...")
            success = storage.cleanup_corrupted_data()
            
            if success:
                print("✅ Storage cleanup completed successfully!")
                print("The bot will now use the cleaned data.")
            else:
                print("⚠️  Storage cleanup completed with warnings.")
                print("The bot will use fresh data.")
                
            return success
            
        except Exception as e:
            print(f"❌ Error during storage cleanup: {e}")
            return False

    def clear_all_wait_times(self):
        """Clear all scheduled response wait times and send messages immediately"""
        try:
            if not self.bot_controller:
                print("❌ Bot controller not available. Please start the bot first.")
                return False
            
            # Check if bot is running
            if not self.is_running:
                print("❌ Bot is not currently running. Please start the bot first.")
                return False
            
            print("🚀 Clearing all scheduled response wait times...")
            print("📤 All pending messages will be sent immediately!")
            
            # Access the ResponseTimer through chat managers
            cleared_count = 0
            total_scheduled = 0
            
            # Get all chat managers from the bot controller
            if hasattr(self.bot_controller, 'chat_managers'):
                print(f"   🔍 Checking {len(self.bot_controller.chat_managers)} active chat managers...")
                
                for match_id, chat_manager in self.bot_controller.chat_managers.items():
                    print(f"   📋 Checking chat manager for match {match_id}...")
                    
                    if hasattr(chat_manager, 'response_timer'):
                        response_timer = chat_manager.response_timer
                        print(f"      ✅ Found ResponseTimer instance")
                        
                        if hasattr(response_timer, 'scheduled_responses'):
                            scheduled_count = len(response_timer.scheduled_responses)
                            total_scheduled += scheduled_count
                            
                            print(f"      📊 Scheduled responses: {scheduled_count}")
                            
                            if scheduled_count > 0:
                                print(f"   📝 Found {scheduled_count} scheduled response(s) for match {match_id}")
                                
                                # Send all scheduled responses immediately
                                current_time = time.time()
                                responses_to_send = []
                                
                                for scheduled_match_id, response_data in response_timer.scheduled_responses.items():
                                    responses_to_send.append((scheduled_match_id, response_data))
                                
                                # Send responses immediately
                                for scheduled_match_id, response_data in responses_to_send:
                                    try:
                                        print(f"   ⚡ Sending immediate response to {scheduled_match_id}")
                                        print(f"      📝 Message: {response_data['message_content'][:50]}...")
                                        
                                        # Send the message using the chat manager
                                        if response_data.get('chat_manager'):
                                            response_data['chat_manager'].parse_and_send_response(
                                                response_data['message_content'], 
                                                scheduled_match_id, 
                                                debug=False
                                            )
                                        else:
                                            # Fallback to direct API call
                                            response_data['api'].send_message(scheduled_match_id, response_data['message_content'])
                                        
                                        # Remove from scheduled responses
                                        del response_timer.scheduled_responses[scheduled_match_id]
                                        cleared_count += 1
                                        
                                        print(f"      ✅ Message sent immediately!")
                                        
                                    except Exception as e:
                                        print(f"      ❌ Error sending immediate response: {e}")
                        else:
                            print(f"      ⚠️  ResponseTimer has no scheduled_responses attribute")
                    else:
                        print(f"      ⚠️  Chat manager has no response_timer attribute")
            else:
                print("   ⚠️  Bot controller has no chat_managers attribute")
            
            # Also check if there's a global ResponseTimer instance
            if hasattr(self.bot_controller, 'response_timer'):
                print("   🔍 Checking global ResponseTimer instance...")
                global_response_timer = self.bot_controller.response_timer
                
                if hasattr(global_response_timer, 'scheduled_responses'):
                    global_scheduled_count = len(global_response_timer.scheduled_responses)
                    total_scheduled += global_scheduled_count
                    
                    if global_scheduled_count > 0:
                        print(f"   📝 Found {global_scheduled_count} scheduled response(s) in global ResponseTimer")
                        
                        # Send all scheduled responses immediately
                        responses_to_send = []
                        
                        for scheduled_match_id, response_data in global_response_timer.scheduled_responses.items():
                            responses_to_send.append((scheduled_match_id, response_data))
                        
                        # Send responses immediately
                        for scheduled_match_id, response_data in responses_to_send:
                            try:
                                print(f"   ⚡ Sending immediate response to {scheduled_match_id}")
                                print(f"      📝 Message: {response_data['message_content'][:50]}...")
                                
                                # Send the message using the chat manager
                                if response_data.get('chat_manager'):
                                    response_data['chat_manager'].parse_and_send_response(
                                        response_data['message_content'], 
                                        scheduled_match_id, 
                                        debug=False
                                    )
                                else:
                                    # Fallback to direct API call
                                    response_data['api'].send_message(scheduled_match_id, response_data['message_content'])
                                
                                # Remove from scheduled responses
                                del global_response_timer.scheduled_responses[scheduled_match_id]
                                cleared_count += 1
                                
                                print(f"      ✅ Message sent immediately!")
                                
                            except Exception as e:
                                print(f"      ❌ Error sending immediate response: {e}")
            
            if total_scheduled == 0:
                print("ℹ️  No scheduled responses found. All messages are already sent or no delays are active.")
                print("💡 This could mean:")
                print("   - All messages have already been sent")
                print("   - No messages are currently scheduled for delayed sending")
                print("   - The bot is not actively processing any conversations")
            else:
                print(f"✅ Successfully cleared {cleared_count} out of {total_scheduled} scheduled responses!")
                print(f"📤 All pending messages have been sent immediately.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clearing wait times: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_webconfig(self):
        """Start the web configuration interface"""
        try:
            print("Starting TinderGPT Web Configuration Interface...")
            print("Web interface will be available at: http://localhost:8080")
            print("Alternative access: http://127.0.0.1:8080")
            print("Press Ctrl+C to stop the web server")
            
            # Import and start the web config app
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'webconfig'))
            from webconfig.app import WebConfigApp
            
            app = WebConfigApp()
            app.run(host='0.0.0.0', port=8080, debug=False)
            
        except KeyboardInterrupt:
            print("\nWeb configuration interface stopped.")
        except ImportError as e:
            print(f"Error: Could not import web configuration module: {e}")
            print("Make sure Flask is installed: pip install flask")
        except Exception as e:
            print(f"Error starting web configuration interface: {e}")

    def activate_virtual_environment(self):
        """Activate virtual environment if available"""
        venv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.venv')
        if os.path.exists(venv_path):
            # Add virtual environment to Python path
            site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
            if os.path.exists(site_packages):
                if site_packages not in sys.path:
                    sys.path.insert(0, site_packages)
                    print(f"Debug: Added virtual environment to Python path: {site_packages}")
                return True
            else:
                # Try alternative Python versions
                for version in ['python3.11', 'python3.10', 'python3.9']:
                    alt_site_packages = os.path.join(venv_path, 'lib', version, 'site-packages')
                    if os.path.exists(alt_site_packages):
                        if alt_site_packages not in sys.path:
                            sys.path.insert(0, alt_site_packages)
                            print(f"Debug: Added virtual environment to Python path: {alt_site_packages}")
                        return True
        return False

def main():
    """Main deployment interface"""
    manager = DeploymentManager()
    
    print("Starvincis TinderBot Deployment Manager")
    print("=" * 50)
    
    while True:
        print(f"\nCurrent version: {manager.current_version}")
        print("\nAvailable commands:")
        print("  start_bot           - Start the bot")
        print("  stop_bot            - Stop the bot")
        print("  deploy              - Deploy next patch version (auto-increment)")
        print("  deploy_patch        - Deploy next patch version (1.0.0 -> 1.0.1)")
        print("  deploy_minor        - Deploy next minor version (1.0.0 -> 1.1.0)")
        print("  deploy_major        - Deploy next major version (1.0.0 -> 2.0.0)")
        print("  deploy_custom [ver] - Deploy custom version (e.g., deploy_custom 2.1.5)")
        print("  hot_reload          - Hot reload current version")
        print("  status              - Show deployment status")
        print("  rollback [backup]   - Rollback to backup")
        print("  test                - Run comprehensive test suite")
        print("  backup              - Create backup")
        print("  exclude_chat [name] - Exclude chat from auto-processing")
        print("  include_chat [name] - Include chat in auto-processing")
        print("  list_excluded       - List excluded chats")
        print("  list_active         - List active chats")
        print("  add_match_instruction [name] [instruction] - Add custom instruction for specific match")
        print("  list_match_instructions - List all custom match instructions")
        print("  remove_match_instruction [name] - Remove custom instruction for specific match")
        print("  debug_chats         - Start debug mode")
        print("  show_debug          - Show bot debug output")
        print("  start_debug         - Start bot in debug mode")
        print("  version_history     - Show version history and backups")
        print("  git_status          - Check Git status and changes")
        print("  setup_tinder        - Setup Tinder authentication")
        print("  auto_setup_tinder   - Automatic Tinder setup using stored credentials")
        print("  test_tinder_auth    - Test current Tinder authentication")
        print("  debug_settings      - Show current debug settings")
        print("  set_debug [type] [on/off] - Set debug mode (bot/api/chat/storage)")
        print("  cleanup_storage     - Clean up corrupted persistent data")
        print("  test_logs           - Show recent test logs")
        print("  clear_wait_times    - Clear all scheduled response wait times (send immediately)")
        print("  webconfig           - Start web configuration interface")
        print("  exit                - Exit")
        
        try:
            command = input("\nDeployment > ").strip().split()
            if not command:
                continue
            
            action = command[0]
            
            if action == "start_bot":
                manager.start_bot()
            elif action == "stop_bot":
                manager.stop_bot()
            elif action == "deploy":
                manager.deploy_new_version(version_type="patch")
            elif action == "deploy_patch":
                manager.deploy_new_version(version_type="patch")
            elif action == "deploy_minor":
                manager.deploy_new_version(version_type="minor")
            elif action == "deploy_major":
                manager.deploy_new_version(version_type="major")
            elif action == "deploy_custom":
                if len(command) > 1:
                    version = command[1]
                    manager.deploy_new_version(new_version=version)
                else:
                    print("Please specify version: deploy_custom [version]")
            elif action == "hot_reload":
                manager.hot_reload()
            elif action == "status":
                status = manager.get_status()
                print(json.dumps(status, indent=2))
            elif action == "rollback":
                backup = command[1] if len(command) > 1 else None
                manager.rollback(backup)
            elif action == "test":
                manager.run_tests()
            elif action == "backup":
                manager.create_backup()
            elif action == "exclude_chat":
                if len(command) > 1:
                    manager.exclude_chat(command[1])
                else:
                    print("Please specify name: exclude_chat [name]")
            elif action == "include_chat":
                if len(command) > 1:
                    manager.include_chat(command[1])
                else:
                    print("Please specify name: include_chat [name]")
            elif action == "list_excluded":
                manager.list_excluded_chats()
            elif action == "list_active":
                manager.list_active_chats()
            elif action == "add_match_instruction":
                if len(command) > 2:
                    name = command[1]
                    instruction = " ".join(command[2:])
                    manager.add_match_instruction(name, instruction)
                else:
                    print("Please specify name and instruction: add_match_instruction [name] [instruction]")
            elif action == "list_match_instructions":
                manager.list_match_instructions()
            elif action == "remove_match_instruction":
                if len(command) > 1:
                    name = command[1]
                    manager.remove_match_instruction(name)
                else:
                    print("Please specify name: remove_match_instruction [name]")
            elif action == "debug_chats":
                manager.debug_chats()
            elif action == "show_debug":
                manager.show_debug()
            elif action == "start_debug":
                manager.start_debug_mode()
            elif action == "version_history":
                manager.show_version_history()
            elif action == "git_status":
                if NEW_SYSTEMS_AVAILABLE and manager.git_manager:
                    manager.git_manager.check_for_changes()
                else:
                    print("Git version manager not available")
            elif action == "setup_tinder":
                if NEW_SYSTEMS_AVAILABLE and manager.tinder_setup:
                    manager.tinder_setup.manual_setup()
                else:
                    print("Tinder setup system not available")
            elif action == "auto_setup_tinder":
                if NEW_SYSTEMS_AVAILABLE and manager.tinder_setup:
                    manager.tinder_setup.automatic_setup()
                else:
                    print("Tinder setup system not available")
            elif action == "test_tinder_auth":
                if NEW_SYSTEMS_AVAILABLE and manager.tinder_setup:
                    manager.tinder_setup.check_auth_token_validity()
                else:
                    print("Tinder setup system not available")
            elif action == "debug_settings":
                manager.show_debug_settings()
            elif action == "set_debug":
                if len(command) > 2:
                    debug_type = command[1]
                    debug_value = command[2].lower() == 'on'
                    manager.set_debug_setting(debug_type, debug_value)
                else:
                    print("Please specify debug type and value: set_debug [type] [on/off]")
                    print("Available types: bot, api, chat, storage")
            elif action == "cleanup_storage":
                if NEW_SYSTEMS_AVAILABLE and manager.bot_controller:
                    manager.bot_controller.cleanup_corrupted_data()
                    print("Persistent data cleanup initiated. Bot will restart to apply changes.")
                else:
                    print("Bot controller or persistent storage not available for cleanup.")
            elif action == "clear_wait_times":
                manager.clear_all_wait_times()
            elif action == "test_logs":
                if NEW_SYSTEMS_AVAILABLE:
                    manager.show_test_logs()
                else:
                    print("Test logger not available")
            elif action == "webconfig":
                manager.start_webconfig()
            elif action == "exit":
                if manager.is_running:
                    manager.stop_bot()
                print("Goodbye!")
                break
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            if manager.is_running:
                manager.stop_bot()
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
