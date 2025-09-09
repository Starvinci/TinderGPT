#!/usr/bin/env python3
"""
Demo for Dynamic Conversation System
Shows how the bot adapts to different match styles
"""

import json
import sys
import time

def load_config():
    """Load configuration"""
    try:
        with open("src/config/config.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return {}

def demo_dynamic_adaptation():
    """Demo the dynamic adaptation system"""
    print("=" * 60)
    print("DYNAMIC CONVERSATION SYSTEM DEMO")
    print("=" * 60)
    
    config = load_config()
    
    try:
        from ..dynamics import ConversationDynamics
        dynamics = ConversationDynamics(config)
        
        print("\n1. ANALYZING DIFFERENT MATCH STYLES")
        print("-" * 40)
        
        # Test different match styles
        match_styles = [
            {
                "name": "Emoji-Liebhaber",
                "messages": [
                    "Hey! 😊😄 Wie geht's?",
                    "Das ist super! 😂😁",
                    "Ich freue mich! 😊😄😁"
                ]
            },
            {
                "name": "Formeller Typ",
                "messages": [
                    "Guten Tag. Wie heißen Sie?",
                    "Das ist sehr interessant.",
                    "Vielen Dank für die Information."
                ]
            },
            {
                "name": "Flirty Person",
                "messages": [
                    "Hey Süßer! 😘",
                    "Du bist echt attraktiv! 😍",
                    "Lass uns mal treffen! 😊"
                ]
            },
            {
                "name": "Ernsthafter Typ",
                "messages": [
                    "Ich suche eine ernsthafte Beziehung.",
                    "Was sind deine Ziele für die Zukunft?",
                    "Familie ist mir sehr wichtig."
                ]
            }
        ]
        
        for style in match_styles:
            print(f"\n{style['name']}:")
            dynamics.match_style = {
                'emoji_usage': 'medium',
                'message_length': 'medium',
                'question_frequency': 'medium',
                'response_speed': 'medium',
                'communication_style': 'neutral'
            }
            
            for i, message in enumerate(style['messages']):
                analysis = dynamics.analyze_match_message(message)
                dynamics.update_match_style(analysis)
                
                print(f"  Nachricht {i+1}: '{message[:30]}...'")
                print(f"    -> Stil: {analysis['communication_style']}")
                print(f"    -> Emojis: {analysis['emoji_style']}")
                print(f"    -> Länge: {analysis['length_style']}")
            
            print(f"  Finaler Match-Stil: {dynamics.match_style['communication_style']}, "
                  f"Emojis: {dynamics.match_style['emoji_usage']}")
        
        print("\n2. DYNAMIC PROMPT ADJUSTMENTS")
        print("-" * 40)
        
        # Show how adjustments change based on phase and style
        phases = ['icebreaker', 'interests', 'compatibility', 'date_planning']
        
        for phase in phases:
            print(f"\n{phase.upper()} Phase:")
            
            # Test with different match styles
            for style_name, emoji_style in [("Emoji-Liebhaber", "high"), ("Formeller Typ", "low")]:
                dynamics.match_style['emoji_usage'] = emoji_style
                dynamics.match_style['communication_style'] = 'casual' if emoji_style == 'high' else 'formal'
                
                adjustments = dynamics.get_dynamic_prompt_adjustments(phase)
                
                print(f"  {style_name}:")
                print(f"    -> Emoji-Intensität: {adjustments['emoji_intensity']}")
                print(f"    -> Fragen-Häufigkeit: {adjustments['question_frequency']:.1%}")
                print(f"    -> Nachrichten-Länge: {adjustments['message_length']}")
                print(f"    -> Kommunikations-Stil: {adjustments['communication_style']}")
        
        print("\n3. TOPIC DETECTION")
        print("-" * 40)
        
        topics = [
            ("Lass uns mal treffen! 😊", "flirty"),
            ("Ich suche eine ernsthafte Beziehung", "serious"),
            ("Das war so lustig! 😂", "humor"),
            ("Ich liebe Sport und Musik", "interests"),
            ("Erzähl mir von deiner Familie", "personal"),
            ("Was machst du am Wochenende?", "plans")
        ]
        
        for message, expected_topic in topics:
            detected_topic = dynamics.detect_topic(message)
            status = "✓" if detected_topic == expected_topic else "✗"
            print(f"  {status} '{message[:30]}...' -> {detected_topic}")
        
        print("\n4. MESSAGE POST-PROCESSING")
        print("-" * 40)
        
        test_message = "Hey! 😊😄😁 Das ist super! 😂 Wie geht's? 😊"
        print(f"Original: {test_message}")
        
        # Test different emoji intensities
        for intensity in ['low', 'medium', 'high']:
            adjustments = {'emoji_intensity': intensity}
            processed = dynamics.post_process_message(test_message, adjustments)
            print(f"{intensity.capitalize()}: {processed}")
        
        print("\n5. QUESTION FREQUENCY ADAPTATION")
        print("-" * 40)
        
        # Show how question frequency adapts
        for phase in phases:
            print(f"\n{phase.upper()}:")
            
            for question_style in ['low', 'medium', 'high']:
                dynamics.match_style['question_frequency'] = question_style
                adjustments = dynamics.get_dynamic_prompt_adjustments(phase)
                
                print(f"  Match-Fragen-Stil: {question_style} -> "
                      f"Bot-Fragen-Häufigkeit: {adjustments['question_frequency']:.1%}")
        
        print("\n" + "=" * 60)
        print("DEMO ABGESCHLOSSEN")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"Demo failed: {e}")
        return False

