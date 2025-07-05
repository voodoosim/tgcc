#!/usr/bin/env python3
# run_attendance_bot.py
"""Standalone script to run the attendance bot"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from attendance_bot.main import run_bot
    run_bot()