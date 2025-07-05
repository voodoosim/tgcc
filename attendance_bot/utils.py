# attendance_bot/utils.py
"""Utility functions for time handling and points management"""
import logging
from datetime import datetime, timezone
import pytz
from typing import Optional

logger = logging.getLogger(__name__)

# Korean timezone
KST = pytz.timezone('Asia/Seoul')


def get_korean_time() -> datetime:
    """
    Get current time in Korean timezone (Asia/Seoul)
    
    Returns:
        Current datetime in Korean timezone
    """
    return datetime.now(KST)


def get_korean_date_string() -> str:
    """
    Get current date string in Korean timezone
    
    Returns:
        Date string in YYYY-MM-DD format
    """
    return get_korean_time().strftime("%Y-%m-%d")


def get_korean_datetime_string() -> str:
    """
    Get current datetime string in Korean timezone
    
    Returns:
        Datetime string in YYYY-MM-DD HH:MM:SS format
    """
    return get_korean_time().strftime("%Y-%m-%d %H:%M:%S")


def format_korean_time(dt: datetime) -> str:
    """
    Format datetime to Korean time string
    
    Args:
        dt: DateTime object to format
        
    Returns:
        Formatted datetime string
    """
    if dt.tzinfo is None:
        # If naive datetime, assume it's UTC and convert to KST
        dt = dt.replace(tzinfo=timezone.utc)
    
    korean_dt = dt.astimezone(KST)
    return korean_dt.strftime("%Y년 %m월 %d일 %H:%M:%S")


def is_same_day_korea(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes are on the same day in Korean timezone
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        
    Returns:
        True if same day in Korean timezone
    """
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)
    
    korean_dt1 = dt1.astimezone(KST)
    korean_dt2 = dt2.astimezone(KST)
    
    return korean_dt1.date() == korean_dt2.date()


def calculate_points(base_points: int = 100, bonus_multiplier: float = 1.0) -> int:
    """
    Calculate points to award for attendance
    
    Args:
        base_points: Base points for attendance
        bonus_multiplier: Bonus multiplier for special events
        
    Returns:
        Calculated points
    """
    return int(base_points * bonus_multiplier)


def get_streak_bonus(consecutive_days: int) -> float:
    """
    Calculate bonus multiplier based on consecutive attendance days
    
    Args:
        consecutive_days: Number of consecutive attendance days
        
    Returns:
        Bonus multiplier
    """
    if consecutive_days >= 30:
        return 2.0  # 100% bonus for 30+ days
    elif consecutive_days >= 14:
        return 1.5  # 50% bonus for 14+ days  
    elif consecutive_days >= 7:
        return 1.2  # 20% bonus for 7+ days
    else:
        return 1.0  # No bonus


def format_points(points: int) -> str:
    """
    Format points with nice display
    
    Args:
        points: Number of points
        
    Returns:
        Formatted points string
    """
    if points >= 1000:
        return f"{points:,}포인트"
    else:
        return f"{points}포인트"


def get_rank_emoji(rank: int) -> str:
    """
    Get emoji for rank position
    
    Args:
        rank: Rank position (1-based)
        
    Returns:
        Emoji string
    """
    rank_emojis = {
        1: "🥇",
        2: "🥈", 
        3: "🥉"
    }
    return rank_emojis.get(rank, f"{rank}위")


def format_attendance_message(nickname: str, points: int, total_points: int, total_attendance: int) -> str:
    """
    Format attendance success message
    
    Args:
        nickname: User's nickname
        points: Points awarded today
        total_points: User's total points
        total_attendance: User's total attendance count
        
    Returns:
        Formatted success message
    """
    return f"""✅ 출석체크 완료!

👤 닉네임: {nickname}
🎁 오늘 획득: {format_points(points)}
💰 총 포인트: {format_points(total_points)}
📅 총 출석: {total_attendance}일

오늘도 함께해주셔서 감사합니다! 🎉"""


def format_already_attended_message(nickname: str, total_points: int) -> str:
    """
    Format already attended message
    
    Args:
        nickname: User's nickname  
        total_points: User's total points
        
    Returns:
        Formatted already attended message
    """
    return f"""⚠️ 이미 출석체크를 완료했습니다!

👤 닉네임: {nickname}
💰 총 포인트: {format_points(total_points)}

내일 다시 출석체크해주세요! 😊"""


def format_stats_message(stats: dict) -> str:
    """
    Format user statistics message
    
    Args:
        stats: User statistics dictionary
        
    Returns:
        Formatted stats message
    """
    return f"""📊 {stats['nickname']}님의 출석 통계

💰 총 포인트: {format_points(stats['total_points'])}
📅 총 출석: {stats['total_attendance']}일
🗓️ 첫 출석: {stats['first_attendance']}
📆 최근 출석: {stats['last_attendance']}"""


def format_leaderboard_message(top_users: list) -> str:
    """
    Format leaderboard message
    
    Args:
        top_users: List of top user dictionaries
        
    Returns:
        Formatted leaderboard message
    """
    if not top_users:
        return "📊 아직 출석한 사용자가 없습니다."
    
    message = "🏆 출석 리더보드 (Top 10)\n\n"
    
    for i, user in enumerate(top_users, 1):
        rank_emoji = get_rank_emoji(i)
        message += f"{rank_emoji} {user['nickname']}\n"
        message += f"   💰 {format_points(user['total_points'])} | 📅 {user['total_attendance']}일\n\n"
    
    return message.strip()


def validate_nickname(nickname: Optional[str]) -> str:
    """
    Validate and sanitize nickname
    
    Args:
        nickname: Raw nickname from user
        
    Returns:
        Validated nickname
    """
    if not nickname or not nickname.strip():
        return "익명"
    
    # Limit length and sanitize
    sanitized = nickname.strip()[:50]
    return sanitized if sanitized else "익명"


def get_welcome_message() -> str:
    """
    Get welcome message for new users
    
    Returns:
        Welcome message
    """
    return """🎉 출석체크 봇에 오신 것을 환영합니다!

📝 사용법:
• /출첵 - 출석체크하기 (1일 1회, 100포인트)
• /통계 - 내 출석 통계 보기  
• /순위 - 출석 리더보드 보기

⏰ 출석체크는 한국시간(KST) 기준으로 매일 자정에 초기화됩니다.

지금 바로 /출첵 명령어로 출석체크를 시작해보세요! 🚀"""