# ui/worker.py
import traceback

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from adapters.pyrogram_adapter import PyrogramAdapter
from adapters.telethon_adapter import TelethonAdapter


class Worker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(str, str)
    failure = pyqtSignal(str)
    # 2FA 뿐만 아니라 일반 코드 입력도 처리할 수 있도록 시그널 확장
    request_code_from_gui = pyqtSignal(str)

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
        self.gui_input = None
        self._is_running = True

    def run(self):
        try:
            if self.library == "Telethon":
                self.adapter = TelethonAdapter(self.api_id, self.api_hash)
            else:
                self.adapter = PyrogramAdapter(self.api_id, self.api_hash)

            action_map = {
                "create": self._handle_creation,
                "check": self._handle_check,
                "string_import": self._handle_string_import,
            }
            if self.action in action_map:
                action_map[self.action]()

        except Exception as e:
            error_info = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            self.failure.emit(f"알 수 없는 오류 발생:\n{error_info}")
        finally:
            self.finished.emit()

    def _handle_creation(self):
        result, message = self.adapter.create_session(self.session_name, self.phone_number, self._get_code_from_gui)
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

    def _get_code_from_gui(self, prompt_message):
        self.gui_input = None  # 이전 값 초기화
        self.request_code_from_gui.emit(prompt_message)
        while self.gui_input is None and self._is_running:
            QThread.msleep(100)  # 0.1초 대기
        return self.gui_input

    def set_gui_input(self, text):
        self.gui_input = text

    def stop(self):
        self._is_running = False
