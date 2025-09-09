from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class WebConfigApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'tindergpt_webconfig_secret_key_2024'
        self.setup_routes()
        
        # Paths
        self.config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'config', 'config.json')
        self.match_instructions_path = os.path.join(os.path.dirname(__file__), '..', '..', 'match_instructions.json')
        self.persistent_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'persistent_data.pkl')
        
        # Create match_instructions.json if it doesn't exist
        if not os.path.exists(self.match_instructions_path):
            try:
                with open(self.match_instructions_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=4)
                print(f"Created empty match_instructions.json at {self.match_instructions_path}")
            except Exception as e:
                print(f"Error creating match_instructions.json: {e}")
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
            
        @self.app.route('/api/config')
        def get_config():
            try:
                print(f"Loading config from: {self.config_path}")
                if not os.path.exists(self.config_path):
                    print(f"Config file not found: {self.config_path}")
                    return jsonify({'error': f'Config file not found: {self.config_path}'}), 404
                    
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"Successfully loaded config with {len(config)} keys")
                return jsonify(config)
            except Exception as e:
                print(f"Error loading config: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/config', methods=['POST'])
        def save_config():
            try:
                config_data = request.json
                
                # Load existing config to merge with new data
                existing_config = {}
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                    
                    # Backup existing config
                    backup_path = f"{self.config_path}.backup.{int(time.time())}"
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        with open(backup_path, 'w', encoding='utf-8') as backup:
                            backup.write(f.read())
                
                # Merge new data with existing config
                merged_config = {**existing_config, **config_data}
                
                # Save merged config
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_config, f, indent=4, ensure_ascii=False)
                    
                return jsonify({'success': True, 'message': 'Konfiguration gespeichert'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/match_instructions')
        def get_match_instructions():
            try:
                print(f"Loading match instructions from: {self.match_instructions_path}")
                if os.path.exists(self.match_instructions_path):
                    with open(self.match_instructions_path, 'r', encoding='utf-8') as f:
                        instructions = json.load(f)
                    print(f"Successfully loaded {len(instructions)} match instructions")
                else:
                    instructions = {}
                    print("No match instructions file found, returning empty dict")
                return jsonify(instructions)
            except Exception as e:
                print(f"Error loading match instructions: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/match_instructions', methods=['POST'])
        def save_match_instructions():
            try:
                instructions_data = request.json
                
                # Backup existing instructions
                if os.path.exists(self.match_instructions_path):
                    backup_path = f"{self.match_instructions_path}.backup.{int(time.time())}"
                    with open(self.match_instructions_path, 'r', encoding='utf-8') as f:
                        with open(backup_path, 'w', encoding='utf-8') as backup:
                            backup.write(f.read())
                
                # Save new instructions
                with open(self.match_instructions_path, 'w', encoding='utf-8') as f:
                    json.dump(instructions_data, f, indent=4, ensure_ascii=False)
                    
                return jsonify({'success': True, 'message': 'Match-Anweisungen gespeichert'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/excluded_chats')
        def get_excluded_chats():
            try:
                print(f"Loading excluded chats from: {self.persistent_data_path}")
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage(self.persistent_data_path)
                excluded_chats = list(storage.get_excluded_chats())
                print(f"Successfully loaded {len(excluded_chats)} excluded chats: {excluded_chats}")
                return jsonify(excluded_chats)
            except Exception as e:
                print(f"Error loading excluded chats: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/excluded_chats', methods=['POST'])
        def save_excluded_chats():
            try:
                excluded_data = request.json
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage(self.persistent_data_path)
                
                # Clear existing and add new
                current_excluded = storage.get_excluded_chats()
                for chat in current_excluded:
                    storage.remove_excluded_chat(chat)
                    
                for chat in excluded_data:
                    storage.add_excluded_chat(chat)
                    
                return jsonify({'success': True, 'message': 'Ausgeschlossene Chats gespeichert'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/debug_settings')
        def get_debug_settings():
            try:
                print(f"Loading debug settings from: {self.persistent_data_path}")
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage(self.persistent_data_path)
                debug_settings = storage.get_debug_settings()
                print(f"Successfully loaded debug settings: {debug_settings}")
                return jsonify(debug_settings)
            except Exception as e:
                print(f"Error loading debug settings: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/debug_settings', methods=['POST'])
        def save_debug_settings():
            try:
                debug_data = request.json
                from src.utils.storage import PersistentStorage
                storage = PersistentStorage(self.persistent_data_path)
                
                for setting, value in debug_data.items():
                    storage.update_debug_setting(setting, value)
                    
                return jsonify({'success': True, 'message': 'Debug-Einstellungen gespeichert'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/system_status')
        def get_system_status():
            try:
                status = {
                    'config_exists': os.path.exists(self.config_path),
                    'match_instructions_exists': os.path.exists(self.match_instructions_path),
                    'persistent_data_exists': os.path.exists(self.persistent_data_path),
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/bot_status')
        def get_bot_status():
            try:
                # Simple bot status without deployment module dependency
                bot_status = {
                    'is_running': False,  # Default to False since we can't check easily
                    'current_version': '1.0.18',  # Hardcoded for now
                    'total_matches': 0,
                    'active_chats': 0,
                    'excluded_chats': 0,
                    'scheduled_responses': {},
                    'total_scheduled': 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Try to get excluded chats count from storage
                try:
                    from src.utils.storage import PersistentStorage
                    storage = PersistentStorage(self.persistent_data_path)
                    excluded_chats = storage.get_excluded_chats()
                    bot_status['excluded_chats'] = len(excluded_chats)
                except Exception as e:
                    print(f"Could not get excluded chats count: {e}")
                
                return jsonify(bot_status)
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/bot_control', methods=['POST'])
        def bot_control():
            try:
                action = request.json.get('action')
                
                if action not in ['start', 'stop']:
                    return jsonify({'error': 'Invalid action'}), 400
                
                from deployment.deployment import DeploymentManager
                manager = DeploymentManager()
                
                if action == 'start':
                    if manager.is_running:
                        return jsonify({'success': False, 'message': 'Bot is already running'})
                    else:
                        success = manager.start_bot()
                        return jsonify({'success': success, 'message': 'Bot started' if success else 'Failed to start bot'})
                elif action == 'stop':
                    if not manager.is_running:
                        return jsonify({'success': False, 'message': 'Bot is not running'})
                    else:
                        manager.stop_bot()
                        return jsonify({'success': True, 'message': 'Bot stopped'})
                        
            except Exception as e:
                return jsonify({'error': str(e)}), 500
                
    def run(self, host='0.0.0.0', port=8080, debug=False):
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    app = WebConfigApp()
    app.run(debug=True)
