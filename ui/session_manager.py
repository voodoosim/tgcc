"""
Session Manager for Veronica Project

Coordinates UI events with adapter logic for session management.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pyperclip

from adapters.pyrogram_adapter import PyrogramAdapter
from adapters.telethon_adapter import TelethonAdapter
from core.config import Config
from ui.async_worker import AsyncWorker
from ui.dialogs import DialogHelper
from utils.phone import (
    format_phone_display,
    guess_country_from_number,
    normalize_phone_number,
    validate_phone_number,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Handles all session-related logic."""

    def __init__(self, parent: Any, log_callback: Callable):
        self.parent = parent
        self.log = log_callback
        self.config = Config()
        self.adapters = {
            "telethon": TelethonAdapter(),
            "pyrogram": PyrogramAdapter(),
        }
        self.active_workers: List[AsyncWorker] = []
        self.current_session_string: Optional[str] = None

    def cleanup_workers(self):
        """Clean up any active async workers."""
        for worker in self.active_workers:
            if worker.isRunning():
                worker.stop()
        self.active_workers.clear()

    def _run_async_task(self, coro: Any, on_success: Callable, on_error: Callable):
        """Helper to run an async task in a worker thread."""
        self.cleanup_workers()
        worker = AsyncWorker(coro)
        worker.result.connect(on_success)
        worker.error.connect(on_error)
        worker.finished.connect(lambda: self._remove_worker(worker))
        self.active_workers.append(worker)
        worker.start()

    def _remove_worker(self, worker: AsyncWorker):
        """Remove a worker from the active list once finished."""
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def create_session(self, phone: str, api_index: int, library: str):
        """Start the session creation process."""
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone or not validate_phone_number(normalized_phone):
            self.log("Invalid phone number format.", "ERROR")
            return

        api_cred = self.config.get_api_credentials()[api_index]
        adapter = self.adapters[library]

        self.log(f"Requesting code for {normalized_phone} via {library}...", "INFO")
        coro = adapter.create_session(
            normalized_phone, int(api_cred["api_id"]), api_cred["api_hash"]
        )
        self._run_async_task(
            coro,
            lambda result: self._handle_code_request_result(
                result, normalized_phone, api_cred, library
            ),
            lambda e: self.log(f"Failed to request code: {e}", "ERROR"),
        )

    def _handle_code_request_result(self, result: Dict, phone: str, api_cred: Dict, library: str):
        """Handle the result of a code request and ask for the code."""
        code = DialogHelper.get_auth_code(self.parent)
        if not code:
            self.log("Authentication cancelled.", "WARNING")
            return

        adapter = self.adapters[library]
        session_string = result.get("session_string")  # For Telethon
        phone_code_hash = result["phone_code_hash"]

        self.log("Verifying code and completing authentication...", "INFO")
        coro = adapter.complete_auth(
            phone, int(api_cred["api_id"]), api_cred["api_hash"], code, phone_code_hash
        )
        self._run_async_task(coro, self._handle_auth_complete, lambda e: self.log(f"Authentication failed: {e}", "ERROR"))

    def _handle_auth_complete(self, result: Optional[Dict]):
        """Handle the final result of a successful authentication."""
        if not result or not isinstance(result, Dict):
            self.log("Authentication result is invalid or not a dictionary.", "ERROR")
            return

        session_string = result.get("session_string")
        phone = result.get("phone")
        username = result.get("username")

        if not session_string or not isinstance(session_string, str):
            self.log("Authentication result missing session string.", "ERROR")
            return
        if not phone or not isinstance(phone, str):
            self.log("Authentication result missing phone number.", "ERROR")
            return

        self.current_session_string = session_string
        self.parent.session_string.setText(self.current_session_string[:60] + "...")
        self.log("✨ Session created successfully!", "SUCCESS")
        self.log(f"User: {username or phone}", "INFO")
        self._save_session_to_file(phone, self.current_session_string)

    def _save_session_to_file(self, phone: str, session_string: str):
        """Save the session string to a .session file."""
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        session_file = sessions_dir / f"{phone.lstrip('+')}.session"
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                f.write(session_string)
            self.log(f"Session saved to: {session_file}", "INFO")
        except IOError as e:
            self.log(f"Failed to save session file: {e}", "ERROR")

    def validate_session(self, phone: str, api_index: int, library: str):
        """Validate the current session string."""
        if not self.current_session_string:
            self.log("No session loaded to validate.", "WARNING")
            return

        api_cred = self.config.get_api_credentials()[api_index]
        adapter = self.adapters[library]

        self.log(f"Validating session for {phone} via {library}...", "INFO")
        coro = adapter.validate_session(
            self.current_session_string, int(api_cred["api_id"]), api_cred["api_hash"]
        )
        self._run_async_task(coro, self._handle_validate_result, lambda e: self.log(f"Validation failed: {e}", "ERROR"))

    def _handle_validate_result(self, is_valid: bool):
        """Handle the result of a session validation."""
        if is_valid:
            self.log("✅ Session is valid and active.", "SUCCESS")
        else:
            self.log("❌ Session is invalid or expired.", "ERROR")

    def copy_session_string(self):
        """Copy the current session string to the clipboard."""
        if self.current_session_string:
            pyperclip.copy(self.current_session_string)
            self.log("📋 Session string copied to clipboard!", "SUCCESS")
        else:
            self.log("No session string to copy.", "WARNING")

    def import_session(self):
        """Import a session string from a dialog."""
        session_string = DialogHelper.get_session_string(self.parent)
        if session_string:
            self.current_session_string = session_string
            self.parent.session_string.setText(session_string[:60] + "...")
            self.log("📥 Session string imported successfully.", "SUCCESS")
            self.log("You can now validate it or save it by creating a session.", "INFO")

    def load_session_file(self, file_path: str):
        """Load a session string from a .session file."""
        try:
            p = Path(file_path)
            with open(p, "r", encoding="utf-8") as f:
                session_string = f.read().strip()
            
            self.current_session_string = session_string
            self.parent.session_string.setText(session_string[:60] + "...")
            self.parent.phone_input.setText(p.stem)
            self.log(f"📁 Session loaded from {p.name}.", "SUCCESS")
            self.log("You can now validate the loaded session.", "INFO")
        except (IOError, UnicodeDecodeError) as e:
            self.log(f"Failed to load session file: {e}", "ERROR")