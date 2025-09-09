#!/usr/bin/env python3
"""
TinderGPT - Main Entry Point
AI-powered Tinder bot with dynamic conversation system
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for TinderGPT"""
    try:
        from src.core import BotController
        from src.config import config
        
        print("Starting TinderGPT...")
        print("=" * 50)
        
        # Initialize and start bot
        bot = BotController()
        bot.start_bot()
        
        # Keep the main thread alive
        try:
            while bot.bot_running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down TinderGPT...")
            bot.stop_bot()
        
    except KeyboardInterrupt:
        print("\nShutting down TinderGPT...")
    except Exception as e:
        print(f"Error starting TinderGPT: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
