import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Union

from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, FloodWait, PhoneCodeInvalid

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    전화번호를 정규화합니다.
    - 공백, 하이픈, 괄호 등 제거
    - + 기호는 유지
    - 숫자만 남김
    """
    import re

    if not phone:
        return None

    # + 기호를 임시로 보관
    has_plus = phone.startswith("+")

    # 숫자만 추출
    digits = re.sub(r"[^\d]", "", phone)

    if not digits:
        return None

    # + 기호 복원
    if has_plus:
        return "+" + digits

    return digits


class PyrogramAdapter:
    """Pyrogram 기반 세션 관리"""

    def __init__(self):
        self.sessions_dir = Path("sessions")

    async def create_session(self, phone: str, api_id: int, api_hash: str) -> Dict[str, Union[str, bool]]:
        """세션 생성 및 인증 코드 요청"""
        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")
        phone = normalized_phone

        session_file = self.sessions_dir / f"{phone.lstrip('+')}.session"
        client: Optional[Client] = None
        try:
            self.sessions_dir.mkdir(exist_ok=True)
            if session_file.exists():
                logging.warning("Session file already exists: %s", session_file)
                return {
                    "phone": phone,
                    "phone_code_hash": "",
                    "session_file": str(session_file),
                    "exists": True,
                }
            client = Client(str(session_file.stem), api_id, api_hash)
            await client.connect()
            if not phone.startswith("+"):
                phone = "+" + phone
            sent_code = await client.send_code(phone)
            return {
                "phone": phone,
                "phone_code_hash": sent_code.phone_code_hash,
                "session_file": str(session_file),
                "exists": False,
            }
        except FloodWait as e:
            logging.error("Rate limit hit, wait %s seconds", e.value)
            raise
        except ValueError as e:
            logging.error("Invalid input in create_session: %s", e)
            raise
        finally:
            if client:
                await client.disconnect()

    async def complete_auth(
        self, phone: str, api_id: int, api_hash: str, code: str, phone_code_hash: str
    ) -> Dict[str, str]:
        """인증 코드로 세션 완료"""
        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")
        phone = normalized_phone

        session_file = self.sessions_dir / f"{phone.lstrip('+')}.session"
        client: Optional[Client] = None
        try:
            client = Client(str(session_file.stem), api_id, api_hash)
            await client.connect()
            await client.sign_in(phone, phone_code_hash, code)
            me = await client.get_me()
            if me is None:
                raise ValueError("Failed to retrieve user information")
            return {
                "user_id": str(me.id),
                "username": me.username or "",
                "phone": me.phone_number or phone,
            }
        except PhoneCodeInvalid as e:
            logging.error("Invalid authentication code: %s", e)
            raise
        except ValueError as e:
            logging.error("Authentication failed: %s", e)
            raise
        finally:
            if client:
                await client.disconnect()

    async def validate_session(self, session_file: Path, api_id: int, api_hash: str) -> bool:
        """세션 유효성 검증"""
        client: Optional[Client] = None
        try:
            if not session_file.exists():
                logging.warning(f"Session file not found: {session_file}")
                return False

            logging.info(f"Validating session file: {session_file}")
            client = Client(str(session_file.stem), api_id, api_hash)
            await client.connect()

            # 사용자 정보 가져와서 확인
            try:
                me = await client.get_me()
                if me:
                    logging.info(f"Session valid for user: {me.username or me.phone_number}")
                    return True
                return False
            except Exception as e:
                logging.error(f"Error getting user info: {e}")
                return False

        except AuthKeyUnregistered as e:
            logging.error("Session invalid: %s", e)
            return False
        except ValueError as e:
            logging.error("Validation failed: %s", e)
            return False
        except Exception as e:
            logging.error(f"Unexpected error during validation: {e}")
            return False
        finally:
            if client:
                await client.disconnect()

    def session_to_string(self, session_file: Path) -> str:
        """세션 파일을 Base64 문자열로 변환"""
        try:
            if not session_file.exists():
                raise FileNotFoundError(f"Session file not found: {session_file}")
            with open(session_file, "rb") as f:
                return base64.urlsafe_b64encode(f.read()).decode("utf-8")
        except (FileNotFoundError, ValueError) as e:
            logging.error("Session string conversion failed: %s", e)
            raise

    def string_to_session(self, session_string: str, phone: str) -> Path:
        """Base64 문자열로 세션 파일 생성"""
        try:
            # 전화번호 정규화
            normalized_phone = normalize_phone_number(phone)
            if not normalized_phone:
                raise ValueError("Invalid phone number format")
            phone = normalized_phone

            session_data = base64.urlsafe_b64decode(session_string.encode("utf-8"))
            session_file = self.sessions_dir / f"{phone.lstrip('+')}.session"

            # 디렉토리 생성
            self.sessions_dir.mkdir(exist_ok=True)

            with open(session_file, "wb") as f:
                f.write(session_data)
            return session_file
        except (ValueError, FileNotFoundError) as e:
            logging.error("Session file conversion failed: %s", e)
            raise
