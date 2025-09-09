"""
Configuration management for TinderGPT
Load and manage configuration files
"""

import json
import os
from pathlib import Path

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_version():
    """Load version information from version.json"""
    version_path = Path(__file__).parent / "version.json"
    
    if not version_path.exists():
        return {"version": "1.0.0", "last_update": "unknown"}
    
    with open(version_path, 'r') as f:
        return json.load(f)

# Load configuration
try:
    config = load_config()
    version_info = load_version()
except Exception as e:
    print(f"Warning: Could not load configuration: {e}")
    config = {}
    version_info = {"version": "1.0.0"}

__all__ = ['config', 'version_info', 'load_config', 'load_version']
