
"""
######################################################################
#                                                                    #
#  Starvnici Inc.                                                    #
#  Created on: 19.5.2024                                             #
#                                                                    #
#  This file is part of the Starvincis TinderBot project.            #
#                                                                    #
#  This software is the confidential and proprietary information     #
#  of Starvnici Inc. ("Confidential Information"). You shall not     #
#  disclose such Confidential Information and shall use it only in   #
#  accordance with the terms of the license agreement you entered    #
#  into with Starvnici Inc.                                          #
#                                                                    #
#  STARVNICI INC. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE   #
#  SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING #
#  BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY,     #
#  FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.            #
#  STARVNICI INC. SHALL NOT BE LIABLE FOR ANY DAMAGES SUFFERED BY    #
#  LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THIS     #
#  SOFTWARE OR ITS DERIVATIVES.                                      #
#                                                                    #
#  All rights reserved.                                              #
#                                                                    #
######################################################################
"""
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime
import builtins
import re

# Force immediate output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Sanitize CLI output: remove emojis and non-ASCII symbols from prints
_original_print = builtins.print

def _strip_emoji(text: str) -> str:
    try:
        return re.sub(r'[\u2600-\u27BF\u1F300-\u1FAFF]', '', text)
    except Exception:
        return text

def print(*args, **kwargs):  # noqa: A001 - intentional shadowing for sanitation
    try:
        clean_args = tuple(_strip_emoji(str(a)) for a in args)
    except Exception:
        clean_args = args
    return _original_print(*clean_args, **kwargs)

try:
    import requests
    from langchain_community.chat_message_histories import ChatMessageHistory
    from src.chat.chat import ChatManager
    from src.utils.storage import PersistentStorage
    from src.utils.tinder_setup import TinderSetup
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Please install required dependencies: pip install requests langchain")
    sys.exit(1)

TINDER_URL = "https://api.gotinder.com"

