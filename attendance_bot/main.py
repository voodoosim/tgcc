# attendance_bot/main.py
"""Main entry point for the Telegram attendance bot"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from telegram.ext import Application
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from attendance_bot.db import AttendanceDB
from attendance_bot.handlers import setup_handlers

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("attendance_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Adjust external library logging levels
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class AttendanceBot:
    """Main attendance bot class"""
    
    def __init__(self, token: str, db_path: Optional[str] = None):
        """
        Initialize the attendance bot
        
        Args:
            token: Telegram bot token
            db_path: Path to SQLite database file (optional)
        """
        self.token = token
        self.db_path = db_path or "attendance.db"
        self.db: Optional[AttendanceDB] = None
        self.application: Optional[Application] = None
    
    async def initialize(self) -> None:
        """Initialize database and bot application"""
        try:
            # Initialize database
            self.db = AttendanceDB(self.db_path)
            logger.info(f"Database initialized: {self.db_path}")
            
            # Create bot application
            self.application = Application.builder().token(self.token).build()
            
            # Setup handlers
            setup_handlers(self.application, self.db)
            logger.info("Bot handlers setup complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    async def start_polling(self) -> None:
        """Start the bot with polling"""
        if not self.application:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        
        try:
            logger.info("Starting bot polling...")
            await self.application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the bot and cleanup resources"""
        try:
            if self.application:
                await self.application.stop()
                logger.info("Bot application stopped")
            
            if self.db:
                self.db.close()
                logger.info("Database connection closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def start_webhook(self, webhook_url: str, port: int = 8443) -> None:
        """
        Start the bot with webhook (for production deployment)
        
        Args:
            webhook_url: Public webhook URL
            port: Port to listen on
        """
        if not self.application:
            raise RuntimeError("Bot not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Starting bot webhook on {webhook_url}:{port}")
            await self.application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Error during webhook: {e}")
            raise


def get_bot_token() -> str:
    """
    Get bot token from environment variables or user input
    
    Returns:
        Bot token string
        
    Raises:
        ValueError: If token is not found
    """
    # Try environment variable first
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if token:
        logger.info("Bot token loaded from environment variable")
        return token
    
    # Try .env file
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token:
            logger.info("Bot token loaded from .env file")
            return token
    
    # Ask user for token
    print("🤖 텔레그램 봇 토큰을 입력해주세요.")
    print("(@BotFather에서 받은 토큰을 입력하세요)")
    token = input("Bot Token: ").strip()
    
    if not token:
        raise ValueError("Bot token is required")
    
    # Save to .env file for future use
    try:
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"\nTELEGRAM_BOT_TOKEN={token}\n")
        print("✅ 토큰이 .env 파일에 저장되었습니다.")
    except Exception as e:
        logger.warning(f"Could not save token to .env file: {e}")
    
    return token


async def main() -> None:
    """Main function to run the bot"""
    try:
        # Get bot token
        token = get_bot_token()
        
        # Get database path from environment or use default
        db_path = os.getenv("DB_PATH", "attendance.db")
        
        # Create and initialize bot
        bot = AttendanceBot(token, db_path)
        await bot.initialize()
        
        # Check if webhook URL is provided for production deployment
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", "8443"))
        
        if webhook_url:
            logger.info("Starting bot in webhook mode")
            await bot.start_webhook(webhook_url, port)
        else:
            logger.info("Starting bot in polling mode")
            await bot.start_polling()
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if 'bot' in locals():
            await bot.stop()


def run_bot() -> None:
    """Entry point function for running the bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 봇이 중지되었습니다.")
    except Exception as e:
        print(f"❌ 봇 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 출석체크 봇을 시작합니다...")
    print("중지하려면 Ctrl+C를 누르세요.\n")
    run_bot()