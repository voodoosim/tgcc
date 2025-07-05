# attendance_bot/main.py
"""텔레그램 출석체크 봇 실행 진입점"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from attendance_bot.db import AttendanceDB
from attendance_bot.handlers import AttendanceHandlers

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('attendance_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 외부 라이브러리 로깅 레벨 조정
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class AttendanceBot:
    """텔레그램 출석체크 봇 클래스"""

    def __init__(self, token: str, db_path: Optional[str] = None):
        """
        봇 초기화

        Args:
            token: 텔레그램 봇 토큰
            db_path: 데이터베이스 파일 경로
        """
        self.token = token
        self.db = AttendanceDB(db_path or "data/attendance.db")
        self.handlers = AttendanceHandlers(self.db)
        self.application: Optional[Application] = None

    async def setup_bot(self) -> None:
        """봇 설정 및 초기화"""
        try:
            # Application 생성
            self.application = Application.builder().token(self.token).build()

            # 명령어 핸들러 등록
            command_handlers = [
                CommandHandler("start", self.handlers.start_command),
                CommandHandler("출첵", self.handlers.attendance_command),
                CommandHandler("내정보", self.handlers.my_info_command),
                CommandHandler("순위", self.handlers.leaderboard_command),
                CommandHandler("도움말", self.handlers.help_command),
                CommandHandler("help", self.handlers.help_command),
            ]

            for handler in command_handlers:
                self.application.add_handler(handler)

            # 일반 메시지 핸들러 (명령어가 아닌 경우)
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )

            # 봇 명령어 메뉴 설정
            await self.set_bot_commands()

            logger.info("봇 설정 완료")

        except Exception as e:
            logger.error(f"봇 설정 실패: {e}")
            raise

    async def set_bot_commands(self) -> None:
        """봇 명령어 메뉴 설정"""
        try:
            commands = [
                BotCommand("start", "봇 시작하기"),
                BotCommand("출첵", "일일 출석체크"),
                BotCommand("내정보", "내 포인트 및 출석 현황"),
                BotCommand("순위", "포인트 순위 (TOP 10)"),
                BotCommand("도움말", "명령어 도움말"),
            ]

            await self.application.bot.set_my_commands(commands)
            logger.info("봇 명령어 메뉴 설정 완료")

        except Exception as e:
            logger.error(f"봇 명령어 메뉴 설정 실패: {e}")

    async def handle_message(self, update, context) -> None:
        """
        일반 메시지 핸들러

        Args:
            update: 텔레그램 업데이트 객체
            context: 봇 컨텍스트
        """
        try:
            user = update.effective_user
            message_text = update.message.text

            # '/출첵' 텍스트를 명령어로 처리
            if message_text == "출첫" or message_text == "출석" or message_text == "출석체크":
                await self.handlers.attendance_command(update, context)
                return

            # 기본 안내 메시지
            response = """
👋 안녕하세요! 베로니카 출석체크 봇입니다.

명령어를 사용해주세요:
• `/출첵` - 출석체크
• `/내정보` - 내 정보 보기
• `/순위` - 순위 보기
• `/도움말` - 도움말

또는 메뉴에서 명령어를 선택해주세요! 😊
"""

            await update.message.reply_text(response.strip())
            logger.info(f"사용자 {user.id}의 일반 메시지 처리: {message_text[:50]}")

        except Exception as e:
            logger.error(f"일반 메시지 처리 실패: {e}")

    async def start(self) -> None:
        """봇 시작"""
        try:
            if not self.application:
                await self.setup_bot()

            logger.info("텔레그램 출석체크 봇 시작")
            
            # 봇 정보 출력
            bot_info = await self.application.bot.get_me()
            logger.info(f"봇 정보: @{bot_info.username} ({bot_info.first_name})")

            # 봇 실행
            await self.application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )

        except Exception as e:
            logger.error(f"봇 실행 실패: {e}")
            raise

    async def stop(self) -> None:
        """봇 중지"""
        try:
            if self.application:
                await self.application.stop()
                logger.info("봇 중지됨")
        except Exception as e:
            logger.error(f"봇 중지 실패: {e}")


def get_bot_token() -> str:
    """
    환경변수에서 봇 토큰 가져오기

    Returns:
        봇 토큰

    Raises:
        ValueError: 토큰이 설정되지 않은 경우
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.\n"
            "다음과 같이 설정해주세요:\n"
            "export TELEGRAM_BOT_TOKEN='your_bot_token_here'"
        )
    return token


async def main() -> None:
    """메인 함수"""
    try:
        # 봇 토큰 가져오기
        token = get_bot_token()
        
        # 봇 인스턴스 생성 및 시작
        bot = AttendanceBot(token)
        await bot.start()

    except KeyboardInterrupt:
        logger.info("사용자에 의한 봇 중지")
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("봇이 중지되었습니다")
    except Exception as e:
        logger.error(f"프로그램 실행 실패: {e}")
        sys.exit(1)