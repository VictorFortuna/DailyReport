#!/usr/bin/env python3
"""
Launcher script for Daily Report Bot
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run main
from bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())