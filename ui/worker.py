# ui/worker.py
import traceback

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from adapters.pyrogram_adapter import PyrogramAdapter
from adapters.telethon_adapter import TelethonAdapter


class Worker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(str, str)
    failure = pyqtSignal(str)
    request_2fa = pyqtSignal()

    def __init__(self, library, api_id, api_hash, phone_number, session_name, action, session_string=None):
        super().__init__()
        self.library = library
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.action = action
        self.session_string = session_string
        self.adapter = None
        self.two_fa_password = None
        self._is_running = True

    def run(self):
        try:
            if self.library == "Telethon":
                self.adapter = TelethonAdapter(self.api_id, self.api_hash)
            else:
                self.adapter = PyrogramAdapter(self.api_id, self.api_hash)

            if self.action == "create":
                self._handle_creation()
            elif self.action == "check":
                self._handle_check()
            elif self.action == "string_import":
                self._handle_string_import()

        except Exception as e:
            error_info = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            self.failure.emit(f"알 수 없는 오류 발생:\n{error_info}")
        finally:
            self.finished.emit()

    def _handle_creation(self):
        result, message = self.adapter.create_session(
            session_name=self.session_name,
            phone_number=self.phone_number,
            password_callback=self._request_2fa_from_main_thread,
        )
        if result:
            session_string = self.adapter.export_session_string(self.session_name)
            self.success.emit(session_string, message)
        else:
            self.failure.emit(message)

    def _handle_check(self):
        result, message = self.adapter.check_session(self.session_name)
        if result:
            session_string = self.adapter.export_session_string(self.session_name)
            self.success.emit(session_string, message)
        else:
            self.failure.emit(message)

    def _handle_string_import(self):
        result, message = self.adapter.import_session_from_string(self.session_name, self.session_string)
        if result:
            self.success.emit(self.session_string, message)
        else:
            self.failure.emit(message)

    def _request_2fa_from_main_thread(self):
        self.request_2fa.emit()
        while self.two_fa_password is None and self._is_running:
            QThread.msleep(100)
        return self.two_fa_password

    def set_2fa_password(self, password):
        self.two_fa_password = password

    def stop(self):
        self._is_running = False
