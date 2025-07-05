# attendance_bot/utils.py
"""시간 및 포인트 유틸리티 함수"""
import logging
from datetime import datetime
from typing import Tuple
import pytz

logger = logging.getLogger(__name__)

# 한국 시간대
KST = pytz.timezone('Asia/Seoul')


def get_korean_date() -> Tuple[datetime, str]:
    """
    한국 시간 기준 현재 날짜 반환

    Returns:
        (datetime 객체, 날짜 문자열) 튜플
    """
    try:
        # 한국 시간 기준 현재 시간
        korean_now = datetime.now(KST)
        date_str = korean_now.strftime('%Y-%m-%d')
        
        logger.debug(f"한국 시간 조회: {korean_now}, 날짜 문자열: {date_str}")
        return korean_now, date_str
        
    except Exception as e:
        logger.error(f"한국 시간 조회 실패: {e}")
        # 폴백으로 UTC 시간 사용
        utc_now = datetime.utcnow()
        date_str = utc_now.strftime('%Y-%m-%d')
        return utc_now, date_str


def get_korean_time_string() -> str:
    """
    한국 시간 기준 현재 시간 문자열 반환

    Returns:
        시간 문자열 (YYYY-MM-DD HH:MM:SS KST)
    """
    try:
        korean_now = datetime.now(KST)
        return korean_now.strftime('%Y-%m-%d %H:%M:%S KST')
    except Exception as e:
        logger.error(f"한국 시간 문자열 생성 실패: {e}")
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')


def calculate_points(base_points: int = 100, bonus_multiplier: float = 1.0) -> int:
    """
    포인트 계산

    Args:
        base_points: 기본 포인트
        bonus_multiplier: 보너스 배율

    Returns:
        계산된 포인트
    """
    try:
        calculated_points = int(base_points * bonus_multiplier)
        logger.debug(f"포인트 계산: {base_points} * {bonus_multiplier} = {calculated_points}")
        return calculated_points
    except Exception as e:
        logger.error(f"포인트 계산 실패: {e}")
        return base_points


def format_attendance_message(nickname: str, points: int, total_points: int, attendance_count: int) -> str:
    """
    출석체크 성공 메시지 포맷

    Args:
        nickname: 사용자 닉네임
        points: 획득한 포인트
        total_points: 총 포인트
        attendance_count: 총 출석 횟수

    Returns:
        포맷된 메시지
    """
    korean_time = get_korean_time_string()
    
    message = f"""
✅ **출석체크 완료!**

👤 **{nickname}**님
🎯 획득 포인트: **{points:,}P**
💰 총 포인트: **{total_points:,}P**
📅 출석 횟수: **{attendance_count}회**
🕐 시간: {korean_time}

계속해서 출석체크하여 더 많은 포인트를 모아보세요! 🚀
"""
    return message.strip()


def format_already_attended_message(nickname: str, total_points: int, attendance_count: int) -> str:
    """
    이미 출석체크한 경우 메시지 포맷

    Args:
        nickname: 사용자 닉네임
        total_points: 총 포인트
        attendance_count: 총 출석 횟수

    Returns:
        포맷된 메시지
    """
    korean_time = get_korean_time_string()
    
    message = f"""
⏰ **이미 출석체크를 완료했습니다!**

👤 **{nickname}**님
💰 현재 포인트: **{total_points:,}P**
📅 출석 횟수: **{attendance_count}회**
🕐 현재 시간: {korean_time}

내일 다시 출석체크해주세요! 😊
"""
    return message.strip()


def format_error_message(error_type: str = "general") -> str:
    """
    오류 메시지 포맷

    Args:
        error_type: 오류 유형

    Returns:
        포맷된 오류 메시지
    """
    error_messages = {
        "general": "⚠️ 출석체크 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        "database": "💾 데이터베이스 오류가 발생했습니다. 관리자에게 문의해주세요.",
        "network": "🌐 네트워크 오류가 발생했습니다. 연결을 확인하고 다시 시도해주세요.",
    }
    
    return error_messages.get(error_type, error_messages["general"])


def validate_user_data(user_id: int, nickname: str) -> bool:
    """
    사용자 데이터 유효성 검증

    Args:
        user_id: 사용자 ID
        nickname: 사용자 닉네임

    Returns:
        유효성 여부
    """
    try:
        # 사용자 ID 검증
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"유효하지 않은 사용자 ID: {user_id}")
            return False
            
        # 닉네임 검증
        if not nickname or not isinstance(nickname, str) or len(nickname.strip()) == 0:
            logger.warning(f"유효하지 않은 닉네임: {nickname}")
            return False
            
        # 닉네임 길이 제한 (최대 50자)
        if len(nickname.strip()) > 50:
            logger.warning(f"닉네임이 너무 깁니다: {len(nickname)} 글자")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"사용자 데이터 유효성 검증 실패: {e}")
        return False