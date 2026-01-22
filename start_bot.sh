#!/bin/bash
# PythonAnywhere startup script for DailyReport Bot

echo "Starting DailyReport Bot on PythonAnywhere..."
cd /home/$(whoami)/DailyReport

# Install dependencies
pip3.11 install --user -r requirements.txt

# Run the bot
python3.11 run_bot.py
