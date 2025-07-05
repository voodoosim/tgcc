# attendance_bot/db.py
"""SQLite 데이터베이스 모델 및 함수 정의"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AttendanceDB:
    """출석체크 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "data/attendance.db"):
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """데이터베이스 테이블 초기화"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 출석 기록 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        nickname TEXT NOT NULL,
                        attendance_date DATE NOT NULL,
                        points_earned INTEGER DEFAULT 100,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, attendance_date)
                    )
                ''')
                
                # 사용자 포인트 테이블
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_points (
                        user_id INTEGER PRIMARY KEY,
                        nickname TEXT NOT NULL,
                        total_points INTEGER DEFAULT 0,
                        attendance_count INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("데이터베이스 테이블 초기화 완료")
                
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise

    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"데이터베이스 연결 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def check_attendance_today(self, user_id: int, date_str: str) -> bool:
        """
        오늘 출석체크 여부 확인

        Args:
            user_id: 사용자 ID
            date_str: 날짜 문자열 (YYYY-MM-DD)

        Returns:
            출석체크 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM attendance WHERE user_id = ? AND attendance_date = ?",
                    (user_id, date_str)
                )
                result = cursor.fetchone()
                return result is not None
                
        except sqlite3.Error as e:
            logger.error(f"출석체크 확인 실패: {e}")
            return False

    def record_attendance(self, user_id: int, nickname: str, date_str: str, points: int = 100) -> bool:
        """
        출석체크 기록

        Args:
            user_id: 사용자 ID
            nickname: 사용자 닉네임
            date_str: 날짜 문자열 (YYYY-MM-DD)
            points: 지급할 포인트

        Returns:
            기록 성공 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 출석 기록 추가
                cursor.execute('''
                    INSERT INTO attendance (user_id, nickname, attendance_date, points_earned)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, nickname, date_str, points))
                
                # 사용자 포인트 업데이트
                cursor.execute('''
                    INSERT OR REPLACE INTO user_points (user_id, nickname, total_points, attendance_count, last_updated)
                    VALUES (?, ?, 
                        COALESCE((SELECT total_points FROM user_points WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT attendance_count FROM user_points WHERE user_id = ?), 0) + 1,
                        CURRENT_TIMESTAMP)
                ''', (user_id, nickname, user_id, points, user_id))
                
                conn.commit()
                logger.info(f"출석체크 기록 완료 - 사용자: {user_id}, 날짜: {date_str}, 포인트: {points}")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"중복 출석체크 시도 - 사용자: {user_id}, 날짜: {date_str}")
            return False
        except sqlite3.Error as e:
            logger.error(f"출석체크 기록 실패: {e}")
            return False

    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        사용자 통계 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 통계 딕셔너리 또는 None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM user_points WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except sqlite3.Error as e:
            logger.error(f"사용자 통계 조회 실패: {e}")
            return None

    def get_attendance_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        출석 기록 조회

        Args:
            user_id: 사용자 ID
            limit: 조회할 기록 수

        Returns:
            출석 기록 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT attendance_date, points_earned, created_at
                    FROM attendance
                    WHERE user_id = ?
                    ORDER BY attendance_date DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except sqlite3.Error as e:
            logger.error(f"출석 기록 조회 실패: {e}")
            return []

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        포인트 순위 조회

        Args:
            limit: 조회할 순위 수

        Returns:
            순위 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, nickname, total_points, attendance_count
                    FROM user_points
                    ORDER BY total_points DESC, attendance_count DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except sqlite3.Error as e:
            logger.error(f"리더보드 조회 실패: {e}")
            return []