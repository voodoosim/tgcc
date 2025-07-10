"""
Base adapter module that defines the interface for database adapters.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class BaseAdapter(ABC):
    """
    Base adapter class that defines the interface for database adapters.
    All database adapters should inherit from this class and implement its methods.
    """

    def __init__(self, db_path: Union[str, Path]):
        """
        Initialize the base adapter with a database path.

        Args:
            db_path: Path to the database file
        """
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.connection = None

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the database.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement connect method")

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database connection.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement close method")

    @abstractmethod
    async def init_db(self) -> None:
        """
        Initialize the database schema.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement init_db method")

    def get_db_path(self) -> Path:
        """
        Get the database path.

        Returns:
            Path: The path to the database file
        """
        return self.db_path

    @abstractmethod
    async def add_attendance(self, user_id: int, username: str, date: datetime) -> bool:
        """
        Add attendance record for a user.

        Args:
            user_id: Telegram user ID
            username: User's nickname or username
            date: Date of attendance

        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement add_attendance method")

    @abstractmethod
    async def check_attendance(self, user_id: int, date: datetime) -> bool:
        """
        Check if a user has already checked in for the day.

        Args:
            user_id: Telegram user ID
            date: Date to check

        Returns:
            bool: True if user has checked in, False otherwise
        """
        raise NotImplementedError("Subclasses must implement check_attendance method")

    @abstractmethod
    async def add_points(self, user_id: int, points: int) -> int:
        """
        Add points to a user's account.

        Args:
            user_id: Telegram user ID
            points: Points to add

        Returns:
            int: New point balance
        """
        raise NotImplementedError("Subclasses must implement add_points method")

    @abstractmethod
    async def get_points(self, user_id: int) -> int:
        """
        Get a user's current point balance.

        Args:
            user_id: Telegram user ID

        Returns:
            int: Current point balance
        """
        raise NotImplementedError("Subclasses must implement get_points method")

    def get_username_or_default(self, username: Optional[str]) -> str:
        """
        Get username if not None, otherwise return a default value.

        Args:
            username: User's nickname or username, possibly None

        Returns:
            str: The username or a default value
        """
        return username if username is not None else "Unknown User"

    @abstractmethod
    async def get_attendance_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get attendance history for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            List[Dict[str, Any]]: List of attendance records
        """
        raise NotImplementedError("Subclasses must implement get_attendance_history method")

    @abstractmethod
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users by points.

        Args:
            limit: Number of users to return

        Returns:
            List[Dict[str, Any]]: List of users with their points
        """
        raise NotImplementedError("Subclasses must implement get_leaderboard method")
