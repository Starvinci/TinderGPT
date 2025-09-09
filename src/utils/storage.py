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

import os
import pickle
import time
import json

class PersistentStorage:
    def __init__(self, filename='persistent_data.pkl'):
        self.filename = filename

    def save(self, data):
        with open(self.filename, 'wb') as f:
            pickle.dump(data, f)

    def load(self):
        if os.path.exists(self.filename):
            if os.path.getsize(self.filename) > 0:  # Check if the file is not empty
                try:
                    with open(self.filename, 'rb') as f:
                        return pickle.load(f)
                except (pickle.UnpicklingError, ImportError, AttributeError) as e:
                    print(f"Warning: Could not load pickle file due to compatibility issues: {e}")
                    print("Attempting to recover essential data...")
                    return self._recover_essential_data()
        return None

    def _recover_essential_data(self):
        """Recover essential data from corrupted pickle file"""
        try:
            # Try to load as JSON first (if it was saved as JSON)
            json_filename = self.filename.replace('.pkl', '.json')
            if os.path.exists(json_filename):
                with open(json_filename, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Return minimal essential data
        return {
            'known_match_ids': set(),
            'known_message_ids': set(),
            'chats': {},
            'excluded_chat_names': set(),
            'debug_settings': {
                'bot_debug': False,
                'api_debug': False,
                'chat_debug': False,
                'storage_debug': False
            }
        }

    def save_extended_data(self, data):
        """
        Save extended data including excluded chats, phases, and timing info
        """
        existing_data = self.load() or {}
        existing_data.update(data)
        self.save(existing_data)

    def save_essential_data(self, data):
        """
        Save only essential, serializable data to avoid compatibility issues
        """
        essential_data = {}
        
        # Extract only essential data types
        for key, value in data.items():
            if isinstance(value, (dict, list, set, str, int, float, bool, type(None))):
                if isinstance(value, set):
                    essential_data[key] = list(value)  # Convert set to list for JSON compatibility
                elif isinstance(value, dict):
                    # Recursively handle nested dictionaries
                    essential_data[key] = self._convert_dict_for_storage(value)
                else:
                    essential_data[key] = value
        
        # Save as both pickle and JSON for redundancy
        self.save(essential_data)
        
        # Also save as JSON for better compatibility
        json_filename = self.filename.replace('.pkl', '.json')
        try:
            with open(json_filename, 'w') as f:
                json.dump(essential_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save JSON backup: {e}")

    def _convert_dict_for_storage(self, data_dict):
        """Convert nested dictionary data for storage compatibility"""
        converted = {}
        for key, value in data_dict.items():
            if isinstance(value, set):
                converted[key] = list(value)
            elif isinstance(value, dict):
                converted[key] = self._convert_dict_for_storage(value)
            elif isinstance(value, (list, str, int, float, bool, type(None))):
                converted[key] = value
            else:
                # Skip incompatible types
                converted[key] = str(value)
        return converted

    def get_excluded_chats(self):
        """Get list of excluded chat names"""
        data = self.load()
        if data and 'excluded_chat_names' in data:
            excluded = data['excluded_chat_names']
            # Convert list back to set if it was saved as list
            if isinstance(excluded, list):
                return set(excluded)
            return excluded
        return set()

    def add_excluded_chat(self, chat_name):
        """Add a chat name to excluded list"""
        excluded_chats = self.get_excluded_chats()  # This returns a set
        excluded_chats.add(chat_name)
        
        # Load existing data and update
        existing_data = self.load() or {}
        existing_data['excluded_chat_names'] = list(excluded_chats)  # Convert to list for storage
        
        # Save using the robust method
        self.save_essential_data(existing_data)
        
        print(f"Debug: Added '{chat_name}' to excluded chats. Total: {len(excluded_chats)}")
        return True

    def remove_excluded_chat(self, chat_name):
        """Remove a chat name from excluded list"""
        excluded_chats = self.get_excluded_chats()  # This returns a set
        if chat_name in excluded_chats:
            excluded_chats.remove(chat_name)
            
            # Load existing data and update
            existing_data = self.load() or {}
            existing_data['excluded_chat_names'] = list(excluded_chats)  # Convert to list for storage
            
            # Save using the robust method
            self.save_essential_data(existing_data)
            
            print(f"Debug: Removed '{chat_name}' from excluded chats. Total: {len(excluded_chats)}")
            return True
        return False

    def get_chat_phases(self):
        """Get conversation phases for all chats"""
        data = self.load()
        return data.get('chat_phases', {}) if data else {}

    def set_chat_phase(self, match_id, phase):
        """Set conversation phase for a specific chat"""
        phases = self.get_chat_phases()
        phases[match_id] = phase
        self.save_extended_data({'chat_phases': phases})

    def get_response_timing(self):
        """Get response timing data for all chats"""
        data = self.load()
        return data.get('response_timing', {}) if data else {}

    def set_response_timing(self, match_id, timing_data):
        """Set response timing data for a specific chat"""
        timing = self.get_response_timing()
        timing[match_id] = timing_data
        self.save_extended_data({'response_timing': timing})
    
    def get_debug_settings(self):
        """Get debug settings"""
        data = self.load()
        return data.get('debug_settings', {
            'bot_debug': True,
            'api_debug': True,
            'chat_debug': True,
            'storage_debug': False
        }) if data else {
            'bot_debug': True,
            'api_debug': True,
            'chat_debug': True,
            'storage_debug': False
        }
    
    def set_debug_settings(self, debug_settings):
        """Set debug settings"""
        self.save_extended_data({'debug_settings': debug_settings})
    
    def update_debug_setting(self, setting_name, value):
        """Update a specific debug setting"""
        current_settings = self.get_debug_settings()
        current_settings[setting_name] = value
        self.set_debug_settings(current_settings)

    def cleanup_corrupted_data(self):
        """Clean up corrupted pickle data and save only essential information"""
        print("Cleaning up corrupted persistent data...")
        
        try:
            # Try to load existing data
            existing_data = self.load()
            if existing_data:
                print(f"Found existing data with keys: {list(existing_data.keys())}")
                
                # Extract only essential data
                essential_data = {}
                
                # Handle known_match_ids
                if 'known_match_ids' in existing_data:
                    if isinstance(existing_data['known_match_ids'], set):
                        essential_data['known_match_ids'] = list(existing_data['known_match_ids'])
                    else:
                        essential_data['known_match_ids'] = []
                
                # Handle known_message_ids
                if 'known_message_ids' in existing_data:
                    if isinstance(existing_data['known_message_ids'], set):
                        essential_data['known_message_ids'] = list(existing_data['known_message_ids'])
                    else:
                        essential_data['known_message_ids'] = []
                
                # Handle chats (only basic structure)
                if 'chats' in existing_data:
                    essential_data['chats'] = {}
                
                # Handle excluded_chat_names
                if 'excluded_chat_names' in existing_data:
                    excluded = existing_data['excluded_chat_names']
                    if isinstance(excluded, set):
                        essential_data['excluded_chat_names'] = list(excluded)
                    elif isinstance(excluded, list):
                        essential_data['excluded_chat_names'] = excluded
                    else:
                        essential_data['excluded_chat_names'] = []
                else:
                    essential_data['excluded_chat_names'] = []
                
                # Handle debug_settings
                if 'debug_settings' in existing_data:
                    debug_settings = existing_data['debug_settings']
                    if isinstance(debug_settings, dict):
                        essential_data['debug_settings'] = {
                            'bot_debug': debug_settings.get('bot_debug', False),
                            'api_debug': debug_settings.get('api_debug', False),
                            'chat_debug': debug_settings.get('chat_debug', False),
                            'storage_debug': debug_settings.get('storage_debug', False)
                        }
                    else:
                        essential_data['debug_settings'] = {
                            'bot_debug': False,
                            'api_debug': False,
                            'chat_debug': False,
                            'storage_debug': False
                        }
                else:
                    essential_data['debug_settings'] = {
                        'bot_debug': False,
                        'api_debug': False,
                        'chat_debug': False,
                        'storage_debug': False
                    }
                
                # Save cleaned data
                self.save_essential_data(essential_data)
                print(f"Successfully cleaned and saved essential data: {list(essential_data.keys())}")
                return True
            else:
                print("No existing data found, creating fresh storage")
                self.save_essential_data(self._recover_essential_data())
                return True
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
            print("Creating fresh storage...")
            self.save_essential_data(self._recover_essential_data())
            return False