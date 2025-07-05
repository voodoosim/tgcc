# adapters/telethon_adapter.py
import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Union

from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError, UnauthorizedError
from telethon.tl.types import User

from .base_adapter import BaseAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TelethonAdapter(BaseAdapter):
    """Telethon 기반 세션 관리"""

    def __init__(self):
        super().__init__()

    async def create_session(self, phone: str, api_id: int, api_hash: str) -> Dict[str, Union[str, bool]]:
        """세션 생성 및 인증 코드 요청"""
        # 전화번호 정규화
        phone = self.normalize_and_validate_phone(phone)

        session_file = self.get_session_file(phone)
        client: Optional[TelegramClient] = None
        try:
            if session_file.exists():
                logging.warning("Session file already exists: %s", session_file)
                return {
                    "phone": phone,
                    "phone_code_hash": "",
                    "session_file": str(session_file),
                    "exists": True,
                }
            client = TelegramClient(str(session_file), api_id, api_hash)
            await client.connect()
            if not phone.startswith("+"):
                phone = "+" + phone
            result = await client.send_code_request(phone)
            if result is None:
                raise ValueError("Failed to send code request")
            return {
                "phone": phone,
                "phone_code_hash": result.phone_code_hash,
                "session_file": str(session_file),
                "exists": False,
            }
        except UnauthorizedError as e:
            logging.error("Authentication error: %s", e)
            raise
        except FloodWaitError as e:
            logging.error("Rate limit hit, wait %s seconds", e.seconds)
            raise
        except ValueError as e:
            logging.error("Invalid input in create_session: %s", e)
            raise
        finally:
            if client and client.is_connected():
                try:
                    await client.disconnect()
                except RuntimeError:
                    # 연결 종료 시 발생할 수 있는 예외 처리
                    logging.debug("Error disconnecting client")

    async def complete_auth(
        self, phone: str, api_id: int, api_hash: str, code: str, phone_code_hash: str
    ) -> Dict[str, str]:
        """인증 코드로 세션 완료"""
        # 전화번호 정규화
        phone = self.normalize_and_validate_phone(phone)

        session_file = self.get_session_file(phone)
        client: Optional[TelegramClient] = None
        try:
            client = TelegramClient(str(session_file), api_id, api_hash)
            await client.connect()
            sign_in_result = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            if sign_in_result is None:
                raise ValueError("Sign-in failed")
            me: User = await client.get_me()  # type: ignore
            if me is None:
                raise ValueError("Failed to retrieve user information")
            return {
                "user_id": str(me.id),
                "username": me.username or "",
                "phone": me.phone or phone,
            }
        except PhoneCodeInvalidError as e:
            logging.error("Invalid authentication code: %s", e)
            raise
        except SessionPasswordNeededError as e:
            logging.error("2FA password required: %s", e)
            raise
        except ValueError as e:
            logging.error("Authentication failed: %s", e)
            raise
        finally:
            if client and client.is_connected():
                try:
                    await client.disconnect()
                except RuntimeError:
                    # 연결 종료 시 발생할 수 있는 예외 처리
                    logging.debug("Error disconnecting client")

    async def validate_session(self, session_file: Path, api_id: int, api_hash: str) -> bool:
        """세션 유효성 검증"""
        client: Optional[TelegramClient] = None
        try:
            if not session_file.exists():
                logging.warning(f"Session file not found: {session_file}")
                return False

            logging.info(f"Validating session file: {session_file}")
            client = TelegramClient(str(session_file), api_id, api_hash)
            await client.connect()

            # 사용자 인증 확인
            is_authorized = await client.is_user_authorized()

            if is_authorized:
                # 추가로 사용자 정보 가져와서 확인
                try:
                    me = await client.get_me()
                    if me:
                        logging.info(f"Session valid for user: {me.username or me.phone}")
                        return True
                except Exception as e:
                    logging.error(f"Error getting user info: {e}")
                    return False

            return False

        except ValueError as e:
            logging.error("Validation failed: %s", e)
            return False
        except Exception as e:
            logging.error(f"Unexpected error during validation: {e}")
            return False
        finally:
            if client and client.is_connected():
                try:
                    await client.disconnect()
                except RuntimeError:
                    # 연결 종료 시 발생할 수 있는 예외 처리
                    logging.debug("Error disconnecting client")
