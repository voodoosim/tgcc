# attendance_bot/__init__.py
"""Telegram attendance check bot package"""

__version__ = "1.0.0"
__author__ = "Veronica Project"
__description__ = "Telegram bot for daily attendance tracking with points system"

from .db import AttendanceDB
from .utils import get_korean_time, get_korean_date_string
from .handlers import AttendanceHandlers, setup_handlers
from .main import AttendanceBot

__all__ = [
    "AttendanceDB",
    "AttendanceHandlers", 
    "AttendanceBot",
    "setup_handlers",
    "get_korean_time",
    "get_korean_date_string"
]