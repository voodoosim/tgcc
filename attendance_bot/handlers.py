# attendance_bot/handlers.py
"""Telegram bot command handlers for attendance tracking"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional

from .db import AttendanceDB
from .utils import (
    get_korean_date_string,
    calculate_points,
    format_attendance_message,
    format_already_attended_message,
    format_stats_message,
    format_leaderboard_message,
    validate_nickname,
    get_welcome_message
)

logger = logging.getLogger(__name__)


class AttendanceHandlers:
    """Attendance bot command handlers"""
    
    def __init__(self, db: AttendanceDB):
        """
        Initialize handlers with database connection
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message:
                return
                
            welcome_msg = get_welcome_message()
            await update.message.reply_text(welcome_msg)
            
            if update.effective_user:
                logger.info(f"Sent welcome message to user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            if update.message:
                await update.message.reply_text("❌ 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message:
                return
                
            help_text = """🤖 출석체크 봇 도움말

📝 사용 가능한 명령어:
• /출첵 - 출석체크하기 (1일 1회, 100포인트)
• /통계 - 내 출석 통계 보기
• /순위 - 출석 리더보드 보기 (Top 10)
• /help - 이 도움말 보기

💡 팁:
- 출석체크는 한국시간 기준 매일 자정에 초기화됩니다
- 하루에 한 번만 출석체크가 가능합니다
- 연속 출석시 보너스 포인트를 받을 수 있습니다 (추후 업데이트 예정)

문의사항이 있으시면 관리자에게 연락해주세요! 📞"""
            
            await update.message.reply_text(help_text)
            
            if update.effective_user:
                logger.info(f"Sent help message to user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            if update.message:
                await update.message.reply_text("❌ 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    async def attendance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /출첵 (attendance) command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message or not update.effective_user:
                return
                
            user = update.effective_user
            user_id = str(user.id)
            
            # Get user's display name (prefer username, fallback to first_name)
            nickname = validate_nickname(user.username or user.first_name or "익명")
            
            # Get today's date in Korean timezone
            today = get_korean_date_string()
            
            # Check if user already attended today
            if self.db.check_attendance_today(user_id, today):
                # User already attended, show their stats
                stats = self.db.get_user_stats(user_id)
                if stats:
                    message = format_already_attended_message(stats['nickname'], stats['total_points'])
                else:
                    message = "⚠️ 이미 출석체크를 완료했습니다!\n내일 다시 출석체크해주세요! 😊"
                    
                await update.message.reply_text(message)
                logger.info(f"User {user_id} tried to attend again on {today}")
                return
            
            # Calculate points (base 100 points for now)
            points = calculate_points(100)
            
            # Record attendance
            success = self.db.record_attendance(user_id, nickname, today, points)
            
            if success:
                # Get updated user stats
                stats = self.db.get_user_stats(user_id)
                if stats:
                    message = format_attendance_message(
                        stats['nickname'], 
                        points, 
                        stats['total_points'], 
                        stats['total_attendance']
                    )
                else:
                    message = f"✅ 출석체크 완료!\n🎁 {points}포인트를 획득했습니다!"
                
                await update.message.reply_text(message)
                logger.info(f"Recorded attendance for user {user_id} on {today}")
                
            else:
                await update.message.reply_text("❌ 출석체크 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                logger.error(f"Failed to record attendance for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in attendance_command: {e}")
            if update.message:
                await update.message.reply_text("❌ 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /통계 (stats) command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message or not update.effective_user:
                return
                
            user_id = str(update.effective_user.id)
            
            # Get user stats
            stats = self.db.get_user_stats(user_id)
            
            if stats:
                message = format_stats_message(stats)
                
                # Add recent attendance history
                history = self.db.get_attendance_history(user_id, 5)
                if history:
                    message += "\n\n📅 최근 출석 기록:\n"
                    for record in history:
                        message += f"• {record['date']} (+{record['points']}포인트)\n"
                
            else:
                message = """📊 아직 출석 기록이 없습니다.

/출첵 명령어로 첫 출석체크를 시작해보세요! 🚀"""
            
            await update.message.reply_text(message)
            logger.info(f"Sent stats to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            if update.message:
                await update.message.reply_text("❌ 통계 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /순위 (leaderboard) command
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message:
                return
                
            # Get top 10 users
            top_users = self.db.get_top_users(10)
            
            message = format_leaderboard_message(top_users)
            
            await update.message.reply_text(message)
            
            if update.effective_user:
                logger.info(f"Sent leaderboard to user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in leaderboard_command: {e}")
            if update.message:
                await update.message.reply_text("❌ 순위 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle unknown commands
        
        Args:
            update: Telegram update object
            context: Bot context
        """
        try:
            if not update.message:
                return
                
            message = """❓ 알 수 없는 명령어입니다.

사용 가능한 명령어:
• /출첵 - 출석체크하기
• /통계 - 내 출석 통계 보기
• /순위 - 출석 리더보드 보기
• /help - 도움말 보기

도움이 필요하시면 /help 명령어를 사용해주세요! 😊"""
            
            await update.message.reply_text(message)
            
            if update.effective_user and update.message.text:
                logger.info(f"Unknown command from user {update.effective_user.id}: {update.message.text}")
            
        except Exception as e:
            logger.error(f"Error in unknown_command: {e}")
    
    async def error_handler(self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle errors
        
        Args:
            update: Telegram update object (may be None)
            context: Bot context
        """
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                )
            except Exception as e:
                logger.error(f"Error sending error message: {e}")


def setup_handlers(application, db: AttendanceDB) -> None:
    """
    Set up all command handlers
    
    Args:
        application: Telegram bot application
        db: Database manager instance
    """
    handlers = AttendanceHandlers(db)
    
    # Add command handlers
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("출첵", handlers.attendance_command))
    application.add_handler(CommandHandler("통계", handlers.stats_command))
    application.add_handler(CommandHandler("순위", handlers.leaderboard_command))
    
    # Add unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, handlers.unknown_command))
    
    # Add error handler
    application.add_error_handler(handlers.error_handler)
    
    logger.info("All handlers registered successfully")