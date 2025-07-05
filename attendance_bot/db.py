# attendance_bot/db.py
"""SQLite database models and functions for attendance tracking"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AttendanceDB:
    """Attendance database manager"""
    
    def __init__(self, db_path: str = "attendance.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.init_database()
        
    def init_database(self) -> None:
        """Create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create attendance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        nickname TEXT NOT NULL,
                        attendance_date DATE NOT NULL,
                        points INTEGER DEFAULT 100,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, attendance_date)
                    )
                """)
                
                # Create users table for additional info
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        nickname TEXT NOT NULL,
                        total_points INTEGER DEFAULT 0,
                        total_attendance INTEGER DEFAULT 0,
                        first_attendance DATE,
                        last_attendance DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def record_attendance(self, user_id: str, nickname: str, attendance_date: str, points: int = 100) -> bool:
        """
        Record user attendance for a specific date
        
        Args:
            user_id: Telegram user ID
            nickname: User's display name
            attendance_date: Date in YYYY-MM-DD format
            points: Points to award (default: 100)
            
        Returns:
            True if attendance was recorded, False if already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Try to insert attendance record
                cursor.execute("""
                    INSERT INTO attendance (user_id, nickname, attendance_date, points)
                    VALUES (?, ?, ?, ?)
                """, (user_id, nickname, attendance_date, points))
                
                # Update or insert user info
                cursor.execute("""
                    INSERT INTO users (user_id, nickname, total_points, total_attendance, first_attendance, last_attendance)
                    VALUES (?, ?, ?, 1, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        nickname = excluded.nickname,
                        total_points = total_points + excluded.total_points,
                        total_attendance = total_attendance + 1,
                        last_attendance = excluded.last_attendance,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, nickname, points, attendance_date, attendance_date))
                
                conn.commit()
                logger.info(f"Attendance recorded for user {user_id} on {attendance_date}")
                return True
                
        except sqlite3.IntegrityError:
            # User already attended today
            logger.info(f"User {user_id} already attended on {attendance_date}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Failed to record attendance: {e}")
            raise
    
    def check_attendance_today(self, user_id: str, date: str) -> bool:
        """
        Check if user already attended today
        
        Args:
            user_id: Telegram user ID
            date: Date in YYYY-MM-DD format
            
        Returns:
            True if user already attended, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM attendance 
                    WHERE user_id = ? AND attendance_date = ?
                """, (user_id, date))
                
                return cursor.fetchone() is not None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to check attendance: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user attendance statistics
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with user stats or None if user not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, nickname, total_points, total_attendance, 
                           first_attendance, last_attendance
                    FROM users WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "user_id": row[0],
                        "nickname": row[1],
                        "total_points": row[2],
                        "total_attendance": row[3],
                        "first_attendance": row[4],
                        "last_attendance": row[5]
                    }
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get user stats: {e}")
            return None
    
    def get_attendance_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's recent attendance history
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of records to return
            
        Returns:
            List of attendance records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT attendance_date, points, created_at
                    FROM attendance 
                    WHERE user_id = ?
                    ORDER BY attendance_date DESC
                    LIMIT ?
                """, (user_id, limit))
                
                return [
                    {
                        "date": row[0],
                        "points": row[1],
                        "created_at": row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get attendance history: {e}")
            return []
    
    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users by total points
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of top users
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT nickname, total_points, total_attendance
                    FROM users
                    ORDER BY total_points DESC, total_attendance DESC
                    LIMIT ?
                """, (limit,))
                
                return [
                    {
                        "nickname": row[0],
                        "total_points": row[1],
                        "total_attendance": row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get top users: {e}")
            return []
    
    def close(self) -> None:
        """Close database connections (for cleanup)"""
        # SQLite3 connections are auto-closed when using context manager
        pass