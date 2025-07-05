# core/logging_config.py
"""로깅 설정 모듈"""
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """컬러 출력을 위한 포매터"""

    # ANSI 색상 코드
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_file: Optional[str] = None, log_level: str = "INFO", console: bool = True, file: bool = True
) -> logging.Logger:
    """
    로깅 설정

    Args:
        log_file: 로그 파일 경로
        log_level: 로그 레벨
        console: 콘솔 출력 여부
        file: 파일 출력 여부

    Returns:
        설정된 루트 로거
    """
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 로그 파일 이름 생성
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"veronica_{timestamp}.log"
    else:
        log_file = Path(log_file)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포맷 설정
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    # 파일 핸들러 추가
    if file:
        # 회전 파일 핸들러 (10MB, 5개 백업)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # 콘솔 핸들러 추가
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 외부 라이브러리 로그 레벨 설정
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("pyrogram.crypto").setLevel(logging.ERROR)
    logging.getLogger("pyrogram.session").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 가져오기

    Args:
        name: 로거 이름 (보통 __name__)

    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)


class LoggerMixin:
    """로거를 포함하는 클래스를 위한 믹스인"""

    @property
    def logger(self) -> logging.Logger:
        """클래스 전용 로거"""
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


# 로그 메시지 템플릿
class LogMessages:
    """표준 로그 메시지 템플릿"""

    # 세션 관련
    SESSION_CREATE_START = "Creating session for phone: {phone}"
    SESSION_CREATE_SUCCESS = "Session created successfully for: {phone}"
    SESSION_CREATE_FAILED = "Failed to create session for {phone}: {error}"
    SESSION_VALIDATE_START = "Validating session for: {phone}"
    SESSION_VALIDATE_SUCCESS = "Session is valid for: {phone}"
    SESSION_VALIDATE_FAILED = "Session validation failed for: {phone}"
    SESSION_EXISTS = "Session already exists for: {phone}"

    # API 관련
    API_CREDENTIAL_ADDED = "API credential added: {name}"
    API_CREDENTIAL_EXISTS = "API credential already exists: {name}"
    API_CREDENTIAL_INVALID = "Invalid API credentials"

    # 전화번호 관련
    PHONE_NORMALIZED = "Phone normalized: {original} -> {normalized}"
    PHONE_INVALID = "Invalid phone number: {phone}"

    # 네트워크 관련
    RATE_LIMIT_HIT = "Rate limit hit, wait {seconds} seconds"
    NETWORK_ERROR = "Network error: {error}"

    # 파일 관련
    FILE_NOT_FOUND = "File not found: {path}"
    FILE_CREATED = "File created: {path}"
    FILE_DELETED = "File deleted: {path}"
