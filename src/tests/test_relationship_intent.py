#!/usr/bin/env python3
"""
Test script to demonstrate relationship_intent-based prompt adjustment
"""

import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_relationship_intent_prompts():
    """Test different relationship intents and their prompts"""
    
    # Load config
    try:
        with open('src/config/config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("Error: Could not find config.json")
            return
    
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
            "bio": "Suche nach einer echten Verbindung und gemeinsamer Zukunft",
            "interests": ["Lesen", "Kochen", "Familie"]
        },
        {
            "name": "Maria",
            "relationship_intent": "Offen für festes",
            "bio": "Mal sehen was passiert 😉",
            "interests": ["Sport", "Musik", "Reisen"]
        },
        {
            "name": "Sarah",
            "relationship_intent": "Weiß ich noch nicht",
            "bio": "Bin mir noch nicht sicher was ich suche",
            "interests": ["Kunst", "Natur", "Kaffee"]
        }
    ]
    
    print("Testing relationship_intent-based prompt adjustment:")
    print("=" * 60)
    
    relationship_prompts = config.get('relationship_intent_prompts', {})
    print(f"Available relationship prompts: {list(relationship_prompts.keys())}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']} - '{test_case['relationship_intent']}'")
        print("-" * 40)
        
        # Check if relationship intent prompt was found
        found_prompt = False
        
        for intent_key, prompt in relationship_prompts.items():
            if intent_key.lower() in test_case['relationship_intent'].lower() or test_case['relationship_intent'].lower() in intent_key.lower():
                print(f"✅ Relationship intent prompt found: '{intent_key}'")
                print(f"   Prompt: {prompt}")
                found_prompt = True
                break
        
        if not found_prompt:
            print(f"❌ No relationship intent prompt found for '{test_case['relationship_intent']}'")
        
        print()

def test_prompt_construction():
    """Test how the prompt would be constructed"""
    
    # Load config
    try:
        with open('src/config/config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("Error: Could not find config.json")
            return
    
    # Simulate prompt construction
    base_goals = config['goals_to_be_achieved']
    phase_name = "icebreaker"
    goal = config['conversation_phases']['icebreaker']['goal']
    match_details = "Name: Anna, Bio: Spaß haben, Interessen: Reisen, Beziehungsziel: Nichts ernstes"
    
    # Get relationship intent prompt
    relationship_intent = "Nichts ernstes"
    relationship_prompts = config.get('relationship_intent_prompts', {})
    relationship_prompt = ""
    
    for intent_key, prompt in relationship_prompts.items():
        if intent_key.lower() in relationship_intent.lower():
            relationship_prompt = f"\n\n{prompt}"
            break
    
    # Construct full prompt
    full_prompt = f"""
    {base_goals}
    
    AKTUELLE PHASE: {phase_name.upper()}
    PHASEN-ZIEL: {goal}
    
    MATCH-INFO: {match_details}
    """
    
    if relationship_prompt:
        full_prompt += relationship_prompt
    
    full_prompt += "\n\nWICHTIG: Halte deine Antworten kurz und prägnant. Stelle eine Frage um das Gespräch am Laufen zu halten."
    
    print("Example prompt construction:")
    print("=" * 60)
    print(full_prompt)

if __name__ == "__main__":
    test_relationship_intent_prompts()
    print("\n" + "=" * 60 + "\n")
    test_prompt_construction()