def demo_conversation_simulation():
    """Simulate a conversation with dynamic adaptation"""
    print("\n" + "=" * 60)
    print("CONVERSATION SIMULATION")
    print("=" * 60)
    
    config = load_config()
    
    try:
        from ..dynamics import ConversationDynamics
        dynamics = ConversationDynamics(config)
        
        # Simulate a conversation
        conversation = [
            ("Match", "Hey! 😊 Wie geht's?"),
            ("Bot", "Hey! Mir geht's gut, danke! 😊 Wie ist dein Tag so?"),
            ("Match", "Ganz okay! 😄 Was machst du so?"),
            ("Bot", "Ich arbeite gerade an einem Projekt. 😊 Was beschäftigt dich?"),
            ("Match", "Ich studiere Informatik! 😁"),
            ("Bot", "Das ist super! 😊 Was interessiert dich daran am meisten?"),
            ("Match", "Programmierung und KI! 😄"),
            ("Bot", "Spannend! 😊 Ich arbeite auch viel mit Technologie."),
            ("Match", "Cool! 😁 Lass uns mal treffen!"),
            ("Bot", "Das klingt gut! 😊 Wann hättest du Zeit?")
        ]
        
        print("Simulierte Konversation mit dynamischer Anpassung:")
        print("-" * 50)
        
        for i, (speaker, message) in enumerate(conversation):
            if speaker == "Match":
                # Analyze match message
                analysis = dynamics.analyze_match_message(message)
                dynamics.update_match_style(analysis)
                
                # Detect topic
                topic = dynamics.detect_topic(message)
                dynamics.current_topic = topic
                
                print(f"\n{i+1}. {speaker}: {message}")
                print(f"   -> Stil: {analysis['communication_style']}, "
                      f"Emojis: {analysis['emoji_style']}, "
                      f"Thema: {topic}")
                
                # Show bot's dynamic adjustments
                phase = "icebreaker" if i < 3 else "interests" if i < 6 else "compatibility"
                adjustments = dynamics.get_dynamic_prompt_adjustments(phase, topic)
                
                print(f"   -> Bot-Anpassungen: Emoji={adjustments['emoji_intensity']}, "
                      f"Fragen={adjustments['question_frequency']:.1%}, "
                      f"Länge={adjustments['message_length']}")
                
            else:
                print(f"{i+1}. {speaker}: {message}")
        
        print(f"\nFinaler Match-Stil: {dynamics.match_style['communication_style']}")
        print(f"Emoji-Nutzung: {dynamics.match_style['emoji_usage']}")
        print(f"Fragen-Häufigkeit: {dynamics.match_style['question_frequency']}")
        
        return True
        
    except Exception as e:
        print(f"Conversation simulation failed: {e}")
        return False

def main():
    """Run the demo"""
    print("Starting Dynamic Conversation System Demo...")
    
    success1 = demo_dynamic_adaptation()
    success2 = demo_conversation_simulation()
    
    if success1 and success2:
        print("\nDemo erfolgreich abgeschlossen!")
        return True
    else:
        print("\nDemo fehlgeschlagen!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
