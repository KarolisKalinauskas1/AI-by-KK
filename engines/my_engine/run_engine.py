#!/usr/bin/env python3
"""
UCI Engine Entry Point

This script is the executable that the lichess-bot starter launches.
It sets up the engine configuration and starts the UCI command loop.

Requirements:
- python-chess library installed
- Python >= 3.10
- config.yaml in the same directory

The script ensures unbuffered stdout for proper UCI communication.
"""

import sys
import os
import signal
from pathlib import Path

# Ensure unbuffered output for UCI protocol
sys.stdout.reconfigure(line_buffering=True)

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import uci

def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM gracefully by setting stop flag."""
    if hasattr(uci, 'stop_token') and uci.stop_token:
        uci.stop_token.set()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Path to config file
    config_path = current_dir / "config.yaml"
    
    # Start UCI loop
    uci.main(str(config_path))
