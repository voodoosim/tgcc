# ui/main_window.py
import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config import Config
from ui.constants import (
    ADD_API_BUTTON,
    CHECK_SESSION_BUTTON,
    COPY_SESSION_STRING_BUTTON,
    CREATE_SESSION_BUTTON,
    IMPORT_STRING_BUTTON,
    LIBRARY_LABEL,
    LOG_AREA_TITLE,
    OPEN_SESSIONS_FOLDER_BUTTON,
    PHONE_PLACEHOLDER,
    REMOVE_API_BUTTON,
    SESSION_LIST_TITLE,
    SESSION_STRING_PLACEHOLDER,
    SESSIONS_DIR,
    TITLE,
    WINDOW_SIZE,
)
from ui.session_manager import SessionManager
from ui.styles import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.setGeometry(*WINDOW_SIZE)
        self.setStyleSheet(DARK_STYLE)

        self.config = Config()
        self.session_manager = SessionManager(self)

        self.init_ui()
        self.load_config()
        self.update_session_list()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ... (이하 UI 구성 코드는 이전과 동일하게 유지됩니다) ...
        top_controls_layout = QHBoxLayout()
        self.api_combo = QComboBox()
        self.api_combo.setToolTip("사용할 API ID/Hash 선택")
        top_controls_layout.addWidget(self.api_combo)
        self.add_api_button = QPushButton(ADD_API_BUTTON)
        self.add_api_button.clicked.connect(self.add_api)
        top_controls_layout.addWidget(self.add_api_button)
        self.remove_api_button = QPushButton(REMOVE_API_BUTTON)
        self.remove_api_button.clicked.connect(self.remove_api)
        top_controls_layout.addWidget(self.remove_api_button)
        top_controls_layout.addStretch()
        top_controls_layout.addWidget(QLabel(LIBRARY_LABEL))
        self.library_combo = QComboBox()
        self.library_combo.addItems(["Pyrogram", "Telethon"])
        self.library_combo.setToolTip("세션 생성에 사용할 라이브러리를 선택하세요.")
        top_controls_layout.addWidget(self.library_combo)
        main_layout.addLayout(top_controls_layout)
        splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(PHONE_PLACEHOLDER)
        left_layout.addWidget(self.phone_input)
        self.create_session_button = QPushButton(CREATE_SESSION_BUTTON)
        self.create_session_button.clicked.connect(self.create_session)
        left_layout.addWidget(self.create_session_button)
        left_layout.addStretch()
        self.session_string_input = QTextEdit()
        self.session_string_input.setPlaceholderText(SESSION_STRING_PLACEHOLDER)
        left_layout.addWidget(self.session_string_input)
        self.import_string_button = QPushButton(IMPORT_STRING_BUTTON)
        self.import_string_button.clicked.connect(self.import_from_string)
        left_layout.addWidget(self.import_string_button)
        splitter.addWidget(left_panel)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel(SESSION_LIST_TITLE))
        self.session_list_widget = QListWidget()
        self.session_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        right_layout.addWidget(self.session_list_widget)
        session_buttons_layout = QHBoxLayout()
        self.check_session_button = QPushButton(CHECK_SESSION_BUTTON)
        self.check_session_button.clicked.connect(self.check_session)
        session_buttons_layout.addWidget(self.check_session_button)
        self.open_folder_button = QPushButton(OPEN_SESSIONS_FOLDER_BUTTON)
        self.open_folder_button.clicked.connect(self.open_sessions_folder)
        session_buttons_layout.addWidget(self.open_folder_button)
        right_layout.addLayout(session_buttons_layout)
        splitter.addWidget(right_panel)
        main_layout.addWidget(splitter)
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(QLabel(LOG_AREA_TITLE))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        bottom_layout.addWidget(self.log_area)
        session_string_layout = QHBoxLayout()
        self.session_string_output = QLineEdit()
        self.session_string_output.setReadOnly(True)
        self.session_string_output.setPlaceholderText("성공 시 여기에 세션 문자열이 표시됩니다.")
        session_string_layout.addWidget(self.session_string_output)
        self.copy_button = QPushButton(COPY_SESSION_STRING_BUTTON)
        self.copy_button.clicked.connect(self.copy_session_string)
        session_string_layout.addWidget(self.copy_button)
        bottom_layout.addLayout(session_string_layout)
        splitter.setSizes([self.width() // 2, self.width() // 2])

    def load_apis(self):
        """API 목록을 콤보박스에 로드합니다."""
        self.api_combo.clear()
        credentials = self.config.get_api_credentials()
        if not credentials:
            self.api_combo.addItem("등록된 API 없음")
            return
        for cred in credentials:
            self.api_combo.addItem(f"{cred['name']} ({cred['api_id']})")

        last_api = self.config.get_last_used_api()
        if last_api:
            for i in range(self.api_combo.count()):
                if self.api_combo.itemText(i).startswith(last_api):
                    self.api_combo.setCurrentIndex(i)
                    break

    def load_config(self):
        """설정 파일에서 마지막 상태를 불러옵니다."""
        self.load_apis()
        last_library = self.config.get_last_used_library()
        index = self.library_combo.findText(last_library)
        if index >= 0:
            self.library_combo.setCurrentIndex(index)

    def save_config(self):
        """현재 상태를 설정 파일에 저장합니다."""
        nickname = None
        current_text = self.api_combo.currentText()
        if current_text and "등록된" not in current_text:
            nickname = current_text.split(" (")[0]
        library_name = self.library_combo.currentText()
        self.config.save_last_used(nickname, library_name)

    def get_selected_api(self):
        """콤보박스에서 선택된 API의 ID와 Hash를 반환합니다."""
        current_text = self.api_combo.currentText()
        if not current_text or "등록된" in current_text:
            return None, None
        nickname = current_text.split(" (")[0]
        for cred in self.config.get_api_credentials():
            if cred["name"] == nickname:
                return cred["api_id"], cred["api_hash"]
        return None, None

    def add_api(self):
        """사용자로부터 API 정보를 입력받아 추가합니다."""
        nickname, ok = QInputDialog.getText(self, "API 추가", "API 닉네임 (별명):")
        if not ok or not nickname.strip():
            return

        api_id, ok = QInputDialog.getText(self, "API 추가", f"'{nickname}'의 API ID:")
        if not ok or not api_id.strip():
            return

        api_hash, ok = QInputDialog.getText(self, "API 추가", f"'{nickname}'의 API Hash:")
        if not ok or not api_hash.strip():
            return

        if self.config.add_api_credential(nickname, api_id, api_hash):
            self.log(f"✅ API '{nickname}' 추가 완료.")
            self.load_apis()
        else:
            QMessageBox.warning(self, "오류", f"이미 '{nickname}'라는 이름의 API가 존재합니다.")

    def remove_api(self):
        """선택된 API를 설정에서 삭제합니다."""
        current_text = self.api_combo.currentText()
        if not current_text or "등록된" in current_text:
            QMessageBox.warning(self, "선택 오류", "삭제할 API를 목록에서 선택해주세요.")
            return

        nickname = current_text.split(" (")[0]
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"정말로 '{nickname}' API를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.config.remove_api_credential(nickname):
                self.log(f"🗑️ API '{nickname}' 삭제 완료.")
                self.load_apis()
            else:  # 혹시 모를 경우
                self.log(f"❌ API '{nickname}' 삭제 실패.", is_error=True)

    def get_selected_library(self):
        return self.library_combo.currentText()

    def create_session(self):
        api_id, api_hash = self.get_selected_api()
        if not api_id:
            QMessageBox.warning(self, "API 선택 필요", "먼저 API를 추가하거나 선택해주세요.")
            return
        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력해주세요.")
            return
        library = self.get_selected_library()
        self.session_manager.create_session(library, api_id, api_hash, phone)

    def check_session(self):
        selected = self.session_list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "선택 오류", "확인할 세션 파일을 목록에서 선택해주세요.")
            return
        api_id, api_hash = self.get_selected_api()
        if not api_id:
            QMessageBox.warning(self, "API 선택 필요", "세션을 확인하려면 API를 선택해야 합니다.")
            return
        self.session_manager.check_session(selected.text())

    def import_from_string(self):
        api_id, api_hash = self.get_selected_api()
        if not api_id:
            QMessageBox.warning(self, "API 선택 필요", "세션을 가져오려면 API를 선택해야 합니다.")
            return
        session_string = self.session_string_input.toPlainText().strip()
        if not session_string:
            QMessageBox.warning(self, "입력 오류", "세션 문자열을 입력해주세요.")
            return
        filename, ok = QInputDialog.getText(self, "파일 이름 지정", "저장할 파일 이름을 입력하세요 (확장자 제외):")
        if not ok or not filename.strip():
            return
        library = self.get_selected_library()
        self.session_manager.import_from_string(library, api_id, api_hash, session_string, filename)

    def update_session_list(self):
        self.session_list_widget.clear()
        try:
            files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
            self.session_list_widget.addItems(sorted(files))
        except FileNotFoundError:
            os.makedirs(SESSIONS_DIR)
            self.log(f"'{SESSIONS_DIR}' 폴더를 새로 만들었습니다.")

    def log(self, message, is_error=False):
        color = "#ff4757" if is_error else "white"
        self.log_area.append(f"<span style='color:{color};'>{message}</span>")

    def copy_session_string(self):
        text = self.session_string_output.text()
        if text:
            QApplication.clipboard().setText(text)
            self.log("📋 세션 문자열이 클립보드에 복사되었습니다.")
        else:
            self.log("복사할 세션 문자열이 없습니다.", is_error=True)

    def set_session_string(self, text):
        self.session_string_output.setText(text)

    def open_sessions_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(SESSIONS_DIR))

    def set_ui_enabled(self, enabled):
        status_text = "활성화" if enabled else "비활성화 (작업 처리 중...)"
        self.statusBar().showMessage(f"UI 상태: {status_text}")
        for widget in self.findChildren((QPushButton, QLineEdit, QComboBox, QTextEdit)):
            widget.setEnabled(enabled)
        QApplication.processEvents()

    def closeEvent(self, event):
        self.save_config()
        if self.session_manager.thread and self.session_manager.thread.isRunning():
            reply = QMessageBox.question(
                self,
                "작업 진행 중",
                "세션 작업이 아직 진행 중입니다. 정말로 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.session_manager.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
