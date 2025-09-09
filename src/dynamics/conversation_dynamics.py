#!/usr/bin/env python3
"""
Dynamic Conversation System for TinderBot
Adapts to match style and controls message dynamics
"""

import re
import random
import json
from typing import Dict, List, Tuple, Optional

class ConversationDynamics:
    def __init__(self, config):
        self.config = config
        self.match_style = {
            'emoji_usage': 'medium',  # low, medium, high
            'message_length': 'medium',  # short, medium, long
            'question_frequency': 'medium',  # low, medium, high
            'response_speed': 'medium',  # slow, medium, fast
            'communication_style': 'neutral'  # formal, casual, flirty, serious
        }
        self.conversation_history = []
        self.current_topic = None
        self.phase_adjustments = self.load_phase_adjustments()
        
    def load_phase_adjustments(self):
        """Load phase-specific adjustments"""
        return {
            'icebreaker': {
                'emoji_boost': 0.5,  # Much more conservative with emojis
                'question_frequency': 0.6,  # Fewer questions initially
                'message_length': 'very_short',  # Very short messages
                'style_adaptation': 0.1  # Minimal adaptation in early phase
            },
            'interests': {
                'emoji_boost': 1.0,
                'question_frequency': 0.6,
                'message_length': 'medium',
                'style_adaptation': 0.6
            },
            'compatibility': {
                'emoji_boost': 0.8,
                'question_frequency': 0.4,
                'message_length': 'medium',
                'style_adaptation': 0.8
            },
            'date_planning': {
                'emoji_boost': 0.6,
                'question_frequency': 0.2,
                'message_length': 'long',
                'style_adaptation': 0.9
            }
        }
    
    def analyze_match_message(self, message: str) -> Dict:
        """Analyze match message to understand their style"""
        # Count words and characters
        words = message.split()
        word_count = len(words)
        
        analysis = {
            'emoji_count': len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', message)),
            'message_length': len(message),
            'word_count': word_count,
            'has_question': '?' in message,
            'question_count': message.count('?'),
            'exclamation_count': message.count('!'),
            'capitalization_ratio': sum(1 for c in message if c.isupper()) / len(message) if message else 0,
            'emoji_ratio': len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', message)) / len(message) if message else 0,
            'avg_word_length': sum(len(word) for word in words) / word_count if word_count > 0 else 0,
            'sentence_count': len([s for s in message.split('.') if s.strip()]),
            'uses_ellipsis': '...' in message,
            'uses_abbreviations': any(word in message.lower() for word in ['lol', 'omg', 'wtf', 'btw', 'imo', 'tbh']),
            'punctuation_style': self.analyze_punctuation_style(message)
        }
        
        # Determine style characteristics
        analysis['emoji_style'] = self.categorize_emoji_usage(analysis['emoji_ratio'])
        analysis['length_style'] = self.categorize_message_length(analysis['word_count'])
        analysis['question_style'] = self.categorize_question_usage(analysis['question_count'])
        analysis['communication_style'] = self.categorize_communication_style(analysis)
        analysis['writing_style'] = self.categorize_writing_style(analysis)
        
        return analysis
    
    def categorize_emoji_usage(self, emoji_ratio: float) -> str:
        """Categorize emoji usage level"""
        if emoji_ratio > 0.12:
            return 'high'
        elif emoji_ratio > 0.03:
            return 'medium'
        else:
            return 'low'
    
    def categorize_message_length(self, word_count: int) -> str:
        """Categorize message length by word count"""
        if word_count > 20:
            return 'long'
        elif word_count > 8:
            return 'medium'
        elif word_count > 3:
            return 'short'
        else:
            return 'very_short'
    
    def analyze_punctuation_style(self, message: str) -> Dict:
        """Analyze punctuation style"""
        return {
            'uses_ellipsis': '...' in message,
            'uses_dashes': '-' in message,
            'uses_parentheses': '(' in message or ')' in message,
            'uses_quotes': '"' in message or "'" in message,
            'punctuation_density': sum(1 for c in message if c in '.,!?;:') / len(message) if message else 0
        }
    
    def categorize_writing_style(self, analysis: Dict) -> str:
        """Categorize overall writing style"""
        if analysis['uses_abbreviations'] and analysis['avg_word_length'] < 4:
            return 'casual_abbreviated'
        elif analysis['emoji_count'] > 2 and analysis['word_count'] < 10:
            return 'emoji_heavy_short'
        elif analysis['word_count'] < 5 and analysis['emoji_count'] == 0:
            return 'very_concise'
        elif analysis['word_count'] > 15 and analysis['sentence_count'] > 2:
            return 'detailed_elaborate'
        elif analysis['question_count'] > 1:
            return 'inquisitive'
        else:
            return 'balanced'
    
    def categorize_question_usage(self, question_count: int) -> str:
        """Categorize question usage"""
        if question_count > 2:
            return 'high'
        elif question_count > 0:
            return 'medium'
        else:
            return 'low'
    
    def categorize_communication_style(self, analysis: Dict) -> str:
        """Categorize overall communication style"""
        # Determine style based on multiple factors
        if analysis['exclamation_count'] > 1 and analysis['emoji_ratio'] > 0.1:
            return 'flirty'
        elif analysis['capitalization_ratio'] > 0.3:
            return 'energetic'
        elif analysis['message_length'] > 100 and analysis['question_count'] > 1:
            return 'serious'
        elif analysis['emoji_ratio'] < 0.02 and analysis['message_length'] < 30:
            return 'formal'
        else:
            return 'casual'
    
    def update_match_style(self, message_analysis: Dict):
        """Update match style based on recent message analysis"""
        # Update with weighted average (newer messages have more weight)
        weight = 0.7
        
        self.match_style['emoji_usage'] = self.blend_styles(
            self.match_style['emoji_usage'], 
            message_analysis['emoji_style'], 
            weight
        )
        
        self.match_style['message_length'] = self.blend_styles(
            self.match_style['message_length'], 
            message_analysis['length_style'], 
            weight
        )
        
        self.match_style['question_frequency'] = self.blend_styles(
            self.match_style['question_frequency'], 
            message_analysis['question_style'], 
            weight
        )
        
        self.match_style['communication_style'] = message_analysis['communication_style']
        
        # Store analysis in history
        self.conversation_history.append(message_analysis)
        
        # Keep only last 10 messages for analysis
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
    
    def blend_styles(self, current: str, new: str, weight: float) -> str:
        """Blend two style categories with given weight"""
        # Handle different style categories
        if current in ['low', 'medium', 'high'] and new in ['low', 'medium', 'high']:
            styles = ['low', 'medium', 'high']
            current_idx = styles.index(current)
            new_idx = styles.index(new)
            
            # Weighted blend
            blended_idx = int(current_idx * (1 - weight) + new_idx * weight)
            return styles[max(0, min(blended_idx, len(styles) - 1))]
        elif current in ['short', 'medium', 'long'] and new in ['short', 'medium', 'long']:
            styles = ['short', 'medium', 'long']
            current_idx = styles.index(current)
            new_idx = styles.index(new)
            
            # Weighted blend
            blended_idx = int(current_idx * (1 - weight) + new_idx * weight)
            return styles[max(0, min(blended_idx, len(styles) - 1))]
        else:
            # If categories don't match, return the new style
            return new
    
    def get_dynamic_prompt_adjustments(self, phase: str, topic: str = None) -> Dict:
        """Get dynamic prompt adjustments based on current context"""
        phase_config = self.phase_adjustments.get(phase, self.phase_adjustments['interests'])
        
        # Get current match style from conversation history
        current_style = self.get_current_match_style()
        
        # Base adjustments from phase
        adjustments = {
            'emoji_intensity': self.calculate_emoji_intensity(phase_config),
            'question_frequency': self.calculate_question_frequency(phase_config),
            'message_length': self.adapt_message_length(current_style, phase),
            'communication_style': self.calculate_communication_style(phase_config),
            'emoji_style': self.adapt_emoji_style(current_style),
            'writing_style': self.adapt_writing_style(current_style),
            'topic_adjustments': self.get_topic_adjustments(topic)
        }
        
        return adjustments
    
    def calculate_emoji_intensity(self, phase_config: Dict) -> str:
        """Calculate emoji intensity based on match style and phase"""
        match_emoji = self.match_style['emoji_usage']
        phase_boost = phase_config['emoji_boost']
        adaptation = phase_config['style_adaptation']
        
        # Blend match style with phase requirements
        if match_emoji == 'high':
            base_intensity = 0.8
        elif match_emoji == 'medium':
            base_intensity = 0.5
        else:
            base_intensity = 0.2
        
        # Apply phase boost
        adjusted_intensity = base_intensity * phase_boost
        
        # Apply adaptation weight
        final_intensity = base_intensity * (1 - adaptation) + adjusted_intensity * adaptation
        
        if final_intensity > 0.7:
            return 'high'
        elif final_intensity > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def calculate_question_frequency(self, phase_config: Dict) -> float:
        """Calculate question frequency based on match style and phase"""
        match_questions = self.match_style['question_frequency']
        phase_freq = phase_config['question_frequency']
        adaptation = phase_config['style_adaptation']
        
        # Convert match style to frequency
        if match_questions == 'high':
            match_freq = 0.8
        elif match_questions == 'medium':
            match_freq = 0.5
        else:
            match_freq = 0.2
        
        # Blend with phase requirements
        final_freq = match_freq * (1 - adaptation) + phase_freq * adaptation
        
        return min(0.9, max(0.1, final_freq))
    
    def get_current_match_style(self) -> Dict:
        """Get current match style from recent conversation history"""
        if not self.conversation_history:
            return self.match_style
        
        # Analyze last 3 messages from match
        recent_messages = [msg for msg in self.conversation_history[-3:] if msg.get('sender') == 'match']
        
        if not recent_messages:
            return self.match_style
        
        # Aggregate style from recent messages
        current_style = {
            'emoji_usage': 'low',
            'message_length': 'medium',
            'question_frequency': 'low',
            'writing_style': 'balanced'
        }
        
        total_emojis = sum(msg.get('emoji_count', 0) for msg in recent_messages)
        total_words = sum(msg.get('word_count', 0) for msg in recent_messages)
        total_questions = sum(msg.get('question_count', 0) for msg in recent_messages)
        
        # Determine current emoji usage
        if total_emojis > 2:
            current_style['emoji_usage'] = 'high'
        elif total_emojis > 0:
            current_style['emoji_usage'] = 'medium'
        
        # Determine current message length
        avg_words = total_words / len(recent_messages)
        if avg_words < 5:
            current_style['message_length'] = 'very_short'
        elif avg_words < 10:
            current_style['message_length'] = 'short'
        elif avg_words < 20:
            current_style['message_length'] = 'medium'
        else:
            current_style['message_length'] = 'long'
        
        # Determine question frequency
        if total_questions > 1:
            current_style['question_frequency'] = 'high'
        elif total_questions > 0:
            current_style['question_frequency'] = 'medium'
        
        return current_style
    
    def adapt_message_length(self, current_style: Dict, phase: str) -> str:
        """Adapt message length based on match's current style"""
        match_length = current_style.get('message_length', 'medium')
        
        # Strong adaptation to match's current style
        if match_length == 'very_short':
            return 'very_short'  # Match writes very short -> we write very short
        elif match_length == 'short':
            return 'short'  # Match writes short -> we write short
        elif match_length == 'medium':
            return 'medium'  # Match writes medium -> we write medium
        else:  # long
            return 'medium'  # Match writes long -> we write medium (don't overwhelm)
    
    def adapt_emoji_style(self, current_style: Dict) -> str:
        """Adapt emoji usage based on match's current style"""
        match_emoji = current_style.get('emoji_usage', 'low')
        
        # Strong adaptation to match's emoji style
        if match_emoji == 'high':
            return 'high'  # Match uses many emojis -> we use many emojis
        elif match_emoji == 'medium':
            return 'medium'  # Match uses some emojis -> we use some emojis
        else:
            return 'low'  # Match uses no/few emojis -> we use no/few emojis
    
    def adapt_writing_style(self, current_style: Dict) -> str:
        """Adapt writing style based on match's current style"""
        match_length = current_style.get('message_length', 'medium')
        match_emoji = current_style.get('emoji_usage', 'low')
        
        # Determine writing style based on current match behavior
        if match_length == 'very_short' and match_emoji == 'low':
            return 'very_concise'  # Match is very concise -> we are very concise
        elif match_length == 'short' and match_emoji == 'high':
            return 'emoji_heavy_short'  # Match uses short + emojis -> we do the same
        elif match_length == 'long' and match_emoji == 'low':
            return 'detailed_elaborate'  # Match is detailed -> we can be detailed
        else:
            return 'balanced'  # Default balanced style
    
    def calculate_message_length(self, phase_config: Dict) -> str:
        """Calculate target message length"""
        match_length = self.match_style['message_length']
        phase_length = phase_config['message_length']
        adaptation = phase_config['style_adaptation']
        
        # Blend match preference with phase requirements
        if random.random() < adaptation:
            return phase_length
        else:
            return match_length
    
    def calculate_communication_style(self, phase_config: Dict) -> str:
        """Calculate communication style"""
        match_style = self.match_style['communication_style']
        adaptation = phase_config['style_adaptation']
        
        # Sometimes adapt to phase, sometimes keep match style
        if random.random() < adaptation:
            # Phase-based style
            if phase_config['question_frequency'] > 0.6:
                return 'engaging'
            elif phase_config['emoji_boost'] > 1.0:
                return 'casual'
            else:
                return 'serious'
        else:
            return match_style
    
    def get_topic_adjustments(self, topic: str) -> Dict:
        """Get adjustments based on conversation topic"""
        topic_adjustments = {
            'flirty': {'emoji_boost': 1.5, 'question_frequency': 0.7, 'style': 'flirty'},
            'serious': {'emoji_boost': 0.3, 'question_frequency': 0.4, 'style': 'serious'},
            'humor': {'emoji_boost': 1.8, 'question_frequency': 0.6, 'style': 'casual'},
            'interests': {'emoji_boost': 0.8, 'question_frequency': 0.8, 'style': 'engaging'},
            'personal': {'emoji_boost': 0.5, 'question_frequency': 0.3, 'style': 'serious'},
            'plans': {'emoji_boost': 0.7, 'question_frequency': 0.5, 'style': 'practical'}
        }
        
        return topic_adjustments.get(topic, {'emoji_boost': 1.0, 'question_frequency': 0.5, 'style': 'neutral'})
    
    def should_ask_question(self, adjustments: Dict) -> bool:
        """Determine if this message should contain a question"""
        return random.random() < adjustments['question_frequency']
    
    def post_process_message(self, message: str, adjustments: Dict) -> str:
        """Post-process message to match dynamic requirements"""
        # Adjust emoji usage
        if 'emoji_intensity' in adjustments:
            message = self.adjust_emoji_usage(message, adjustments['emoji_intensity'])
        
        # Adjust message length if needed
        if 'message_length' in adjustments:
            message = self.adjust_message_length(message, adjustments['message_length'])
        
        # Ensure question if required
        if adjustments.get('force_question', False) and '?' not in message:
            message = self.add_question(message)
        
        return message
    
    def adjust_emoji_usage(self, message: str, intensity: str) -> str:
        """Adjust emoji usage in message"""
        current_emojis = re.findall(r'[😀-🙏🌀-🗿🚀-🛿]', message)
        current_ratio = len(current_emojis) / len(message) if message else 0
        
        target_ratios = {'low': 0.05, 'medium': 0.15, 'high': 0.25}
        target_ratio = target_ratios.get(intensity, 0.15)
        
        if current_ratio > target_ratio:
            # Remove some emojis
            emojis_to_remove = int(len(current_emojis) * (current_ratio - target_ratio) / current_ratio)
            for _ in range(emojis_to_remove):
                if current_emojis:
                    emoji_to_remove = random.choice(current_emojis)
                    message = message.replace(emoji_to_remove, '', 1)
                    current_emojis.remove(emoji_to_remove)
        
        return message
    
    def adjust_message_length(self, message: str, target_length: str) -> str:
        """Adjust message length"""
        current_length = len(message)
        
        length_targets = {'short': 50, 'medium': 100, 'long': 200}
        target = length_targets.get(target_length, 100)
        
        if current_length > target * 1.5:
            # Message too long, try to shorten
            sentences = message.split('. ')
            if len(sentences) > 1:
                # Remove last sentence if it's not essential
                message = '. '.join(sentences[:-1]) + '.'
        
        return message
    
    def add_question(self, message: str) -> str:
        """Add a question to the message if needed"""
        question_templates = [
            " Was denkst du?",
            " Wie siehst du das?",
            " Was meinst du dazu?",
            " Interessiert dich das?",
            " Wie ist deine Meinung?"
        ]
        
        return message + random.choice(question_templates)
    
    def detect_topic(self, message: str) -> str:
        """Detect conversation topic from message"""
        message_lower = message.lower()
        
        # Topic detection patterns
        topics = {
            'flirty': ['date', 'treffen', 'kennenlernen', 'flirty', 'attraktiv', 'schön'],
            'serious': ['beziehung', 'ernst', 'zukunft', 'plan', 'ziel'],
            'humor': ['witz', 'lustig', 'spaß', 'humor', 'lachen'],
            'interests': ['hobby', 'interesse', 'sport', 'musik', 'film', 'buch'],
            'personal': ['familie', 'beruf', 'leben', 'erfahrung', 'traum'],
            'plans': ['wochenende', 'plan', 'zeit', 'termin', 'verabredung']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return 'neutral'
    
    def get_style_summary(self) -> Dict:
        """Get summary of current match style"""
        return {
            'current_style': self.match_style.copy(),
            'conversation_history_length': len(self.conversation_history),
            'average_emoji_usage': self.calculate_average_emoji_usage(),
            'average_message_length': self.calculate_average_message_length(),
            'question_frequency': self.calculate_actual_question_frequency()
        }
    
    def calculate_average_emoji_usage(self) -> float:
        """Calculate average emoji usage from history"""
        if not self.conversation_history:
            return 0.0
        
        total_ratio = sum(msg['emoji_ratio'] for msg in self.conversation_history)
        return total_ratio / len(self.conversation_history)
    
    def calculate_average_message_length(self) -> float:
        """Calculate average message length from history"""
        if not self.conversation_history:
            return 0.0
        
        total_length = sum(msg['message_length'] for msg in self.conversation_history)
        return total_length / len(self.conversation_history)
    
    def calculate_actual_question_frequency(self) -> float:
        """Calculate actual question frequency from history"""
        if not self.conversation_history:
            return 0.0
        
        questions = sum(1 for msg in self.conversation_history if msg['has_question'])
        return questions / len(self.conversation_history)
