"""
Telethon Adapter for Veronica Project

This module provides a Telethon-based adapter for session management,
standardized to use String Sessions for compatibility and reliability.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Union

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    UnauthorizedError,
)
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerUser, User

from utils.phone import normalize_phone_number

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TelethonAdapter:
    """A Telethon-based adapter for session management using String Sessions."""

    def __init__(self, sessions_dir: Path = Path("sessions")):
        """
        Initializes the TelethonAdapter.

        Args:
            sessions_dir: The directory to store session files.
        """
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(exist_ok=True)

    async def _disconnect_client(self, client: TelegramClient):
        """Safely disconnect the client."""
        if client and client.is_connected():
            try:
                await client.disconnect()
            except Exception as e:
                logging.warning("Failed to disconnect client: %s", e)

    async def create_session(self, phone: str, api_id: int, api_hash: str) -> Dict[str, Union[str, bool]]:
        """
        Starts the session creation process.
        This now only initiates the client and sends the code.
        The session string is handled in complete_auth.
        """
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")

        client = TelegramClient(StringSession(), api_id, api_hash)
        try:
            await client.connect()
            result = await client.send_code_request(normalized_phone)
            return {
                "phone": normalized_phone,
                "phone_code_hash": result.phone_code_hash,
                "session_string": client.session.save(),
                "exists": False,  # A new session is always created
            }
        except (UnauthorizedError, FloodWaitError, ValueError) as e:
            logging.error("Failed to create session for %s: %s", normalized_phone, e)
            raise
        finally:
            await self._disconnect_client(client)

    async def complete_auth(
        self,
        phone: str,
        api_id: int,
        api_hash: str,
        code: str,
        phone_code_hash: str,
        session_string: str,
    ) -> Dict[str, str]:
        """
        Complete authentication with the code and return the final session string.
        """
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")

        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        try:
            await client.connect()
            await client.sign_in(normalized_phone, code, phone_code_hash=phone_code_hash)

            me: Optional[Union[User, InputPeerUser]] = await client.get_me()
            if not me or not isinstance(me, User):
                raise ValueError("Failed to retrieve user information")

            final_session_string = client.session.save()
            return {
                "user_id": str(me.id),
                "username": me.username or "",
                "phone": me.phone or normalized_phone,
                "session_string": final_session_string,
            }
        except (PhoneCodeInvalidError, SessionPasswordNeededError, ValueError) as e:
            logging.error("Authentication failed for %s: %s", normalized_phone, e)
            raise
        finally:
            await self._disconnect_client(client)

    async def validate_session(self, session_string: str, api_id: int, api_hash: str) -> bool:
        """
        Validate an existing session string.
        """
        if not session_string:
            return False

        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        is_valid = False  # Initialize is_valid
        try:
            await client.connect()
            is_valid = await client.is_user_authorized()
        except Exception as e:
            logging.error("Unexpected error during validation: %s", e)
            is_valid = False
        finally:
            await self._disconnect_client(client)
        return is_valid
