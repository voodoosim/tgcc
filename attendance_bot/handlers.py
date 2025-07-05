# attendance_bot/handlers.py
"""텔레그램 봇 명령어 핸들러 정의"""
import logging
from typing import Optional
from telegram import Update, User
from telegram.ext import ContextTypes

from .db import AttendanceDB
from .utils import (
    get_korean_date,
    calculate_points,
    format_attendance_message,
    format_already_attended_message,
    format_error_message,
    validate_user_data
)

logger = logging.getLogger(__name__)


class AttendanceHandlers:
    """출석체크 봇 핸들러 클래스"""

    def __init__(self, db: AttendanceDB):
        """
        핸들러 초기화

        Args:
            db: 출석체크 데이터베이스 인스턴스
        """
        self.db = db

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /start 명령어 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            user = update.effective_user
            if not user:
                return

            welcome_message = f"""
👋 **안녕하세요, {user.first_name}님!**

📋 **베로니카 출석체크 봇**에 오신 것을 환영합니다!

🎯 **사용법:**
• `/출첵` - 일일 출석체크 (100포인트 획득)
• `/내정보` - 내 포인트 및 출석 현황 조회
• `/순위` - 포인트 순위 조회
• `/도움말` - 명령어 도움말

⏰ **출석체크는 하루에 한 번만 가능합니다** (한국 시간 기준)

시작하려면 `/출첵` 명령어를 입력해보세요! 🚀
"""

            await update.message.reply_text(
                welcome_message.strip(),
                parse_mode='Markdown'
            )
            
            logger.info(f"사용자 {user.id}({user.first_name})가 봇을 시작했습니다")
            
        except Exception as e:
            logger.error(f"/start 명령어 처리 실패: {e}")
            await update.message.reply_text(
                format_error_message("general"),
                parse_mode='Markdown'
            )

    async def attendance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /출첵 명령어 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            user = update.effective_user
            if not user:
                return

            user_id = user.id
            nickname = self._get_user_nickname(user)
            
            # 사용자 데이터 유효성 검증
            if not validate_user_data(user_id, nickname):
                await update.message.reply_text(
                    format_error_message("general"),
                    parse_mode='Markdown'
                )
                return

            # 한국 시간 기준 오늘 날짜 가져오기
            korean_datetime, date_str = get_korean_date()

            # 이미 출석체크했는지 확인
            if self.db.check_attendance_today(user_id, date_str):
                # 사용자 통계 조회
                user_stats = self.db.get_user_stats(user_id)
                total_points = user_stats['total_points'] if user_stats else 0
                attendance_count = user_stats['attendance_count'] if user_stats else 0
                
                message = format_already_attended_message(nickname, total_points, attendance_count)
                await update.message.reply_text(message, parse_mode='Markdown')
                
                logger.info(f"사용자 {user_id}({nickname})의 중복 출석체크 시도")
                return

            # 포인트 계산
            points = calculate_points()

            # 출석체크 기록
            success = self.db.record_attendance(user_id, nickname, date_str, points)
            
            if success:
                # 업데이트된 사용자 통계 조회
                user_stats = self.db.get_user_stats(user_id)
                total_points = user_stats['total_points'] if user_stats else points
                attendance_count = user_stats['attendance_count'] if user_stats else 1
                
                message = format_attendance_message(nickname, points, total_points, attendance_count)
                await update.message.reply_text(message, parse_mode='Markdown')
                
                logger.info(f"사용자 {user_id}({nickname})의 출석체크 완료 - 포인트: {points}")
                
            else:
                await update.message.reply_text(
                    format_error_message("database"),
                    parse_mode='Markdown'
                )
                logger.error(f"사용자 {user_id}({nickname})의 출석체크 기록 실패")

        except Exception as e:
            logger.error(f"/출첵 명령어 처리 실패: {e}")
            await update.message.reply_text(
                format_error_message("general"),
                parse_mode='Markdown'
            )

    async def my_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /내정보 명령어 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            user = update.effective_user
            if not user:
                return

            user_id = user.id
            nickname = self._get_user_nickname(user)

            # 사용자 통계 조회
            user_stats = self.db.get_user_stats(user_id)
            
            if not user_stats:
                message = f"""
ℹ️ **{nickname}**님의 정보

아직 출석체크를 하지 않으셨습니다.
`/출첵` 명령어로 첫 출석체크를 해보세요! 🎯
"""
            else:
                # 최근 출석 기록 조회
                recent_attendance = self.db.get_attendance_history(user_id, 5)
                
                message = f"""
📊 **{nickname}**님의 정보

💰 **총 포인트**: {user_stats['total_points']:,}P
📅 **출석 횟수**: {user_stats['attendance_count']}회
🕐 **마지막 업데이트**: {user_stats['last_updated']}

📋 **최근 출석 기록**:
"""
                
                if recent_attendance:
                    for i, record in enumerate(recent_attendance, 1):
                        message += f"{i}. {record['attendance_date']} (+{record['points_earned']}P)\n"
                else:
                    message += "출석 기록이 없습니다.\n"

            await update.message.reply_text(message.strip(), parse_mode='Markdown')
            logger.info(f"사용자 {user_id}({nickname})가 내정보를 조회했습니다")

        except Exception as e:
            logger.error(f"/내정보 명령어 처리 실패: {e}")
            await update.message.reply_text(
                format_error_message("general"),
                parse_mode='Markdown'
            )

    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /순위 명령어 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            # 리더보드 조회
            leaderboard = self.db.get_leaderboard(10)
            
            if not leaderboard:
                message = """
🏆 **포인트 순위**

아직 출석체크한 사용자가 없습니다.
첫 번째가 되어보세요! 🎯
"""
            else:
                message = "🏆 **포인트 순위 TOP 10**\n\n"
                
                for i, user_data in enumerate(leaderboard, 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}위"
                    message += f"{emoji} **{user_data['nickname']}**\n"
                    message += f"   💰 {user_data['total_points']:,}P ({user_data['attendance_count']}회)\n\n"

            await update.message.reply_text(message.strip(), parse_mode='Markdown')
            logger.info("리더보드 조회 요청 처리 완료")

        except Exception as e:
            logger.error(f"/순위 명령어 처리 실패: {e}")
            await update.message.reply_text(
                format_error_message("general"),
                parse_mode='Markdown'
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /도움말 명령어 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            help_message = """
📖 **베로니카 출석체크 봇 도움말**

🎯 **주요 명령어:**
• `/출첵` - 일일 출석체크 (100포인트 획득)
• `/내정보` - 내 포인트 및 출석 현황 조회
• `/순위` - 포인트 순위 조회 (TOP 10)
• `/도움말` - 이 도움말 메시지

⏰ **출석체크 규칙:**
• 하루에 한 번만 가능 (한국 시간 기준)
• 매일 자정(00:00)에 초기화
• 출석체크 시 100포인트 획득

💡 **팁:**
• 연속 출석으로 더 많은 포인트를 모아보세요!
• 순위에서 다른 사용자들과 경쟁해보세요!

📞 **문의사항이 있으시면 관리자에게 연락해주세요.**
"""

            await update.message.reply_text(help_message.strip(), parse_mode='Markdown')
            logger.info("도움말 조회 요청 처리 완료")

        except Exception as e:
            logger.error(f"/도움말 명령어 처리 실패: {e}")
            await update.message.reply_text(
                format_error_message("general"),
                parse_mode='Markdown'
            )

    def _get_user_nickname(self, user: User) -> str:
        """
        사용자 닉네임 추출

        Args:
            user: 텔레그램 사용자 객체

        Returns:
            사용자 닉네임
        """
        try:
            # 우선순위: username > first_name + last_name > first_name > user_id
            if user.username:
                return f"@{user.username}"
            elif user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            else:
                return f"User_{user.id}"
        except Exception as e:
            logger.error(f"닉네임 추출 실패: {e}")
            return f"User_{user.id}"