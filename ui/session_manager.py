# ui/session_manager.py
import os
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLabel
from PyQt5.QtGui import QPixmap, QImage
import qrcode
from ui.worker import Worker
from ui.constants import SESSIONS_DIR

class SessionManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.thread = None
        self.worker = None

    def _start_task(self, library, api_id, api_hash, phone_number, session_name, action, session_string=None):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self.main_window, "경고", "이미 작업이 진행 중입니다.")
            return

        self.main_window.set_ui_enabled(False)
        self.main_window.log(f"'{session_name}' 세션에 대한 '{action}' 작업을 시작합니다...")

        # Sanitize phone number for filename
        sanitized_phone = ''.join(filter(str.isalnum, phone_number))
        if not sanitized_phone:
            final_session_name = session_name
        else:
            final_session_name = f"{sanitized_phone}.session"

        full_path = os.path.join(SESSIONS_DIR, final_session_name)

        if action in ['create', 'string_import'] and os.path.exists(full_path):
             reply = QMessageBox.question(self.main_window, '파일 덮어쓰기',
                                         f"'{final_session_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
             if reply == QMessageBox.No:
                 self.main_window.log("작업이 사용자에 의해 취소되었습니다.")
                 self.main_window.set_ui_enabled(True)
                 return

        self.thread = QThread()
        self.worker = Worker(library, api_id, api_hash, phone_number, final_session_name, action, session_string)
        self.worker.moveToThread(self.thread)

        self.worker.success.connect(self.on_success)
        self.worker.failure.connect(self.on_failure)
        self.worker.finished.connect(self.on_finished)
        self.worker.request_2fa.connect(self.request_2fa_password)
        self.worker.request_qr_login.connect(self.show_qr_code)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def create_session(self, library, api_id, api_hash, phone_number):
        self._start_task(library, api_id, api_hash, phone_number, phone_number, 'create')

    def check_session(self, session_file):
        library = self.main_window.get_selected_library()
        api_id, api_hash = self.main_window.get_selected_api()
        self._start_task(library, api_id, api_hash, "", session_file, 'check')

    def import_from_string(self, library, api_id, api_hash, session_string, phone_for_filename):
        self._start_task(library, api_id, api_hash, phone_for_filename, phone_for_filename, 'string_import', session_string)


    def on_success(self, session_string, message):
        self.main_window.log(f"성공: {message}")
        QMessageBox.information(self.main_window, "성공", message)
        self.main_window.set_session_string(session_string)
        self.main_window.update_session_list()

    def on_failure(self, error_message):
        self.main_window.log(f"오류: {error_message}", is_error=True)
        QMessageBox.critical(self.main_window, "오류", error_message)

    def on_finished(self):
        self.main_window.set_ui_enabled(True)
        self.main_window.log("작업이 완료되었습니다.")
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None

    def request_2fa_password(self):
        password, ok = QInputDialog.getText(self.main_window, "2단계 인증", "2단계 인증 비밀번호를 입력하세요:")
        if ok and password:
            self.worker.set_2fa_password(password)
        else:
            self.main_window.log("2단계 인증이 취소되었습니다. 작업을 중단합니다.", is_error=True)
            self.worker.stop()
            self.on_failure("2단계 인증 비밀번호가 제공되지 않았습니다.")


    def show_qr_code(self, qr_link):
        self.main_window.log("QR 코드를 스캔하여 로그인하세요...")
        qr_dialog = QMessageBox(self.main_window)
        qr_dialog.setWindowTitle("QR 코드로 로그인")
        qr_dialog.setText("텔레그램 모바일 앱을 열고 이 QR 코드를 스캔하세요.\n설정 > 기기 > 데스크톱 기기 연결")
        
        img = qrcode.make(qr_link)
        qt_img = QImage(img.convert("RGBA").tobytes(), img.size[0], img.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qt_img)
        
        icon_label = QLabel()
        icon_label.setPixmap(pixmap.scaledToWidth(256))
        qr_dialog.setIconPixmap(pixmap.scaledToWidth(64)) # For older systems
        qr_dialog.layout().addWidget(icon_label, 0, 0, 1, 2)
        qr_dialog.exec_()
