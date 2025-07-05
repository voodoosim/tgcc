import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Union

from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, FloodWait, PhoneCodeInvalid

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PyrogramAdapter:
    """Pyrogram 기반 세션 관리"""

    def __init__(self):
        self.sessions_dir = Path("sessions")

    async def create_session(
        self, phone: str, api_id: int, api_hash: str
    ) -> Dict[str, Union[str, bool]]:
        """세션 생성 및 인증 코드 요청"""
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
            if not phone.startswith('+'):
                phone = '+' + phone
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

    async def validate_session(
        self, session_file: Path, api_id: int, api_hash: str
    ) -> bool:
        """세션 유효성 검증"""
        client: Optional[Client] = None
        try:
            if not session_file.exists():
                return False
            client = Client(str(session_file.stem), api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            return me is not None
        except AuthKeyUnregistered as e:
            logging.error("Session invalid: %s", e)
            return False
        except ValueError as e:
            logging.error("Validation failed: %s", e)
            return False
        finally:
            if client:
                await client.disconnect()

    def session_to_string(self, session_file: Path) -> str:
        """세션 파일을 Base64 문자열로 변환"""
        try:
            if not session_file.exists():
                raise FileNotFoundError(f"Session file not found: {session_file}")
            with open(session_file, 'rb') as f:
                return base64.urlsafe_b64encode(f.read()).decode('utf-8')
        except (FileNotFoundError, ValueError) as e:
            logging.error("Session string conversion failed: %s", e)
            raise

    def string_to_session(self, session_string: str, phone: str) -> Path:
        """Base64 문자열로 세션 파일 생성"""
        try:
            session_data = base64.urlsafe_b64decode(session_string.encode('utf-8'))
            session_file = self.sessions_dir / f"{phone.lstrip('+')}.session"
            with open(session_file, 'wb') as f:
                f.write(session_data)
            return session_file
        except (ValueError, FileNotFoundError) as e:
            logging.error("Session file conversion failed: %s", e)
            raise
