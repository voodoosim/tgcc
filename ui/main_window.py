# ui/main_window.py
import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
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

from core.config_manager import ConfigManager
from ui.constants import (
    ADD_API_BUTTON,
    CHECK_SESSION_BUTTON,
    CONFIG_FILE,
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
from ui.styles import DARK_STYLESHEET


class MainWindow(QMainWindow):
    # 이 클래스의 내용은 이전과 동일합니다.
    # 코드가 너무 길어 생략하지만, 클래스 전체 내용은 변경되지 않았습니다.
    # 그냥 이전 지시사항에 있던 MainWindow 클래스 코드를 그대로 사용하시면 됩니다.
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.setGeometry(*WINDOW_SIZE)
        self.setStyleSheet(DARK_STYLESHEET)
        self.config_manager = ConfigManager(CONFIG_FILE)
        self.session_manager = SessionManager(self)
        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR)
        self.init_ui()
        self.load_config()
        self.update_session_list()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
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
        self.import_string_button.clicked.connect(self.import_session_from_string)
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

    def get_selected_api(self):
        current_text = self.api_combo.currentText()
        if not current_text or current_text == "등록된 API 없음":
            return None, None
        nickname = current_text.split(" (")[0]
        return self.config_manager.get_api_by_nickname(nickname)

    def get_selected_library(self):
        return self.library_combo.currentText()

    def create_session(self):
        api_id, api_hash = self.get_selected_api()
        if not api_id:
            QMessageBox.warning(self, "API 정보 없음", "먼저 API 정보를 추가해주세요.")
            return
        phone_number = self.phone_input.text().strip()
        if not phone_number:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력해주세요.")
            return
        library = self.get_selected_library()
        self.session_manager.create_session(library, api_id, api_hash, phone_number)

    def check_session(self):
        selected_items = self.session_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "확인할 세션 파일을 목록에서 선택해주세요.")
            return
        session_file = selected_items[0].text()
        self.session_manager.check_session(session_file)

    def import_session_from_string(self):
        session_string = self.session_string_input.toPlainText().strip()
        if not session_string:
            QMessageBox.warning(self, "입력 오류", "세션 문자열을 입력해주세요.")
            return
        phone_for_filename = self.phone_input.text().strip()
        if not phone_for_filename:
            tip = "(세션 파일 이름을 만들기 위한 전화번호 또는 별명을 입력해주세요)"
            QMessageBox.warning(self, "입력 오류", f"파일 이름이 필요합니다.\n{tip}")
            return
        api_id, api_hash = self.get_selected_api()
        if not api_id:
            QMessageBox.warning(self, "API 정보 없음", "먼저 API 정보를 추가해주세요.")
            return
        library = self.get_selected_library()
        self.session_manager.import_from_string(library, api_id, api_hash, session_string, phone_for_filename)

    def update_session_list(self):
        self.session_list_widget.clear()
        try:
            files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
            self.session_list_widget.addItems(files)
        except FileNotFoundError:
            self.log(f"'{SESSIONS_DIR}' 디렉토리를 찾을 수 없습니다. 새로 생성합니다.", is_error=True)
            os.makedirs(SESSIONS_DIR)

    def log(self, message, is_error=False):
        color = "red" if is_error else "white"
        self.log_area.append(f"<span style='color:{color};'>{message}</span>")

    def copy_session_string(self):
        text = self.session_string_output.text()
        if text:
            QApplication.clipboard().setText(text)
            self.log("세션 문자열이 클립보드에 복사되었습니다.")
        else:
            self.log("복사할 세션 문자열이 없습니다.", is_error=True)

    def set_session_string(self, text):
        self.session_string_output.setText(text)

    def add_api(self):
        self.config_manager.add_api_dialog(self)
        self.load_apis()

    def remove_api(self):
        current_text = self.api_combo.currentText()
        if not current_text or current_text == "등록된 API 없음":
            QMessageBox.warning(self, "선택 오류", "삭제할 API를 선택해주세요.")
            return
        nickname = current_text.split(" (")[0]
        self.config_manager.remove_api(nickname)
        self.load_apis()
        self.log(f"'{nickname}' API 정보가 삭제되었습니다.")

    def open_sessions_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(SESSIONS_DIR))

    def load_config(self):
        self.load_apis()
        config = self.config_manager.get_config()
        last_library = config.get("last_used_library")
        if last_library:
            index = self.library_combo.findText(last_library)
            if index != -1:
                self.library_combo.setCurrentIndex(index)

    def load_apis(self):
        self.api_combo.clear()
        apis = self.config_manager.get_apis()
        if not apis:
            self.api_combo.addItem("등록된 API 없음")
            return
        for nickname, data in apis.items():
            self.api_combo.addItem(f"{nickname} ({data['id']})")
        last_api = self.config_manager.get_config().get("last_used_api")
        if last_api and last_api in apis:
            index = self.api_combo.findText(f"{last_api} ({apis[last_api]['id']})")
            if index != -1:
                self.api_combo.setCurrentIndex(index)

    def save_config(self):
        current_text = self.api_combo.currentText()
        nickname = None
        if current_text and current_text != "등록된 API 없음":
            nickname = current_text.split(" (")[0]
        self.config_manager.save_config(
            {"last_used_api": nickname, "last_used_library": self.library_combo.currentText()}
        )

    def set_ui_enabled(self, enabled):
        for widget in self.findChildren(QPushButton):
            widget.setEnabled(enabled)
        for widget in self.findChildren(QLineEdit):
            widget.setEnabled(enabled)
        for widget in self.findChildren(QComboBox):
            widget.setEnabled(enabled)
        self.session_string_input.setEnabled(enabled)
        if not enabled:
            self.log("<i>작업 처리 중...</i>")
        QApplication.processEvents()

    def closeEvent(self, event):
        self.save_config()
        if self.session_manager.thread and self.session_manager.thread.isRunning():
            self.log("진행 중인 작업을 중단합니다...")
            self.session_manager.worker.stop()
            self.session_manager.thread.quit()
            self.session_manager.thread.wait()
        event.accept()
