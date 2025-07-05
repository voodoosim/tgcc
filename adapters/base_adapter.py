# adapters/base_adapter.py
"""텔레그램 세션 어댑터 베이스 클래스"""
import base64
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

from utils.phone import normalize_phone_number

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """텔레그램 세션 관리를 위한 추상 베이스 클래스"""

    def __init__(self):
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)

    def normalize_and_validate_phone(self, phone: str) -> str:
        """
        전화번호 정규화 및 검증

        Args:
            phone: 입력된 전화번호

        Returns:
            정규화된 전화번호

        Raises:
            ValueError: 유효하지 않은 전화번호인 경우
        """
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")
        return normalized_phone

    def get_session_file(self, phone: str) -> Path:
        """
        전화번호에 해당하는 세션 파일 경로 반환

        Args:
            phone: 정규화된 전화번호

        Returns:
            세션 파일 경로
        """
        # + 기호 제거하여 파일명 생성
        clean_phone = phone.lstrip("+")
        session_file: Path = self.sessions_dir / f"{clean_phone}.session"
        return session_file

    def session_to_string(self, session_file: Path) -> str:
        """
        세션 파일을 Base64 문자열로 변환

        Args:
            session_file: 세션 파일 경로

        Returns:
            Base64 인코딩된 세션 문자열

        Raises:
            FileNotFoundError: 세션 파일이 없는 경우
        """
        try:
            if not session_file.exists():
                raise FileNotFoundError(f"Session file not found: {session_file}")

            with open(session_file, "rb") as f:
                session_data = f.read()

            return base64.urlsafe_b64encode(session_data).decode("utf-8")

        except Exception as e:
            logger.error(f"Session string conversion failed: {e}")
            raise

    def string_to_session(self, session_string: str, phone: str) -> Path:
        """
        Base64 문자열을 세션 파일로 변환

        Args:
            session_string: Base64 인코딩된 세션 문자열
            phone: 전화번호

        Returns:
            생성된 세션 파일 경로

        Raises:
            ValueError: 디코딩 실패 시
        """
        try:
            # 전화번호 정규화
            phone = self.normalize_and_validate_phone(phone)

            # Base64 디코딩
            session_data = base64.urlsafe_b64decode(session_string.encode("utf-8"))

            # 세션 파일 저장
            session_file = self.get_session_file(phone)

            with open(session_file, "wb") as f:
                f.write(session_data)

            logger.info(f"Session file created: {session_file}")
            return session_file

        except Exception as e:
            logger.error(f"Session file conversion failed: {e}")
            raise

    @abstractmethod
    async def create_session(self, phone: str, api_id: int, api_hash: str) -> Dict[str, Union[str, bool]]:
        """
        세션 생성 및 인증 코드 요청

        Args:
            phone: 전화번호
            api_id: Telegram API ID
            api_hash: Telegram API Hash

        Returns:
            세션 생성 결과 딕셔너리
        """
        pass

    @abstractmethod
    async def complete_auth(
        self, phone: str, api_id: int, api_hash: str, code: str, phone_code_hash: str
    ) -> Dict[str, str]:
        """
        인증 코드로 세션 완료

        Args:
            phone: 전화번호
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            code: 인증 코드
            phone_code_hash: 전화 코드 해시

        Returns:
            인증 결과 딕셔너리
        """
        pass

    @abstractmethod
    async def validate_session(self, session_file: Path, api_id: int, api_hash: str) -> bool:
        """
        세션 유효성 검증

        Args:
            session_file: 세션 파일 경로
            api_id: Telegram API ID
            api_hash: Telegram API Hash

        Returns:
            세션 유효 여부
        """
        pass

    def check_session_exists(self, phone: str) -> bool:
        """
        세션 파일 존재 여부 확인

        Args:
            phone: 전화번호

        Returns:
            세션 존재 여부
        """
        session_file = self.get_session_file(phone)
        return session_file.exists()

    def ensure_phone_format(self, phone: str) -> str:
        """
        전화번호가 + 기호로 시작하도록 보장

        Args:
            phone: 전화번호

        Returns:
            + 기호가 포함된 전화번호
        """
        if not phone.startswith("+"):
            return "+" + phone
        return phone
