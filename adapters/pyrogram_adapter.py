"""
Pyrogram Adapter for Veronica Project

This module provides a Pyrogram-based adapter for session management,
standardized to use String Sessions for compatibility and reliability.
"""

import logging
from typing import Dict, Union

from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, PhoneCodeInvalid
from pyrogram.session.session import Session

from utils.phone import normalize_phone_number

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PyrogramAdapter:
    """A Pyrogram-based adapter for session management using String Sessions."""

    async def create_session(
        self, phone: str, api_id: int, api_hash: str
    ) -> Dict[str, Union[str, bool]]:
        """
        Starts the session creation process by sending the code.
        """
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")

        # Pyrogram can work in-memory to get the phone_code_hash
        async with Client(":memory:", api_id, api_hash, in_memory=True) as client:
            sent_code = await client.send_code(normalized_phone)
            return {
                "phone": normalized_phone,
                "phone_code_hash": sent_code.phone_code_hash,
                "exists": False,
            }

    async def complete_auth(
        self, phone: str, api_id: int, api_hash: str, code: str, phone_code_hash: str
    ) -> Dict[str, str]:
        """
        Complete authentication and return the session string.
        """
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise ValueError("Invalid phone number format")

        async with Client(":memory:", api_id, api_hash, in_memory=True) as client:
            try:
                await client.sign_in(normalized_phone, phone_code_hash, code)
                me = await client.get_me()
                if not me:
                    raise ValueError("Failed to retrieve user information")

                session_string = await client.export_session_string()
                return {
                    "user_id": str(me.id),
                    "username": me.username or "",
                    "phone": me.phone_number or normalized_phone,
                    "session_string": session_string,
                }
            except (PhoneCodeInvalid, AuthKeyUnregistered) as e:
                logging.error("Authentication failed for %s: %s", normalized_phone, e)
                raise

    async def validate_session(
        self, session_string: str, api_id: int, api_hash: str
    ) -> bool:
        """
        Validate an existing session string.
        """
        if not session_string:
            return False

        try:
            async with Client(Session.from_string(session_string), api_id, api_hash) as client:
                is_authorized = await client.get_me() is not None
                return is_authorized
        except Exception as e:
            logging.error("Unexpected error during validation: %s", e)
            return False
