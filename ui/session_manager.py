# ui/session_manager.py
import os

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QInputDialog, QMessageBox

from ui.constants import SESSIONS_DIR
from ui.worker import Worker


class SessionManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.thread = None
        self.worker = None

    def _start_task(self, library, api_id, api_hash, phone, session_name, action, session_string=None):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self.main_window, "경고", "이미 작업이 진행 중입니다.")
            return

        self.main_window.set_ui_enabled(False)
        self.main_window.log(f"'{session_name}'에 대한 '{action}' 작업을 시작합니다...")

        # 파일 이름으로 사용할 수 없는 문자 제거
        sanitized_name = "".join(c for c in session_name if c.isalnum())
        full_path = os.path.join(SESSIONS_DIR, f"{sanitized_name}.session")

        if action in ["create", "string_import"] and os.path.exists(full_path):
            reply = QMessageBox.question(
                self.main_window,
                "파일 덮어쓰기",
                f"'{sanitized_name}.session' 파일이 이미 존재합니다. 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                self.main_window.log("작업이 사용자에 의해 취소되었습니다.")
                self.main_window.set_ui_enabled(True)
                return

        self.thread = QThread()
        self.worker = Worker(library, api_id, api_hash, phone, sanitized_name, action, session_string)
        self.worker.moveToThread(self.thread)

        # Worker의 시그널과 SessionManager의 슬롯 연결
        self.worker.success.connect(self.on_success)
        self.worker.failure.connect(self.on_failure)
        self.worker.finished.connect(self.on_finished)
        self.worker.request_code_from_gui.connect(self.prompt_for_code)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def create_session(self, library, api_id, api_hash, phone_number):
        self._start_task(library, api_id, api_hash, phone_number, phone_number, "create")

    def check_session(self, session_file):
        library = self.main_window.get_selected_library()
        api_id, api_hash = self.main_window.get_selected_api()
        session_name = session_file.replace(".session", "")
        self._start_task(library, api_id, api_hash, "", session_name, "check")

    def import_from_string(self, library, api_id, api_hash, session_string, filename):
        self._start_task(library, api_id, api_hash, "", filename, "string_import", session_string)

    def prompt_for_code(self, prompt_message):
        text, ok = QInputDialog.getText(self.main_window, "입력 필요", prompt_message)
        if ok and text:
            self.worker.set_gui_input(text)
        else:
            self.worker.set_gui_input(None)  # 사용자가 취소한 경우
            self.worker.stop()

    def on_success(self, session_string, message):
        self.main_window.log(f"✅ 성공: {message}")
        QMessageBox.information(self.main_window, "성공", message)
        self.main_window.set_session_string(session_string)
        self.main_window.update_session_list()

    def on_failure(self, error_message):
        self.main_window.log(f"❌ 오류: {error_message}", is_error=True)
        QMessageBox.critical(self.main_window, "오류", error_message)

    def on_finished(self):
        self.main_window.set_ui_enabled(True)
        self.main_window.log("작업이 완료되었습니다.")
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
