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
import time
import random
import threading
import os
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict

class ResponseTimer:
    def __init__(self, config):
        self.config = config
        self.scheduled_responses = {}
        self.timer_thread = None
        self.running = False

    def start(self):
        """Start the timer thread"""
        if not self.running:
            self.running = True
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()

    def stop(self):
        """Stop the timer thread"""
        self.running = False

    def _timer_loop(self):
        """Main timer loop that checks for scheduled responses"""
        while self.running:
            current_time = time.time()
            responses_to_send = []
            
            # Check which responses are due
            for match_id, response_data in self.scheduled_responses.items():
                if current_time >= response_data['response_time']:
                    responses_to_send.append((match_id, response_data))
            
            # Send responses
            for match_id, response_data in responses_to_send:
                try:
                    # Calculate actual wait time
                    actual_wait_time = current_time - response_data['scheduled_at']
                    planned_wait_time = response_data['delay_seconds']
                    
                    # Log timing information
                    print(f"Sending delayed response to {match_id}")
                    print(f"   Planned wait: {planned_wait_time:.1f}s")
                    print(f"   Actual wait: {actual_wait_time:.1f}s")
                    print(f"   Timing accuracy: {((actual_wait_time - planned_wait_time) / planned_wait_time * 100):+.1f}%")
                    print(f"   Message: {response_data['message_content'][:50]}...")
                    
                    # Send the message using the new message splitting functionality
                    if response_data.get('chat_manager'):
                        try:
                            # Use the chat manager's parse_and_send_response method
                            response_data['chat_manager'].parse_and_send_response(
                                response_data['message_content'], 
                                match_id, 
                                debug=False
                            )
                            print(f"   ✅ Message sent using new splitting functionality!")
                        except Exception as e:
                            print(f"   ⚠️  Could not use chat manager splitting: {e}")
                            # Fallback to direct API call
                            response_data['api'].send_message(match_id, response_data['message_content'])
                            print(f"   ✅ Message sent using fallback method!")
                    else:
                        # Fallback to direct API call if no chat manager
                        response_data['api'].send_message(match_id, response_data['message_content'])
                        print(f"   ✅ Message sent using fallback method!")
                    
                    # Note: update_last_bot_message_time is now handled by parse_and_send_response
                    
                except Exception as e:
                    print(f"❌ Error sending delayed response: {e}")
                finally:
                    del self.scheduled_responses[match_id]
            
            time.sleep(1)  # Check every second

    def schedule_response(self, match_id, delay_seconds, message_content, api, chat_manager=None):
        """Schedule a response to be sent after delay_seconds"""
        current_time = time.time()
        response_time = current_time + delay_seconds
        
        # ANTI-DUPLICATION: Check if response is already scheduled for this match
        if match_id in self.scheduled_responses:
            existing_response = self.scheduled_responses[match_id]
            existing_delay = existing_response['delay_seconds']
            existing_time = existing_response['response_time']
            
            print(f"ANTI-DUPLICATION: Response already scheduled for {match_id}")
            print(f"   ⏰ Existing: {existing_delay:.1f}s delay, will send at {time.strftime('%H:%M:%S', time.localtime(existing_time))}")
            print(f"   ⏰ New: {delay_seconds:.1f}s delay, would send at {time.strftime('%H:%M:%S', time.localtime(response_time))}")
            
            # Use the shorter delay (more responsive)
            if delay_seconds < existing_delay:
                print(f"   ✅ Replacing with shorter delay")
            else:
                print(f"   ⏭️  Keeping existing shorter delay")
                return  # Keep existing response
        
        # Convert to minutes for better readability
        delay_minutes = delay_seconds / 60
        
        # Store additional timing information
        self.scheduled_responses[match_id] = {
            'response_time': response_time,
            'message_content': message_content,
            'api': api,
            'scheduled_at': current_time,
            'delay_seconds': delay_seconds,
            'match_id': match_id,
            'chat_manager': chat_manager,  # Store reference to chat manager
            'message_hash': hash(message_content)  # Add hash for duplicate detection
        }
        
        print(f"Scheduled response for {match_id} in {delay_minutes:.1f} minutes")
        print(f"   Scheduled at: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        print(f"   Will send at: {time.strftime('%H:%M:%S', time.localtime(response_time))}")
        print(f"   Total wait time: {delay_minutes:.1f} minutes ({delay_seconds:.1f} seconds)")

    def get_last_response_time(self, match_id):
        """Get the last response time for a match"""
        # This would be implemented to track when the match last responded
        # For now, return a default value
        return time.time() - 300  # 5 minutes ago as default

class PhaseManager:
    def __init__(self, config):
        self.config = config
        self.phases = config.get('conversation_phases', {})
        self.user_info_levels = config.get('user_info_levels', {})

    def get_current_phase(self, message_count):
        """Determine current phase based on message count"""
        for phase_name, phase_config in self.phases.items():
            min_msg = phase_config.get('min_messages', 1)
            max_msg = phase_config.get('max_messages', 999)
            
            if min_msg <= message_count <= max_msg:
                return phase_name, phase_config
        
        # Default to last phase if message count exceeds all ranges
        last_phase = list(self.phases.keys())[-1]
        return last_phase, self.phases[last_phase]

    def get_user_info_for_phase(self, phase_name):
        """Get user's information level for current phase"""
        phase_config = self.phases.get(phase_name, {})
        info_level = phase_config.get('user_info_level', 'minimal')
        return self.user_info_levels.get(info_level, '')

    def get_phase_goal(self, phase_name):
        """Get the goal for current phase"""
        phase_config = self.phases.get(phase_name, {})
        return phase_config.get('goal', '')

class ChatManager:
    def __init__(self, api, config=None):
        self.api = api
        if isinstance(config, str):
            with open(config, 'r') as file:
                self.config = json.load(file)
        elif isinstance(config, dict):
            self.config = config
        else:
            # Use config from env loader
            try:
                from src.config.env_loader import load_config_with_env
                self.config = load_config_with_env()
            except ImportError:
                print("Warning: Could not import env loader, using default config")
                self.config = {
                    'api_key': 'default_key',
                    'response_timing': {'min_response_time': 30}
                }
        
        self.api_key = self.config['api_key']
        self.model_id = "gpt-5"
        self.chat = ChatOpenAI(api_key=self.api_key, model=self.model_id, temperature=0.2)
        self.chat_history = ChatMessageHistory()
        
        # Load match instructions if available
        self.match_instructions = self._load_match_instructions()    
        self.active = False
        self.match_id = None
        self.match_name = None
        self.match_info = None
        self.last_match_message_time = None
        self.last_bot_message_time = time.time()  # Initialize with current time
        self.bot_message_count = 0
        
        # Initialize managers
        self.phase_manager = PhaseManager(self.config)
        self.response_timer = ResponseTimer(self.config)
        self.response_timer.start()
        
        # Dynamic conversation system
        try:
            from ..dynamics import ConversationDynamics
            self.dynamics = ConversationDynamics(self.config)
        except ImportError:
            self.dynamics = None
            print("Warning: Conversation dynamics not available")

    def setup_prompt_template(self, match_details="", phase_name="icebreaker"):
        """Setup prompt template based on current phase"""
        phase_config = self.phase_manager.phases.get(phase_name, {})
        goal = phase_config.get('goal', '')
        user_info = self.phase_manager.get_user_info_for_phase(phase_name)
        
        details_text = match_details if match_details else "Keine spezifischen Match-Details verfügbar."
        
        # Get user profile info - only include if not in icebreaker phase
        user_profile_info = ""
        if phase_name != "icebreaker":
            if self.api and self.api.user_profile:
                user_profile_info = "Dies ist das Tinder-Profil der Person die du vertrittst: " + self.extract_profile_info(self.api.user_profile)
            else:
                user_profile_info = "Dies ist das Tinder-Profil der Person die du vertrittst: Name: [Nutzer-Name], Bio: [Bio-Text], Interessen: [Interessen], Beruf: [Beruf], Standort: [Standort], Schule: [Schule]"
        
        # Determine if this should be a question message (every second message after phase 1)
        should_ask_question = True
        if phase_name != "icebreaker":
            # Count bot messages in current phase
            phase_start_msg = phase_config.get('min_messages', 1)
            messages_in_phase = self.bot_message_count - (phase_start_msg - 1)
            should_ask_question = (messages_in_phase % 2 == 0)  # Every second message
        
        # Get relationship intent prompt if available
        relationship_prompt = ""
        if hasattr(self, 'match_info') and self.match_info and 'relationship_intent' in self.match_info:
            relationship_intent = self.match_info['relationship_intent']
            relationship_prompts = self.config.get('relationship_intent_prompts', {})
            
            # Find matching prompt (exact match or partial match)
            for intent_key, prompt in relationship_prompts.items():
                if intent_key.lower() in relationship_intent.lower() or relationship_intent.lower() in intent_key.lower():
                    relationship_prompt = f"\n\n{prompt}"
                    break
        
        # Create phase-specific prompt
        phase_prompt = f"""
        {self.config['goals_to_be_achieved']}
        
        AKTUELLE PHASE: {phase_name.upper()}
        PHASEN-ZIEL: {goal}
        
        MATCH-INFO: {details_text}
        
        WICHTIGE KONVERSATIONS-RICHTLINIEN:
        - Berücksichtige die GESAMTE Chat-Historie für Kontext
        - Achte besonders auf die NEUESTEN Nachrichten vom Match
        - Wenn mehrere Nachrichten in kurzer Zeit kamen, beziehe dich auf ALLE
        - Erkenne, wenn das Match mehrere Themen oder Fragen auf einmal angesprochen hat
        - Antworte natürlich und fließend auf die gesamte Konversation
        - Stelle sicher, dass keine wichtigen Punkte aus den neuesten Nachrichten übersehen werden
        """

        # Icebreaker: Priorisiere Bio über Interessen
        if phase_name == "icebreaker":
            phase_prompt += """

PRIORITÄT FÜR ICEBREAKER:
- Nutze PRIMÄR die Bio des Matches für den Aufhänger
- Wenn keine Bio vorhanden oder leer: verwende Interessen oder ein sichtbares Detail
"""
        
        # Add relationship intent prompt if available
        if relationship_prompt:
            phase_prompt += relationship_prompt
        
        # Only add user's info if not in icebreaker phase
        if phase_name != "icebreaker" and user_info:
            phase_prompt += f"\nUSER INFO (AKTUELLE PHASE): {user_info}"
        
        if user_profile_info:
            phase_prompt += f"\n{user_profile_info}"
        
        # Add dynamic conversation instructions if available
        if self.dynamics:
            # Get dynamic adjustments
            topic = self.dynamics.current_topic
            adjustments = self.dynamics.get_dynamic_prompt_adjustments(phase_name, topic)
            
            # Add dynamic instructions
            emoji_intensity = adjustments['emoji_intensity']
            question_freq = adjustments['question_frequency']
            msg_length = adjustments['message_length']
            comm_style = adjustments['communication_style']
            emoji_style = adjustments.get('emoji_style', 'medium')
            writing_style = adjustments.get('writing_style', 'balanced')
            
            # Add detailed style instructions to prompt
            style_instructions = self.generate_style_instructions(adjustments)
            phase_prompt += f"\n\nSTIL-ANPASSUNG (basierend auf Match-Verhalten):\n{style_instructions}"
        
        # Apply custom match instruction if available
        if self.match_name:
            phase_prompt = self.apply_match_instruction_to_prompt(phase_prompt, self.match_name)
            
            phase_prompt += f"""
            
            DYNAMISCHE KONVERSATIONS-RICHTLINIEN:
            - EMOJI-INTENSITÄT: {emoji_intensity} (passe dich an Match-Stil an)
            - FRAGEN-HÄUFIGKEIT: {question_freq:.1%} (stelle Fragen basierend auf Kontext)
            - NACHRICHTEN-LÄNGE: {msg_length} (passe dich an Match-Präferenz an)
            - KOMMUNIKATIONS-STIL: {comm_style} (passe dich an Match-Stil an)
            
            WICHTIG: Sei natürlich und passe dich an den Kommunikationsstil des Matches an.
            """
        
        # Add defensive information instructions
        defensive_info = self.config.get('defensive_info', {})
        if defensive_info:
            defensive_instructions = f"""
DEFENSIVE INFORMATION (NUR bei direkten Fragen verwenden, nie offensiv):
{defensive_info.get('description', '')}
- Lieblingsessen: {defensive_info.get('favorite_food', 'Nicht angegeben')}
- Arbeit: {defensive_info.get('work', 'Nicht angegeben')}
- Reisen: {defensive_info.get('travel', 'Nicht angegeben')}

WICHTIG: Diese Informationen NUR verwenden, wenn der Nutzer direkt danach gefragt wird. Nie alle zusammen geben, sondern stückchenweise und nur bei direkten Fragen.
"""
            phase_prompt += defensive_instructions
        
        # Add recent messages analysis if available
        try:
            recent_context = self.analyze_recent_messages()
            if recent_context:
                phase_prompt += f"\n\n{recent_context}"
        except Exception as e:
            print(f"⚠️  Error analyzing recent messages: {e}")

        # Add message splitting instructions
        message_splitting_instructions = """

MESSAGE SPLITTING OPTION:
Du kannst wählen, ob du eine Nachricht in zwei separate, direkt hintereinander gesendete Nachrichten aufteilst, um authentischer zu wirken.

GRÜNDE FÜR AUFTEILUNG:
- Bei zwei verschiedenen Themen oder Fragen
- Bei Kommentar + Frage Kombinationen
- Um authentischer zu wirken (wie echte Menschen schreiben)
- Bei komplexeren Antworten, die sich in zwei Teile aufteilen lassen

AUFTEILUNGSFORMAT:
Wenn du dich für Aufteilung entscheidest, gib deine Antwort in diesem Format:
[SPLIT:2]
Erste Nachricht
---
Zweite Nachricht

Wenn du bei einer Nachricht bleibst, antworte normal.

BEISPIEL FÜR AUFTEILUNG:
[SPLIT:2]
Das klingt echt spannend! 🎯
---
Was ist dein Lieblingsspiel?

BEISPIEL FÜR EINE NACHRICHT:
Das ist wirklich interessant! Ich spiele auch gerne Schach und finde es toll, wie strategisch das ist. Was ist dein Lieblingszug beim Eröffnen? 🏆
"""
        phase_prompt += message_splitting_instructions
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", phase_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.chain = self.prompt | self.chat

    def extract_profile_info(self, json_data):
        """Extract profile information from Tinder API response"""
        user = json_data['data']['user']
        
        name = user.get('name', 'Unbekannt')
        bio = user.get('bio', 'Keine Bio verfügbar')
        
        interests = [interest['name'] for interest in user.get('user_interests', {}).get('selected_interests', [])]
        interests_str = ', '.join(interests) if interests else 'Keine Interessen angegeben'
        
        job = user.get('jobs', [{'title': {'name': 'Kein Beruf angegeben'}}])[0]['title']['name']
        location = user.get('city', {}).get('name', 'Unbekannter Standort')
        
        schools = [school['name'] for school in user.get('schools', [])]
        schools_str = ', '.join(schools) if schools else 'Keine Schulen angegeben'
        
        profile_info_str = f"Name: {name}, Bio: {bio}, Interessen: {interests_str}, Beruf: {job}, Standort: {location}, Schule: {schools_str}"
        return profile_info_str

    def format_match_infos(self, match_infos):
        """Format match information for prompt"""
        name = match_infos.get('name', 'Unbekannt')
        birth = match_infos.get('birth_date', 'Unbekannt')
        bio = (match_infos.get('bio') or '').strip()
        bio_text = bio if bio else 'Keine Bio vorhanden'
        interests = ', '.join(match_infos.get('interests', [])) if match_infos.get('interests') else 'Keine Interessen angegeben'
        distance = f"{match_infos.get('distance_mi', 'Unbekannt')} Meilen entfernt"
        jobs = ', '.join(match_infos.get('jobs', [])) if match_infos.get('jobs') else 'Kein Beruf angegeben'
        schools = ', '.join(match_infos.get('schools', [])) if match_infos.get('schools') else 'Keine Schulen angegeben'
        
        # Bio explizit hervorheben, damit Icebreaker darauf Bezug nimmt
        return f"Name: {name}, Alter: {birth}, Bio: {bio_text}, Interessen: {interests}, Standort: {distance}, Beruf: {jobs}, Schule: {schools}"
    


    def calculate_response_delay(self):
        """Calculate response delay based on match's response time"""
        # Use the time when we last sent a message, not when we last received one
        last_bot_message_time = self.get_last_bot_message_time()
        if not last_bot_message_time:
            print("⏰ First message - no delay needed")
            # Initialize with current time if not set
            self.update_last_bot_message_time()
            return 0  # First message, send immediately
        
        # Ensure last_bot_message_time is a valid number
        try:
            last_bot_message_time = float(last_bot_message_time)
        except (TypeError, ValueError):
            print("⚠️  Invalid last_bot_message_time, initializing...")
            self.update_last_bot_message_time()
            return 0
        
        # Calculate how long the match took to respond to our last message
        current_time = time.time()
        match_response_time = current_time - last_bot_message_time
        
        # Ensure match_response_time is valid
        if match_response_time < 0:
            print("⚠️  Negative response time detected, using minimum delay...")
            min_time = self.config.get('response_timing', {}).get('min_response_time', 30)
            return min_time
        
        # Convert to minutes for better readability
        match_response_minutes = match_response_time / 60
        
        print(f"MATCH RESPONSE TIMING ANALYSIS:")
        print(f"   Our last message sent: {time.strftime('%H:%M:%S', time.localtime(last_bot_message_time))}")
        print(f"   Current time: {time.strftime('%H:%M:%S', time.localtime(current_time))}")
        print(f"   Match took: {match_response_minutes:.1f} minutes to respond")
        
        # Add random variation (±20%)
        variation = random.uniform(0.8, 1.2)
        bot_response_time = match_response_time * variation
        
        # Convert to minutes for better readability
        bot_response_minutes = bot_response_time / 60
        
        print(f"   Random variation: {variation:.2f}x")
        print(f"   Base bot response time: {bot_response_minutes:.1f} minutes")
        
        # Only apply minimum response time if the calculated time is very short
        # This allows for natural conversation flow while preventing instant responses
        min_time = self.config.get('response_timing', {}).get('min_response_time', 30)
        min_time_minutes = min_time / 60
        
        print(f"   Minimum response time: {min_time_minutes:.1f} minutes")
        
        # If match responded very quickly (< 10 seconds), use minimum time
        # Otherwise, use the calculated time (even if it's shorter than minimum)
        if match_response_time < 10:
            final_delay = max(bot_response_time, min_time)
            final_delay_minutes = final_delay / 60
            print(f"   Fast response detected - using minimum time: {final_delay_minutes:.1f} minutes")
        else:
            # For longer response times, use the calculated time directly
            # This allows for natural conversation flow
            final_delay = bot_response_time
            final_delay_minutes = final_delay / 60
            print(f"   Normal response - using calculated time: {final_delay_minutes:.1f} minutes")
        
        print(f"   Final delay: {final_delay_minutes:.1f} minutes ({final_delay:.1f} seconds)")
        return final_delay

    def start_chat(self, match_id, match_info, debug=False):
        """Start a new chat with a match"""
        if not debug:
            print(f"Starting chat with {match_info.get('name', 'Unknown')}")
            
            self.match_id = match_id
            self.match_name = match_info.get('name', 'Unknown')
            self.match_info = match_info
            self.bot_message_count = 0
            
            match_details = self.format_match_infos(match_info) if match_info else ""
            self.setup_prompt_template(match_details, "icebreaker")
            self.active = True
            
            # Send first message immediately
            initial_context = HumanMessage(content="Schreibe einen Icebreaker für das Match. Beziehe dich PRIMÄR auf ihre Bio wenn vorhanden sonst auf ihre Interessen. Sei humorvoll oder flirty. WICHTIG: Halte die Nachricht SEHR kurz (max. 1-2 Sätze). Verwende maximal 1 Emoji am Ende. Sei vorsichtig und teste den Schreibstil des Matches. VERBOTEN: Frage NIEMALS nach einem Treffen am selben Tag oder nach schnellen Treffen. SCHREIBSTIL: Wie ein junger Erwachsener - kurz, natürlich, ohne Bindestriche, Aufzählungen oder Plus-Zeichen. Sei locker und authentisch.")
            self.chat_history.add_user_message(initial_context)
            
            response = self.chain.invoke({"messages": self.chat_history.messages})
            self.chat_history.add_ai_message(response)
            self.bot_message_count += 1
            
            # Remove emojis for console logging
            clean_response = response.content.encode('ascii', 'ignore').decode('ascii')
            print(f"Chat started with {self.match_name}! \nBot: {clean_response}")
            
            # Send message immediately for first message
            self.parse_and_send_response(response.content, match_id, debug)
            
            # Note: update_last_bot_message_time is now handled by parse_and_send_response
        else:
            # Debug mode - similar logic but no actual sending
            self.match_id = match_id
            self.match_name = match_info.get('name', 'Unknown') if match_info else 'Unknown'
            self.match_info = match_info
            self.bot_message_count = 0
            
            match_details = self.format_match_infos(match_info) if match_info else ""
            self.setup_prompt_template(match_details, "icebreaker")
            self.active = True
            
            initial_context = HumanMessage(content="Schreibe einen Icebreaker für das Match. Sei humorvoll oder flirty basierend auf dem Match-Profil.")
            self.chat_history.add_user_message(initial_context)
            
            response = self.chain.invoke({"messages": self.chat_history.messages})
            self.chat_history.add_ai_message(response)
            self.bot_message_count += 1
            
            # Remove emojis for console logging
            clean_response = response.content.encode('ascii', 'ignore').decode('ascii')
            print("Bot: " + clean_response)

    def handle_message(self, message, debug=False, first_startup=False):
        """Handle incoming message from match"""
        if not self.active:
            print("Chat is not active.")
            return

        # ANTI-DUPLICATION: Check if we're already processing a message
        if hasattr(self, '_processing_message') and self._processing_message:
            print(f"ANTI-DUPLICATION: Already processing message for {self.match_name}, skipping")
            return
        
        # ANTI-DUPLICATION: Set processing flag
        self._processing_message = True
        
        try:
            # Note: We don't update last_match_message_time here anymore
            # Instead, we use last_bot_message_time to track when we last sent a message
            
            message_content = message["message"] if not debug else message
            user_message = HumanMessage(content=message_content)
            self.chat_history.add_user_message(user_message)
            
            # NEW FEATURE: Check if we have a scheduled response and cancel it
            if self.match_id and self.match_id in self.response_timer.scheduled_responses:
                print(f"NEW MESSAGE DETECTED - Cancelling scheduled response for {self.match_name}")
                print(f"   New message: {message_content[:50]}...")
                
                # Cancel the scheduled response
                cancelled_response = self.response_timer.scheduled_responses.pop(self.match_id)
                print(f"   Cancelled response that was scheduled for: {time.strftime('%H:%M:%S', time.localtime(cancelled_response['response_time']))}")
                print(f"   Cancelled message: {cancelled_response['message_content'][:50]}...")
                
                # Add a note to the conversation history about the cancellation
                cancellation_note = f"[SYSTEM: Previous response cancelled due to new message from match - will generate new response considering all recent messages]"
                system_message = HumanMessage(content=cancellation_note)
                self.chat_history.add_user_message(system_message)
                
                print(f"   Will generate new response considering all recent messages")

            # Analyze match message for dynamic adaptation
            if self.dynamics:
                # Analyze match message
                match_analysis = self.dynamics.analyze_match_message(message_content)
                self.dynamics.update_match_style(match_analysis)
                
                # Store message analysis in conversation history for style tracking
                self.dynamics.conversation_history.append({
                    'sender': 'match',
                    'content': message_content,
                    'timestamp': time.time(),
                    'emoji_count': match_analysis.get('emoji_count', 0),
                    'word_count': match_analysis.get('word_count', 0),
                    'question_count': match_analysis.get('question_count', 0),
                    'emoji_style': match_analysis.get('emoji_style', 'low'),
                    'length_style': match_analysis.get('length_style', 'medium'),
                    'writing_style': match_analysis.get('writing_style', 'balanced')
                })
                
                # Detect topic
                topic = self.dynamics.detect_topic(message_content)
                self.dynamics.current_topic = topic
                
                # Log style analysis
                print(f"STIL-ANALYSE für {self.match_name}:")
                print(f"   Wörter: {match_analysis.get('word_count', 0)}")
                print(f"   Emojis: {match_analysis.get('emoji_count', 0)} ({match_analysis.get('emoji_style', 'low')})")
                print(f"   Fragen: {match_analysis.get('question_count', 0)}")
                print(f"   Länge: {match_analysis.get('length_style', 'medium')}")
                print(f"   Stil: {match_analysis.get('writing_style', 'balanced')}")
                print(f"   Thema: {topic}")
                
                print(f"Match style: {match_analysis['communication_style']}, Topic: {topic}")

            # Determine current phase based on message count
            total_messages = len(self.chat_history.messages)
            current_phase, phase_config = self.phase_manager.get_current_phase(total_messages)
            
            print(f"Current phase: {current_phase} (Message {total_messages})")
            
            # Setup prompt for current phase
            match_details = self.format_match_infos(self.match_info) if self.match_info else ""
            self.setup_prompt_template(match_details, current_phase)

            try:
                response = self.chain.invoke({"messages": self.chat_history.messages})
                self.chat_history.add_ai_message(response)
                self.bot_message_count += 1
                
                # Post-process response with dynamic adjustments
                final_response = response.content
                if self.dynamics:
                    adjustments = self.dynamics.get_dynamic_prompt_adjustments(current_phase, topic)
                    final_response = self.dynamics.post_process_message(response.content, adjustments)
                    
                    # Log dynamic adjustments and style adaptation
                    print(f"DYNAMISCHE STIL-ANPASSUNG:")
                    print(f"   Emoji-Intensität: {adjustments['emoji_intensity']}")
                    print(f"   Fragen-Frequenz: {adjustments['question_frequency']:.1%}")
                    print(f"   Nachrichtenlänge: {adjustments['message_length']}")
                    print(f"   Schreibstil: {adjustments.get('writing_style', 'balanced')}")
                    print(f"   Emoji-Stil: {adjustments.get('emoji_style', 'medium')}")
                    print(f"   Kommunikationsstil: {adjustments.get('communication_style', 'neutral')}")
                    
                    # Log the actual response length for verification
                    response_words = len(final_response.split())
                    print(f"   Tatsächliche Antwortlänge: {response_words} Wörter")
                    
                    # Verify if we're following the style instructions
                    if adjustments.get('message_length') == 'very_short' and response_words > 8:
                        print(f"   WARNUNG: Antwort ist zu lang für 'very_short' Stil!")
                    elif adjustments.get('message_length') == 'short' and response_words > 15:
                        print(f"   WARNUNG: Antwort ist zu lang für 'short' Stil!")
                
                # Remove emojis for console logging
                clean_response = final_response.encode('ascii', 'ignore').decode('ascii')
                print(f"Bot: {clean_response}")

                if not debug:
                    # Check if this is first startup - if so, send immediately
                    if first_startup:
                        print(f"\nFIRST STARTUP MODE - sending response immediately (no delay)")
                        self.parse_and_send_response(final_response, message["match_id"], debug)
                        print(f"Response sent immediately due to first startup!")
                    else:
                        # Calculate response delay (normal behavior)
                        print(f"\nRESPONSE TIMING ANALYSIS for {self.match_name}:")
                        delay = self.calculate_response_delay()
                        
                        if delay > 0:
                            # Schedule delayed response
                            print(f"   Scheduling delayed response:")
                            print(f"   Delay: {delay:.1f} seconds")
                            print(f"   Will send at: {time.strftime('%H:%M:%S', time.localtime(time.time() + delay))}")
                            
                            # Use the new message splitting functionality
                            self.response_timer.schedule_response(
                                self.match_id, delay, final_response, self.api, self
                            )
                            
                            print(f"   Response scheduled successfully!")
                        else:
                            # Send immediately using the new message splitting functionality
                            print(f"   Sending response immediately (no delay)")
                            self.parse_and_send_response(final_response, message["match_id"], debug)
                            print(f"   Response sent immediately!")
                    
                    print(f"   Total response generation time: {time.time() - self.last_match_message_time:.1f}s")
                    print()
                        
            except Exception as e:
                print(f"Error generating response: {e}")
                
        except Exception as e:
            print(f"❌ Error in handle_message for {self.match_name}: {e}")
        finally:
            # ANTI-DUPLICATION: Clear processing flag
            self._processing_message = False

    def _load_match_instructions(self):
        """Load match instructions from persistent storage"""
        try:
            instructions_file = "match_instructions.json"
            if os.path.exists(instructions_file):
                with open(instructions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Could not load match instructions: {e}")
            return {}
    
    def get_match_instruction(self, match_name):
        """Get custom instruction for a specific match"""
        try:
            if self.match_instructions and match_name in self.match_instructions:
                data = self.match_instructions[match_name]
                if data.get('active', True):
                    return data.get('instruction', '')
            return None
        except Exception as e:
            print(f"Error getting match instruction: {e}")
            return None
    
    def apply_match_instruction_to_prompt(self, base_prompt, match_name):
        """Apply custom match instruction to the prompt if available"""
        instruction = self.get_match_instruction(match_name)
        if instruction:
            enhanced_prompt = f"{base_prompt}\n\nCUSTOM INSTRUCTION FOR {match_name.upper()}: {instruction}\n\nWICHTIG: Berücksichtige diese spezielle Anweisung bei deiner Antwort."
            return enhanced_prompt
        return base_prompt
    
    def generate_style_instructions(self, adjustments: Dict) -> str:
        """Generate detailed style instructions based on dynamic adjustments"""
        instructions = []
        
        # Message length instructions
        msg_length = adjustments.get('message_length', 'medium')
        if msg_length == 'very_short':
            instructions.append("📝 NACHRICHTENLÄNGE: SEHR KURZ (max. 3-5 Wörter, wie das Match schreibt)")
        elif msg_length == 'short':
            instructions.append("📝 NACHRICHTENLÄNGE: KURZ (max. 8-12 Wörter, ähnlich wie das Match)")
        elif msg_length == 'medium':
            instructions.append("📝 NACHRICHTENLÄNGE: MITTEL (12-20 Wörter, ausgewogen)")
        else:
            instructions.append("📝 NACHRICHTENLÄNGE: LANG (20+ Wörter, detailliert)")
        
        # Emoji style instructions
        emoji_style = adjustments.get('emoji_style', 'medium')
        if emoji_style == 'high':
            instructions.append("😊 EMOJI-STIL: VIELE EMOJIS (2-3 pro Nachricht, wie das Match)")
        elif emoji_style == 'medium':
            instructions.append("😊 EMOJI-STIL: WENIGE EMOJIS (1-2 pro Nachricht, moderat)")
        else:
            instructions.append("😊 EMOJI-STIL: KEINE EMOJIS (nur Text, wie das Match)")
        
        # Writing style instructions
        writing_style = adjustments.get('writing_style', 'balanced')
        if writing_style == 'very_concise':
            instructions.append("✍️ SCHREIBSTIL: SEHR KONZIS (kurze, prägnante Sätze)")
        elif writing_style == 'emoji_heavy_short':
            instructions.append("✍️ SCHREIBSTIL: KURZ + EMOJIS (wenige Wörter, viele Emojis)")
        elif writing_style == 'detailed_elaborate':
            instructions.append("✍️ SCHREIBSTIL: DETAILLIERT (ausführliche Erklärungen)")
        else:
            instructions.append("✍️ SCHREIBSTIL: AUSGEWOGEN (normale Länge, gemischter Stil)")
        
        # Question frequency
        question_freq = adjustments.get('question_frequency', 0.5)
        if question_freq > 0.7:
            instructions.append("❓ FRAGEN: HÄUFIG (jede Nachricht eine Frage)")
        elif question_freq > 0.4:
            instructions.append("❓ FRAGEN: MODERAT (jede zweite Nachricht eine Frage)")
        else:
            instructions.append("❓ FRAGEN: WENIG (selten Fragen stellen)")
        
        # Communication style
        comm_style = adjustments.get('communication_style', 'neutral')
        if comm_style == 'flirty':
            instructions.append("💕 KOMMUNIKATION: FLIRTY (spielerisch, charmant)")
        elif comm_style == 'serious':
            instructions.append("💕 KOMMUNIKATION: ERNST (sachlich, respektvoll)")
        elif comm_style == 'casual':
            instructions.append("💕 KOMMUNIKATION: CASUAL (locker, entspannt)")
        else:
            instructions.append("💕 KOMMUNIKATION: AUSGEWOGEN (normale Mischung)")
        
        return "\n".join(instructions)

    def close_chat(self):
        """Close the chat and cleanup"""
        self.active = False
        self.chat_history = ChatMessageHistory()
        self.response_timer.stop()

    def update_last_bot_message_time(self):
        """Update the timestamp when we last sent a message to the match"""
        self.last_bot_message_time = time.time()
        print(f"Updated last bot message time: {time.strftime('%H:%M:%S', time.localtime(self.last_bot_message_time))}")

    def get_last_bot_message_time(self):
        """Get the timestamp when we last sent a message to the match"""
        return getattr(self, 'last_bot_message_time', None)
    
    def analyze_recent_messages(self):
        """Analyze recent messages to help with context-aware responses"""
        try:
            # Get the last 5 messages from the match (excluding our own messages)
            recent_messages = []
            match_messages = []
            
            for msg in self.chat_history.messages[-10:]:  # Check last 10 messages
                if hasattr(msg, 'type'):
                    if msg.type == 'human':
                        match_messages.append(msg.content)
                    elif msg.type == 'ai':
                        # Skip our own messages
                        continue
                else:
                    # Fallback for different message formats
                    if isinstance(msg, HumanMessage):
                        match_messages.append(msg.content)
                    elif isinstance(msg, AIMessage):
                        continue
            
            # Get the most recent match messages (up to 5)
            recent_messages = match_messages[-5:]
            
            if len(recent_messages) > 1:
                print(f"ANALYSE DER NEUESTEN NACHRICHTEN für {self.match_name}:")
                print(f"   Anzahl neuer Nachrichten: {len(recent_messages)}")
                
                # Check if there are multiple recent messages
                if len(recent_messages) >= 2:
                    print(f"   Mehrere Nachrichten erkannt - wird alle berücksichtigen")
                    
                    # Create a summary for the LLM
                    recent_context = f"""
NEUESTE NACHRICHTEN VOM MATCH (chronologisch):
"""
                    for i, msg in enumerate(recent_messages, 1):
                        recent_context += f"{i}. {msg}\n"
                    
                    recent_context += f"""
WICHTIG: Das Match hat {len(recent_messages)} Nachrichten in kurzer Zeit gesendet. 
Berücksichtige ALLE diese Nachrichten in deiner Antwort und stelle sicher, 
dass du auf alle wichtigen Punkte eingehst.
"""
                    return recent_context
            
            return ""
            
        except Exception as e:
            print(f"⚠️  Error analyzing recent messages: {e}")
            return ""

    def parse_and_send_response(self, llm_response, match_id, debug=False):
        """Parse LLM response and send as one or two messages - transparent enhancement"""
        try:
            if "[SPLIT:2]" in llm_response:
                # Split into two messages
                messages = self.parse_split_response(llm_response)
                if len(messages) == 2:
                    print(f"Message splitting detected - sending as 2 separate messages")
                    self.send_split_messages(messages, match_id, debug)
                    return True
                else:
                    print(f"Split parsing failed, falling back to single message")
                    return self.send_single_message(llm_response, match_id, debug)
            else:
                # Send as single message (existing behavior)
                return self.send_single_message(llm_response, match_id, debug)
        except Exception as e:
            print(f"⚠️  Error in message splitting, falling back to single message: {e}")
            return self.send_single_message(llm_response, match_id, debug)

    def parse_split_response(self, response):
        """Parse [SPLIT:2] response into two messages"""
        try:
            parts = response.split("[SPLIT:2]")
            if len(parts) != 2:
                return [response]  # Fallback to single message
            
            messages_text = parts[1].strip()
            messages = messages_text.split("---")
            
            if len(messages) != 2:
                return [response]  # Fallback to single message
            
            # Clean up messages
            cleaned_messages = []
            for msg in messages:
                cleaned_msg = msg.strip()
                if cleaned_msg:  # Only add non-empty messages
                    cleaned_messages.append(cleaned_msg)
            
            # Validate that we have exactly 2 valid messages
            if len(cleaned_messages) == 2:
                return cleaned_messages
            else:
                return [response]  # Fallback to single message
                
        except Exception as e:
            print(f"⚠️  Error parsing split response: {e}")
            return [response]  # Fallback to single message

    def send_split_messages(self, messages, match_id, debug=False):
        """Send two messages with a short delay between them"""
        if debug:
            print(f"DEBUG: Would send split messages:")
            for i, msg in enumerate(messages, 1):
                print(f"   {i}. {msg}")
            return True
        
        try:
            # Send first message
            print(f"Sending first split message...")
            self.api.send_message(match_id, messages[0])
            
            # Short delay between messages (1-3 seconds)
            import time
            delay = random.uniform(1, 3)
            print(f"Waiting {delay:.1f} seconds before second message...")
            time.sleep(delay)
            
            # Send second message
            print(f"Sending second split message...")
            self.api.send_message(match_id, messages[1])
            
            # Update the time when we last sent a message (after the second message)
            self.update_last_bot_message_time()
            
            print(f"Both split messages sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error sending split messages: {e}")
            return False

    def send_single_message(self, message, match_id, debug=False):
        """Send a single message (existing behavior)"""
        if debug:
            print(f"DEBUG: Would send single message: {message}")
            return True
        
        try:
            self.api.send_message(match_id, message)
            # Update the time when we last sent a message
            self.update_last_bot_message_time()
            return True
        except Exception as e:
            print(f"Error sending single message: {e}")
            return False

class DateSimulation:
    def __init__(self, api):
        self.chats = {}
        self.api = api

    def match(self, user_id, match_info):
        if user_id not in self.chats:
            self.chats[user_id] = ChatManager(self.api)
            self.chats[user_id].start_chat(user_id, match_info, debug=True)
        else:
            print(f"Chat with {user_id} is already active.")

    def response(self, user_id, message):
        if user_id in self.chats:
            self.chats[user_id].handle_message(message, debug=True)
        else:
            print(f"No active chat with {user_id}.")

    def end_chat(self, user_id):
        if user_id in self.chats:
            self.chats[user_id].close_chat()
            print(f"Chat with {user_id} has been closed.")
        else:
            print(f"No active chat with {user_id} to close.")

    def start_simulation(self):
        simulation = DateSimulation(api=None)
        while True:
            command = input("Debug command: ").strip().split(maxsplit=2)
            if len(command) < 2:
                print("Invalid command or format. Please provide at least one argument.")
                continue

            action, user_id = command[0], command[1]
            match_info = None

            if action == "match":
                if len(command) > 2:
                    try:
                        match_info = json.loads(command[2])
                    except json.JSONDecodeError:
                        print("Invalid match info format, continuing without it.")
                simulation.match(user_id, match_info)
            elif action == "response" and len(command) > 2:
                simulation.response(user_id, command[2])
            else:
                print("Invalid command or format.")

if __name__ == "__main__":
    simulation = DateSimulation(api=None)
    simulation.start_simulation()