class TinderAPI():
    def __init__(self, token):
        self._token = token
        self.user_id = self.get_user_id()
        self.user_profile = self.get_profile(token)

    def get_user_id(self):
        headers = {
            "X-Auth-Token": self._token,
            "Content-type": "application/json"
        }
        response = requests.get(TINDER_URL + "/v2/profile?include=account%2Cuser", headers=headers)
        try:
            data = response.json()
        except ValueError:
            print("Error parsing JSON response for profile.")
            print("Response content:", response.content)
            return None
        return data["data"]["user"]["_id"]

    def test_connection(self):
        """Test if Tinder API is reachable"""
        try:
            headers = {
                "X-Auth-Token": self._token,
                "Content-type": "application/json"
            }
            response = requests.get(TINDER_URL + "/v2/profile?include=account%2Cuser", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, f"Authentication failed (401) - Token may be invalid"
            elif response.status_code == 403:
                return False, f"Access forbidden (403) - Account may be suspended"
            elif response.status_code == 429:
                return False, f"Rate limited (429) - Too many requests"
            else:
                return False, f"HTTP {response.status_code} - {response.text[:100]}"
                
        except requests.exceptions.Timeout:
            return False, "Connection timeout - Tinder API not responding"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - Network or Tinder API down"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_profile(self, token):
        headers = {
            "X-Auth-Token": token,
            "Content-type": "application/json"
        }
        response = requests.get("https://api.gotinder.com/v2/profile?include=account%2Cuser", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Unable to fetch profile data. Status code: {response.status_code}")
            return None

    def matches(self, limit=100):
        headers = {
            "X-Auth-Token": self._token,
            "Content-type": "application/json"
        }
        try:
            response = requests.get(TINDER_URL + f"/v2/matches?count={limit}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'ok': True,
                    'status': 200,
                    'error': None,
                    'matches': data.get("data", {}).get("matches", [])
                }
            elif response.status_code == 401:
                print("ERROR: Authentication failed while fetching matches (401) - invalid token")
                return {'ok': False, 'status': 401, 'error': 'auth', 'matches': []}
            elif response.status_code == 403:
                print("ERROR: Access forbidden while fetching matches (403)")
                return {'ok': False, 'status': 403, 'error': 'forbidden', 'matches': []}
            elif response.status_code == 429:
                print("ERROR: Rate limited while fetching matches (429)")
                return {'ok': False, 'status': 429, 'error': 'rate_limited', 'matches': []}
            else:
                print(f"ERROR: Failed to fetch matches - HTTP {response.status_code}")
                return {'ok': False, 'status': response.status_code, 'error': 'http_error', 'matches': []}
                
        except requests.exceptions.Timeout:
            print("ERROR: Timeout while fetching matches")
            return {'ok': False, 'status': 0, 'error': 'timeout', 'matches': []}
        except requests.exceptions.ConnectionError:
            print("ERROR: Connection error while fetching matches")
            return {'ok': False, 'status': 0, 'error': 'connection', 'matches': []}
        except ValueError:
            print("ERROR: Error parsing JSON response for matches.")
            return {'ok': False, 'status': 0, 'error': 'parse', 'matches': []}
        except Exception as e:
            print(f"ERROR: Unexpected error while fetching matches: {e}")
            return {'ok': False, 'status': 0, 'error': 'unexpected', 'matches': []}

    def get_user_info(self, user_id):
        headers = {
            "X-Auth-Token": self._token,
            "Content-type": "application/json"
        }
        try:
            response = requests.get(TINDER_URL + f"/user/{user_id}?locale=de", headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"ERROR: Failed to fetch user info for {user_id} - HTTP {response.status_code}")
                return None
                
            data = response.json()
        except requests.exceptions.Timeout:
            print(f"ERROR: Timeout while fetching user info for {user_id}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Connection error while fetching user info for {user_id}")
            return None
        except ValueError:
            print(f"ERROR: Error parsing JSON response for user {user_id}.")
            print("Response content:", response.content)
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error while fetching user info for {user_id}: {e}")
            return None

        try:
            user_info = data["results"]
            extracted_info = {
                "user_id": user_id,
                "name": user_info.get("name", ""),
                "birth_date": user_info.get("birth_date", ""),
                "bio": user_info.get("bio", ""),
                "distance_mi": user_info.get("distance_mi", 0),
                "interests": [interest["name"] for interest in user_info.get("user_interests", {}).get("selected_interests", [])],
                "relationship_intent": user_info.get("relationship_intent", {}).get("body_text", ""),
                "jobs": [job["title"]["name"] for job in user_info.get("jobs", []) if "title" in job and "name" in job["title"]],
                "schools": [school["name"] for school in user_info.get("schools", [])],
                "pets": next((desc["choice_selections"][0]["name"] for desc in user_info.get("selected_descriptors", []) if desc["id"] == "de_3" and "choice_selections" in desc and desc["choice_selections"]), "")
            }
            return extracted_info
        except Exception as e:
            print(f"ERROR: Error extracting user info for {user_id}: {e}")
            return None

    def send_message(self, match_id, message):
        headers = {
            "X-Auth-Token": self._token,
            "Content-type": "application/json",
            "User-agent": "Tinder/3.0.4 (iPhone; iOS 7.1; Scale/2.00)"
        }
        data = {'message': message}
        try:
            response = requests.post(f'{TINDER_URL}/user/matches/{match_id}', json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"Debug: Message sent successfully to {match_id}")
                return True
            elif response.status_code == 401:
                print(f"ERROR: Authentication failed while sending message to {match_id}")
                return False
            elif response.status_code == 403:
                print(f"ERROR: Access forbidden while sending message to {match_id}")
                return False
            elif response.status_code == 429:
                print(f"ERROR: Rate limited while sending message to {match_id}")
                return False
            else:
                print(f"ERROR: Failed to send message to {match_id} - HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"ERROR: Timeout while sending message to {match_id}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Connection error while sending message to {match_id}")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error while sending message to {match_id}: {e}")
            return False

class BotController:
    def __init__(self, config_file=None):
        if config_file:
            with open(config_file, 'r') as file:
                self.config = json.load(file)
        else:
            # Use config from env loader
            try:
                from src.config.env_loader import load_config_with_env
                self.config = load_config_with_env()
            except ImportError:
                print("Warning: Could not import env loader, using default config")
                self.config = {
                    'tinder-auth-token': 'default_token',
                    'api_key': 'default_key'
                }
        
        self.token = self.config['tinder-auth-token']
        self.api = TinderAPI(self.token)
        self.storage = PersistentStorage('persistent_data.pkl')
        self.bot_running = False
        self.bot_thread = None
        self.reload_requested = False
        self.first_startup = True  # Flag for first startup
        
        # Load existing data
        data = self.storage.load()
        
        # Ensure known_match_ids and known_message_ids are always sets
        if data and 'known_match_ids' in data:
            match_ids = data['known_match_ids']
            if isinstance(match_ids, list):
                self.known_match_ids = set(match_ids)
            else:
                self.known_match_ids = set(match_ids) if match_ids else set()
        else:
            self.known_match_ids = set()
            
        if data and 'known_message_ids' in data:
            message_ids = data['known_message_ids']
            if isinstance(message_ids, list):
                self.known_message_ids = set(message_ids)
            else:
                self.known_message_ids = set(message_ids) if message_ids else set()
        else:
            self.known_message_ids = set()
            
        self.chats = data.get('chats', {}) if data else {}
        
        # Load debug settings
        self.debug_settings = self.storage.get_debug_settings()
        
        # Load excluded chats
        self.excluded_chats = self.storage.get_excluded_chats()
        print(f"Debug: Loaded {len(self.excluded_chats)} excluded chats: {list(self.excluded_chats)}")
        
        # Initialize chat managers with anti-duplication protection
        self.chat_managers = {}
        for user_id, chat_history_data in self.chats.items():
            # ANTI-DUPLICATION: Check if chat manager already exists
            if user_id in self.chat_managers:
                print(f"ANTI-DUPLICATION: Chat manager already exists for {user_id[:8]}..., skipping")
                continue
                
            try:
                chat_manager = ChatManager(self.api)
                chat_manager.chat_history = ChatMessageHistory(messages=chat_history_data)
                chat_manager.active = True
                chat_manager.match_id = user_id
                self.chat_managers[user_id] = chat_manager
            except Exception as e:
                print(f"Error initializing chat manager for {user_id}: {e}")
                continue
        
        # Load chat timing data if available
        if data and 'chat_timing' in data:
            chat_timing = data['chat_timing']
            for user_id, timing_info in chat_timing.items():
                if user_id in self.chat_managers:
                    chat_manager = self.chat_managers[user_id]
                    if 'last_bot_message_time' in timing_info:
                        chat_manager.last_bot_message_time = timing_info['last_bot_message_time']
                        print(f"Debug: Loaded timing for {timing_info.get('match_name', user_id)}: last bot message at {time.strftime('%H:%M:%S', time.localtime(timing_info['last_bot_message_time']))}")
        
        # Setup signal handlers for hot reload
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup signal handlers for hot reload"""
        def reload_handler(signum, frame):
            print("Reload signal received, reloading configuration...")
            self.reload_requested = True
        
        # Register signal handler for SIGUSR1 (Unix only)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, reload_handler)

    def reload_configuration(self):
        """Reload configuration and restart components"""
        print("Reloading configuration...")
        
        # Reload config from config module
        try:
            from src.config import config
            self.config = config
        except ImportError:
            print("Warning: Could not reload config, using existing config")
        
        # Reinitialize chat managers with new config
        for user_id, chat_manager in self.chat_managers.items():
            if chat_manager.active:
                # Reinitialize with new config
                chat_manager.config = self.config
                chat_manager.phase_manager = chat_manager.phase_manager.__class__(self.config)
        
        print("Configuration reloaded successfully")
        self.reload_requested = False

    def get_match_name_by_id(self, match_id):
        """Get match name by match ID"""
        result = self.api.matches()
        matches = result.get('matches', result) if isinstance(result, dict) else (result or [])
        for match in matches:
            if match.get("_id") == match_id:
                return match.get("person", {}).get("name")
        return None

    def get_match_id_by_name(self, name):
        """Get match ID by name"""
        result = self.api.matches()
        matches = result.get('matches', result) if isinstance(result, dict) else (result or [])
        for match in matches:
            if match.get("person", {}).get("name") == name:
                return match.get("_id")
        return None

    def exclude_chat(self, name):
        """Exclude a chat by name"""
        match_id = self.get_match_id_by_name(name)
        if not match_id:
            print(f"Kein Match mit dem Namen '{name}' gefunden.")
            return False
        
        # Get confirmation
        confirm = input(f"Mochtest du den Chat mit '{name}' wirklich von der automatischen Verarbeitung ausschliessen? (j/n): ")
        if confirm.lower() in ['j', 'ja', 'y', 'yes']:
            self.storage.add_excluded_chat(name)
            print(f"Chat mit '{name}' wurde ausgeschlossen.")
            return True
        else:
            print("Ausschluss abgebrochen.")
            return False

    def include_chat(self, name):
        """Include a chat by name"""
        excluded_chats = self.storage.get_excluded_chats()
        if name not in excluded_chats:
            print(f"Chat mit '{name}' ist nicht ausgeschlossen.")
            return False
        
        # Get confirmation
        confirm = input(f"Mochtest du den Chat mit '{name}' wieder zur automatischen Verarbeitung hinzufugen? (j/n): ")
        if confirm.lower() in ['j', 'ja', 'y', 'yes']:
            self.storage.remove_excluded_chat(name)
            print(f"Chat mit '{name}' wurde wieder hinzugefugt.")
            return True
        else:
            print("Hinzufugung abgebrochen.")
            return False

    def list_excluded_chats(self):
        """List all excluded chats"""
        # Use local cache first, then fallback to storage
        if hasattr(self, 'excluded_chats'):
            excluded_chats = self.excluded_chats
        else:
            excluded_chats = self.storage.get_excluded_chats()
            self.excluded_chats = excluded_chats
        
        if not excluded_chats:
            print("Keine ausgeschlossenen Chats.")
        else:
            print("Ausgeschlossene Chats:")
            for name in excluded_chats:
                print(f"  - {name}")

    def list_active_chats(self):
        """List all active chats with their current phase"""
        if not self.chat_managers:
            print("Keine aktiven Chats.")
            return
        
        print("Aktive Chats:")
        for match_id, chat_manager in self.chat_managers.items():
            if chat_manager.active:
                name = self.get_match_name_by_id(match_id) or "Unbekannt"
                message_count = len(chat_manager.chat_history.messages)
                current_phase, _ = chat_manager.phase_manager.get_current_phase(message_count)
                print(f"  - {name} (Phase: {current_phase}, Nachrichten: {message_count})")

    def process_matches(self):
        """Process new matches and clean up deleted matches"""
        if self.debug_settings.get('bot_debug', True):
            print("Fetching matches from Tinder API...")
            sys.stdout.flush()
        try:
            result = self.api.matches()
            if isinstance(result, dict):
                api_ok = result.get('ok', False)
                matches = result.get('matches', [])
                error_type = result.get('error')
                status_code = result.get('status')
            else:
                # Backward compatibility if function still returns list
                api_ok = True
                matches = result or []
                error_type = None
                status_code = 200
            
            if self.debug_settings.get('bot_debug', True):
                print(f"API call completed ok={api_ok} status={status_code} error={error_type} matches={len(matches)}")
                sys.stdout.flush()
        except Exception as e:
            print(f"Failed to fetch matches: {e}")
            sys.stdout.flush()
            return [], []
        
        try:
            # Use local cache first, then fallback to storage
            if hasattr(self, 'excluded_chats'):
                excluded_names = self.excluded_chats
            else:
                excluded_names = self.storage.get_excluded_chats()
                self.excluded_chats = excluded_names
            
            if self.debug_settings.get('bot_debug', True):
                print(f"Found {len(matches)} total matches, {len(excluded_names)} excluded")
                sys.stdout.flush()
        except Exception as e:
            print(f"Failed to get excluded chats: {e}")
            sys.stdout.flush()
            excluded_names = []

        # Wenn API nicht ok ist zB ungültiger Token oder Netzfehler KEIN Cleanup
        if not api_ok:
            if self.debug_settings.get('bot_debug', True):
                print("API not ok skip cleanup and keep existing chats intact")
                sys.stdout.flush()
            # Keine neuen Matches starten wenn Token ungültig ist
            return matches, []

        # Get current match IDs from Tinder API
        current_match_ids = {match["_id"] for match in matches}
        
        # Find deleted matches (in known_match_ids but not in current_match_ids)
        deleted_match_ids = self.known_match_ids - current_match_ids
        
        if deleted_match_ids and self.debug_settings.get('bot_debug', True):
            print(f"Found {len(deleted_match_ids)} deleted matches to clean up")
            sys.stdout.flush()
            
            # Clean up deleted matches
            for deleted_match_id in deleted_match_ids:
                self.cleanup_deleted_match(deleted_match_id)
        
        new_matches = []
        for match in matches:
            match_id = match["_id"]
            match_name = match["person"]["name"]
            
            # ANTI-DUPLICATION: Check if match is already being processed
            if match_id in self.known_match_ids:
                continue
                
            # ANTI-DUPLICATION: Check if chat manager already exists
            if match_id in self.chat_managers:
                print(f"ANTI-DUPLICATION: Chat manager already exists for {match_name}, skipping")
                sys.stdout.flush()
                continue
            
            # Check if this match is excluded
            if match_name in excluded_names:
                if self.debug_settings.get('bot_debug', True):
                    print(f"Skipping excluded match: {match_name}")
                    sys.stdout.flush()
                continue
            
            # IMPROVED LOGIC: Check if match has existing conversations
            match_messages = match.get("messages", [])
            has_existing_conversation = len(match_messages) > 0
            
            if has_existing_conversation:
                # Match has existing conversations - treat as existing match, not new
                print(f"EXISTING MATCH: {match_name} has {len(match_messages)} existing messages, treating as existing match")
                sys.stdout.flush()
                
                # Mark as known but don't add to new_matches
                self.known_match_ids.add(match_id)
                
                # IMPROVED: Create chat manager for existing match if it doesn't exist
                if match_id not in self.chat_managers:
                    print(f"Creating chat manager for existing match: {match_name}")
                    sys.stdout.flush()
                    try:
                        # Get user info for the match
                        user_info = self.api.get_user_info(match["person"]["_id"])
                        if user_info:
                            chat_manager = ChatManager(self.api)
                            chat_manager.match_id = match_id
                            chat_manager.match_name = match_name
                            chat_manager.match_info = user_info
                            chat_manager.active = True
                            
                            # Add existing messages to chat history
                            for msg in match_messages:
                                if msg.get("from") == self.api.user_id:
                                    # Our message
                                    from langchain_core.messages import AIMessage
                                    ai_msg = AIMessage(content=msg.get("message", ""))
                                    chat_manager.chat_history.add_ai_message(ai_msg)
                                else:
                                    # Their message
                                    from langchain_core.messages import HumanMessage
                                    human_msg = HumanMessage(content=msg.get("message", ""))
                                    chat_manager.chat_history.add_user_message(human_msg)
                            
                            self.chat_managers[match_id] = chat_manager
                            print(f"Chat manager created for existing match: {match_name}")
                        else:
                            print(f"Could not get user info for existing match: {match_name}")
                    except Exception as e:
                        print(f"Error creating chat manager for existing match {match_name}: {e}")
                        sys.stdout.flush()
                
                continue
            
            # Check for custom match instructions
            custom_instruction = self.get_match_instruction(match_name)
            if custom_instruction and self.debug_settings.get('bot_debug', True):
                print(f"Found custom instruction for {match_name}: {custom_instruction[:50]}...")
                sys.stdout.flush()
            
            if self.debug_settings.get('bot_debug', True):
                print(f"NEW MATCH: {match_name} ({match_id[:8]}...) - no existing conversations")
                sys.stdout.flush()
            
            # ANTI-DUPLICATION: Mark match as known BEFORE processing
            self.known_match_ids.add(match_id)
            new_matches.append(match)
        
        return matches, new_matches

    def cleanup_deleted_match(self, match_id):
        """Clean up data for a deleted match"""
        try:
            print(f"Cleaning up deleted match: {match_id[:8]}...")
            sys.stdout.flush()
            
            # Remove from known_match_ids
            if match_id in self.known_match_ids:
                self.known_match_ids.remove(match_id)
                print(f"   Removed {match_id[:8]}... from known_match_ids")
                sys.stdout.flush()
            
            # Remove from chat_managers
            if match_id in self.chat_managers:
                chat_manager = self.chat_managers[match_id]
                
                # Stop the response timer if it exists
                if hasattr(chat_manager, 'response_timer'):
                    try:
                        chat_manager.response_timer.stop()
                        print(f"   Stopped response timer for {match_id[:8]}...")
                        sys.stdout.flush()
                    except Exception as e:
                        print(f"   Error stopping response timer for {match_id[:8]}...: {e}")
                        sys.stdout.flush()
                
                # Remove chat manager
                del self.chat_managers[match_id]
                print(f"   Removed chat manager for {match_id[:8]}...")
                sys.stdout.flush()
            
            # Remove from chats data
            if match_id in self.chats:
                del self.chats[match_id]
                print(f"   Removed chat data for {match_id[:8]}...")
                sys.stdout.flush()
            
            # Remove from known_message_ids (messages from this match)
            # This is a bit more complex as we need to identify messages by match_id
            # For now, we'll keep message IDs as they might be referenced elsewhere
            # In a future enhancement, we could add match_id tracking to messages
            
            print(f"Successfully cleaned up deleted match: {match_id[:8]}...")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"Error cleaning up deleted match {match_id[:8]}...: {e}")
            sys.stdout.flush()

    def get_match_instruction(self, match_name):
        """Get custom instruction for a specific match"""
        try:
            instructions_file = "match_instructions.json"
            if os.path.exists(instructions_file):
                with open(instructions_file, 'r', encoding='utf-8') as f:
                    match_instructions = json.load(f)
                    if match_name in match_instructions:
                        data = match_instructions[match_name]
                        if data.get('active', True):
                            return data.get('instruction', '')
            return None
        except Exception as e:
            print(f"Error getting match instruction: {e}")
            return None

    def process_messages(self, matches):
        """Process new messages"""
        try:
            # Use local cache first, then fallback to storage
            if hasattr(self, 'excluded_chats'):
                excluded_names = self.excluded_chats
            else:
                excluded_names = self.storage.get_excluded_chats()
                self.excluded_chats = excluded_names
        except Exception as e:
            print(f"Failed to get excluded chats in process_messages: {e}")
            sys.stdout.flush()
            excluded_names = []
        
        new_messages = []
        total_messages = 0
        new_message_count = 0
        
        print(f"Processing messages for {len(matches)} matches...")
        sys.stdout.flush()
        
        for match in matches:
            match_name = match["person"]["name"]
            
            # Skip if match is excluded
            if match_name in excluded_names:
                print(f"Skipping messages from excluded match: {match_name}")
                sys.stdout.flush()
                continue
            
            print(f"Checking messages for match {match['_id'][:8]}... ({match_name})")
            sys.stdout.flush()
            
            match_messages = match.get("messages", [])
            message_count = len(match_messages)
            total_messages += message_count
            
            print(f"Found {message_count} total messages for {match_name}")
            sys.stdout.flush()
            
            # Show message details for better debugging
            if message_count > 0:
                print(f"   Messages: {[msg.get('_id', 'no_id')[:8] + '...' for msg in match_messages[:3]]}")
                if message_count > 3:
                    print(f"   ... and {message_count - 3} more messages")
            
            for message in match_messages:
                message_id = message["_id"]
                
                # ANTI-DUPLICATION: Check if message is already known
                if message_id in self.known_message_ids:
                    continue
                
                # ANTI-DUPLICATION: Check if message is from us (bot)
                if message.get("from") == self.api.user_id:
                    print(f"ANTI-DUPLICATION: Skipping our own message: {message_id[:8]}...")
                    sys.stdout.flush()
                    self.known_message_ids.add(message_id)  # Mark as known
                    continue
                
                print(f"New message found: {message_id[:8]}... from {match_name}")
                sys.stdout.flush()
                
                # ANTI-DUPLICATION: Mark message as known BEFORE processing
                self.known_message_ids.add(message_id)
                new_messages.append(message)
                new_message_count += 1
        
        print(f"Message processing summary: {total_messages} total messages found, {new_message_count} new messages")
        sys.stdout.flush()
        
        return new_messages

    def start_new_chats(self, new_matches):
        """Start new chats with new matches"""
        for match in new_matches:
            match_name = match['person']['name']
            match_id = match['_id']
            
            # ANTI-DUPLICATION: Double-check that chat manager doesn't exist
            if match_id in self.chat_managers:
                print(f"ANTI-DUPLICATION: Chat manager already exists for {match_name}, skipping")
                sys.stdout.flush()
                continue
            
            print(f"New match found: {match_id} ({match_name})")
            print(f"Waiting 1 minute before starting conversation...")
            
            # Wait 1 minute before starting the conversation
            import time
            time.sleep(60)  # 60 seconds = 1 minute
            
            # ANTI-DUPLICATION: Check again after waiting
            if match_id in self.chat_managers:
                print(f"ANTI-DUPLICATION: Chat manager created during wait for {match_name}, skipping")
                sys.stdout.flush()
                continue
            
            print(f"Starting conversation with {match_name} after 1 minute wait...")
            
            user_info = self.api.get_user_info(match["person"]["_id"])
            if user_info:
                print(f"User info for {match_id}: {user_info}")
                
                # ANTI-DUPLICATION: Create chat manager with lock
                try:
                    chat_manager = ChatManager(self.api)
                    chat_manager.start_chat(match["_id"], user_info, debug=False)
                    
                    # ANTI-DUPLICATION: Final check before adding
                    if match_id not in self.chat_managers:
                        self.chat_managers[match["_id"]] = chat_manager
                        print(f"Chat started successfully with {match_name}")
                    else:
                        print(f"ANTI-DUPLICATION: Chat manager was created elsewhere for {match_name}")
                        # Clean up the duplicate chat manager
                        if hasattr(chat_manager, 'response_timer'):
                            chat_manager.response_timer.stop()
                except Exception as e:
                    print(f"Error creating chat manager for {match_name}: {e}")
                    sys.stdout.flush()
            else:
                print(f"Could not get user info for {match_name}")

    def handle_new_messages(self, new_messages):
        """Handle new messages from matches"""
        # Use local cache first, then fallback to storage
        if hasattr(self, 'excluded_chats'):
            excluded_names = self.excluded_chats
        else:
            excluded_names = self.storage.get_excluded_chats()
            self.excluded_chats = excluded_names
        
        # Check if this is the first startup
        is_first_startup = getattr(self, 'first_startup', False)
        if is_first_startup and new_messages:
            print(f"First startup detected - processing {len(new_messages)} messages immediately (no delay)")
        
        # ANTI-DUPLICATION: Track processed messages to prevent duplicates
        processed_messages = set()
        
        for message in new_messages:
            message_id = message["_id"]
            user_id = message["match_id"]
            
            # ANTI-DUPLICATION: Check if message was already processed in this session
            if message_id in processed_messages:
                print(f"ANTI-DUPLICATION: Message {message_id[:8]}... already processed in this session, skipping")
                sys.stdout.flush()
                continue
            
            # ANTI-DUPLICATION: Check if message is from us
            if message["from"] == self.api.user_id:
                print(f"ANTI-DUPLICATION: Skipping our own message: {message_id[:8]}...")
                sys.stdout.flush()
                continue
            
            print(f"New message received: {message_id[:8]}...")
            sys.stdout.flush()
            
            # Check if this match is excluded
            match_name = self.get_match_name_by_id(user_id)
            if match_name in excluded_names:
                print(f"Uberspringe Nachricht von ausgeschlossenem Match: {match_name}")
                sys.stdout.flush()
                continue
            
            if user_id in self.chat_managers:
                # ANTI-DUPLICATION: Mark message as processed before handling
                processed_messages.add(message_id)
                
                # Pass the first_startup flag to handle_message
                try:
                    self.chat_managers[user_id].handle_message(message, debug=False, first_startup=is_first_startup)
                except Exception as e:
                    print(f"Error handling message for {match_name}: {e}")
                    sys.stdout.flush()
            else:
                print(f"No chat manager for user {user_id}")
                sys.stdout.flush()
        
        # Clear the first startup flag after processing all messages
        if is_first_startup:
            self.first_startup = False
            print("First startup processing completed - normal timing will be used from now on")

    def save_data(self):
        """Save all data to persistent storage"""
        try:
            # Save core data
            core_data = {
                'known_match_ids': list(self.known_match_ids),
                'known_message_ids': list(self.known_message_ids),
                'chats': {user_id: manager.chat_history.messages for user_id, manager in self.chat_managers.items()}
            }
            
            # Save excluded chats separately to ensure persistence
            if hasattr(self, 'excluded_chats'):
                core_data['excluded_chat_names'] = list(self.excluded_chats)
            
            # Save chat manager timing data
            chat_timing = {}
            for user_id, manager in self.chat_managers.items():
                if hasattr(manager, 'last_bot_message_time') and manager.last_bot_message_time:
                    chat_timing[user_id] = {
                        'last_bot_message_time': manager.last_bot_message_time,
                        'match_name': getattr(manager, 'match_name', 'Unknown')
                    }
            
            if chat_timing:
                core_data['chat_timing'] = chat_timing
            
            # Save using the robust method
            self.storage.save_essential_data(core_data)
            print(f"Saved data: {len(self.known_match_ids)} matches, {len(self.known_message_ids)} messages, {len(self.excluded_chats) if hasattr(self, 'excluded_chats') else 0} excluded chats, {len(chat_timing)} chat timing records")
        except Exception as e:
            print(f"Failed to save data: {e}")
            # Fallback to basic save
            self.storage.save({
                'known_match_ids': list(self.known_match_ids),
                'known_message_ids': list(self.known_message_ids),
                'chats': {user_id: manager.chat_history.messages for user_id, manager in self.chat_managers.items()}
            })

    def refresh_excluded_chats(self):
        """Refresh excluded chats from storage during runtime"""
        self.excluded_chats = self.storage.get_excluded_chats()
        print(f"Refreshed excluded chats: {list(self.excluded_chats)}")
        return self.excluded_chats

    def update_excluded_chats(self, chat_name, exclude=True):
        """Update excluded chats during runtime"""
        if exclude:
            self.storage.add_excluded_chat(chat_name)
            self.excluded_chats.add(chat_name)
            print(f"Debug: Added '{chat_name}' to excluded chats during runtime")
        else:
            self.storage.remove_excluded_chat(chat_name)
            if chat_name in self.excluded_chats:
                self.excluded_chats.remove(chat_name)
            print(f"Debug: Removed '{chat_name}' from excluded chats during runtime")
        
        # Save the updated excluded chats immediately
        self.save_excluded_chats()

    def save_excluded_chats(self):
        """Save excluded chats to persistent storage"""
        try:
            # Get current data
            data = self.storage.load() or {}
            # Update excluded chats
            data['excluded_chat_names'] = list(self.excluded_chats)
            # Save using the robust method
            self.storage.save_essential_data(data)
            print(f"Debug: Saved {len(self.excluded_chats)} excluded chats to persistent storage")
        except Exception as e:
            print(f"ERROR: Failed to save excluded chats: {e}")

    def get_scheduled_response_times(self):
        """Get all currently scheduled response times"""
        scheduled_times = {}
        total_scheduled = 0
        
        # Check all chat managers for scheduled responses
        for match_id, chat_manager in self.chat_managers.items():
            if hasattr(chat_manager, 'response_timer') and hasattr(chat_manager.response_timer, 'scheduled_responses'):
                response_timer = chat_manager.response_timer
                scheduled_count = len(response_timer.scheduled_responses)
                total_scheduled += scheduled_count
                
                if scheduled_count > 0:
                    # Get match name for display using the proper method
                    match_name = self.get_match_name_by_id(match_id) or f"Match_{match_id[:8]}"
                    
                    # Get scheduled response details
                    for scheduled_match_id, response_data in response_timer.scheduled_responses.items():
                        scheduled_time = response_data.get('response_time', 0)
                        delay_seconds = response_data.get('delay_seconds', 0)
                        
                        # Calculate remaining time
                        current_time = time.time()
                        remaining_seconds = max(0, scheduled_time - current_time)
                        remaining_minutes = remaining_seconds / 60
                        
                        scheduled_times[scheduled_match_id] = {
                            'match_name': match_name,
                            'remaining_minutes': remaining_minutes,
                            'delay_seconds': delay_seconds,
                            'scheduled_time': scheduled_time
                        }
        
        return scheduled_times, total_scheduled

    def print_status_summary(self, matches, new_matches, new_messages, scheduled_times, total_scheduled):
        """Print a professional status summary"""
        current_time = time.strftime('%H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"TINDERGPT STATUS UPDATE - {current_time}")
        print(f"{'='*60}")
        
        # Connection status
        print(f"CONNECTION: Active (PID: {os.getpid()})")
        
        # Chat management
        print(f"CHAT MANAGEMENT:")
        print(f"   • Active chats: {len(self.chat_managers)}")
        print(f"   • Excluded chats: {len(self.excluded_chats)}")
        print(f"   • Total matches: {len(matches)}")
        
        # Activity summary
        print(f"ACTIVITY SUMMARY:")
        if new_matches:
            print(f"   • New matches: {len(new_matches)}")
        if new_messages:
            print(f"   • New messages: {len(new_messages)}")
        if not new_matches and not new_messages:
            print(f"   • No new activity")
        
        # Scheduled responses
        if total_scheduled > 0:
            print(f"SCHEDULED RESPONSES ({total_scheduled}):")
            for match_id, data in scheduled_times.items():
                match_name = data['match_name']
                remaining = data['remaining_minutes']
                delay = data['delay_seconds'] / 60
                
                if remaining > 0:
                    print(f"   • {match_name}: {remaining:.1f}min remaining (planned: {delay:.1f}min)")
                else:
                    print(f"   • {match_name}: Ready to send (planned: {delay:.1f}min)")
        else:
            print(f"SCHEDULED RESPONSES: None")
        
        print(f"{'='*60}\n")

    def bot_loop(self):
        """Main bot loop"""
        print("TinderGPT Bot gestartet - Überwache neue Matches und Nachrichten...")
        sys.stdout.flush()
        print(f"Bot PID: {os.getpid()}")
        sys.stdout.flush()
        print(f"Monitoring {len(self.chat_managers)} active chats")
        sys.stdout.flush()
        
        # Connection test counter
        connection_test_counter = 0
        last_connection_test = time.time()
        
        while self.bot_running:
            try:
                # Check for reload request
                if self.reload_requested:
                    print("Reloading configuration...")
                    sys.stdout.flush()
                    self.reload_configuration()
                
                # Test connection every 5 minutes (300 seconds)
                current_time = time.time()
                if current_time - last_connection_test > 300:
                    print("Testing Tinder API connection...")
                    sys.stdout.flush()
                    
                    success, message = self.api.test_connection()
                    if success:
                        print(f"Connection test successful - {message}")
                        sys.stdout.flush()
                        connection_test_counter = 0  # Reset counter on success
                    else:
                        connection_test_counter += 1
                        print(f"Connection test failed (attempt {connection_test_counter}): {message}")
                        sys.stdout.flush()
                        
                # Auto-trigger Tinder setup after multiple failures
                if connection_test_counter >= 3:
                    print(f"Multiple connection failures ({connection_test_counter}).")
                    print("Auto-triggering Tinder setup...")
                    sys.stdout.flush()
                    
                    try:
                        from src.utils.tinder_setup import TinderSetup
                        setup = TinderSetup()
                        if setup.auto_setup_trigger():
                            print("Tinder setup completed successfully")
                            connection_test_counter = 0  # Reset counter
                            continue
                        else:
                            print("Tinder setup failed or was skipped")
                    except ImportError:
                        print("Tinder setup system not available")
                    
                    print("Waiting 5 minutes before retry...")
                    sys.stdout.flush()
                    time.sleep(300)  # Wait 5 minutes
                    continue
                elif connection_test_counter >= 1:
                    print(f"Connection failed. Waiting 60 seconds before retry...")
                    sys.stdout.flush()
                    time.sleep(60)  # Wait 1 minute
                    continue
                
                last_connection_test = current_time
                
                # Refresh excluded chats to pick up runtime changes
                self.refresh_excluded_chats()
                
                # Process matches and messages
                matches, new_matches = self.process_matches()
                new_messages = self.process_messages(matches)
                
                # Get scheduled response times
                scheduled_times, total_scheduled = self.get_scheduled_response_times()
                
                # Print professional status summary
                self.print_status_summary(matches, new_matches, new_messages, scheduled_times, total_scheduled)
                
                # Handle new matches
                if new_matches:
                    print(f"Processing {len(new_matches)} new matches...")
                    sys.stdout.flush()
                    self.start_new_chats(new_matches)
                
                # Handle new messages
                if new_messages:
                    print(f"Processing {len(new_messages)} new messages...")
                    sys.stdout.flush()
                    self.handle_new_messages(new_messages)

                # Save data
                print("Saving data...")
                sys.stdout.flush()
                self.save_data()
                
                print("Waiting 10 seconds...")
                sys.stdout.flush()
                time.sleep(10)  # Wait to avoid rate limits
                
            except Exception as e:
                print(f"ERROR: Fehler im Bot-Loop: {e}")
                sys.stdout.flush()
                print(f"Debug: Waiting 30 seconds due to error...")
                sys.stdout.flush()
                time.sleep(30)  # Wait longer on error

    def start_bot(self):
        """Start the bot in a separate thread"""
        if self.bot_running:
            print("Bot lauft bereits!")
            return
        
        self.bot_running = True
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        print("Bot gestartet!")

    def stop_bot(self):
        """Stop the bot"""
        if not self.bot_running:
            print("Bot lauft nicht!")
            return
        
        self.bot_running = False
        if self.bot_thread:
            self.bot_thread.join(timeout=5)
        print("Bot gestoppt!")

def main():
    """Main function - starts bot directly"""
    import pyfiglet
    ascii_art = pyfiglet.figlet_format("Starvincis TinderBot", font="slant")
    print(ascii_art)
    
    controller = BotController()
    
    print("Bot wird gestartet...")
    controller.start_bot()
    
    # Keep the main thread alive
    try:
        while controller.bot_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBot wird beendet...")
        controller.stop_bot()
        print("Auf Wiedersehen!")

if __name__ == "__main__":
    main()

