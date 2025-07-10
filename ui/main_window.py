# ui/main_window.py
import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
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

        # API 및 라이브러리 선택 영역
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

        # 메인 분할 영역
        splitter = QSplitter(Qt.Horizontal)

        # 왼쪽 패널 - 세션 생성 및 가져오기
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 전화번호 입력 및 세션 생성
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(PHONE_PLACEHOLDER)
        left_layout.addWidget(self.phone_input)

        self.create_session_button = QPushButton(CREATE_SESSION_BUTTON)
        self.create_session_button.clicked.connect(self.create_session)
        left_layout.addWidget(self.create_session_button)

        left_layout.addWidget(QLabel("─" * 20))

        # 세션 파일 불러오기 (새로운 기능)
        load_session_layout = QHBoxLayout()
        self.load_session_button = QPushButton("📂 세션 파일 불러오기")
        self.load_session_button.clicked.connect(self.load_session_file)
        self.load_session_button.setToolTip("기존 .session 파일을 불러와서 사용합니다")
        load_session_layout.addWidget(self.load_session_button)
        left_layout.addLayout(load_session_layout)

        left_layout.addStretch()

        # 세션 문자열 가져오기
        self.session_string_input = QTextEdit()
        self.session_string_input.setPlaceholderText(SESSION_STRING_PLACEHOLDER)
        left_layout.addWidget(self.session_string_input)

        self.import_string_button = QPushButton(IMPORT_STRING_BUTTON)
        self.import_string_button.clicked.connect(self.import_from_string)
        left_layout.addWidget(self.import_string_button)

        splitter.addWidget(left_panel)

        # 오른쪽 패널 - 세션 목록 및 관리
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel(SESSION_LIST_TITLE))

        self.session_list_widget = QListWidget()
        self.session_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        right_layout.addWidget(self.session_list_widget)

        # 세션 관리 버튼들
        session_buttons_layout = QVBoxLayout()
        
        # 첫 번째 줄: 확인, 폴더 열기
        session_buttons_row1 = QHBoxLayout()
        self.check_session_button = QPushButton(CHECK_SESSION_BUTTON)
        self.check_session_button.clicked.connect(self.check_session)
        session_buttons_row1.addWidget(self.check_session_button)

        self.open_folder_button = QPushButton(OPEN_SESSIONS_FOLDER_BUTTON)
        self.open_folder_button.clicked.connect(self.open_sessions_folder)
        session_buttons_row1.addWidget(self.open_folder_button)
        session_buttons_layout.addLayout(session_buttons_row1)

        # 두 번째 줄: 삭제, 내보내기 (새로운 기능)
        session_buttons_row2 = QHBoxLayout()
        self.delete_session_button = QPushButton("🗑️ 세션 삭제")
        self.delete_session_button.clicked.connect(self.delete_session)
        self.delete_session_button.setToolTip("선택된 세션 파일을 안전하게 삭제합니다")
        self.delete_session_button.setStyleSheet("QPushButton { background-color: #e74c3c; }")
        session_buttons_row2.addWidget(self.delete_session_button)

        self.export_session_button = QPushButton("📤 세션 내보내기")
        self.export_session_button.clicked.connect(self.export_session)
        self.export_session_button.setToolTip("선택된 세션을 다른 위치로 복사합니다")
        session_buttons_row2.addWidget(self.export_session_button)
        session_buttons_layout.addLayout(session_buttons_row2)

        right_layout.addLayout(session_buttons_layout)
        splitter.addWidget(right_panel)

        main_layout.addWidget(splitter)

        # 하단 영역 - 로그 및 세션 문자열 출력
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(QLabel(LOG_AREA_TITLE))

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        bottom_layout.addWidget(self.log_area)

        # 세션 문자열 출력 및 복사
        session_string_layout = QHBoxLayout()
        self.session_string_output = QLineEdit()
        self.session_string_output.setReadOnly(True)
        self.session_string_output.setPlaceholderText("성공 시 여기에 세션 문자열이 표시됩니다.")
        session_string_layout.addWidget(self.session_string_output)

        self.copy_button = QPushButton(COPY_SESSION_STRING_BUTTON)
        self.copy_button.clicked.connect(self.copy_session_string)
        session_string_layout.addWidget(self.copy_button)

        bottom_layout.addLayout(session_string_layout)
        main_layout.addLayout(bottom_layout)

        # 분할 크기 설정
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
            else:
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

    def load_session_file(self):
        """기존 세션 파일을 불러와서 sessions 폴더로 복사하는 새로운 기능"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "세션 파일 선택",
            "",
            "Session files (*.session);;All files (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            import shutil
            filename = os.path.basename(file_path)
            destination = os.path.join(SESSIONS_DIR, filename)
            
            # 같은 이름의 파일이 있으면 확인
            if os.path.exists(destination):
                reply = QMessageBox.question(
                    self,
                    "파일 덮어쓰기",
                    f"'{filename}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # 폴더가 없으면 생성
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            
            # 파일 복사
            shutil.copy2(file_path, destination)
            
            # 세션 목록 업데이트
            self.update_session_list()
            
            self.log(f"📂 세션 파일 '{filename}'을 성공적으로 불러왔습니다.")
            
            # 불러온 파일을 목록에서 자동 선택
            items = self.session_list_widget.findItems(filename, Qt.MatchExactly)
            if items:
                self.session_list_widget.setCurrentItem(items[0])
                
        except Exception as e:
            self.log(f"❌ 세션 파일 불러오기 실패: {e}", is_error=True)
            QMessageBox.critical(self, "오류", f"세션 파일을 불러오는 중 오류가 발생했습니다:\n{e}")

    def delete_session(self):
        """선택된 세션 파일을 안전하게 삭제하는 새로운 기능"""
        selected = self.session_list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "선택 오류", "삭제할 세션 파일을 목록에서 선택해주세요.")
            return
            
        session_file = selected.text()
        session_path = os.path.join(SESSIONS_DIR, session_file)
        
        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "세션 삭제 확인",
            f"정말로 '{session_file}' 세션을 삭제하시겠습니까?\n\n"
            "⚠️ 이 작업은 되돌릴 수 없습니다!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            # 보안 모듈의 안전한 삭제 기능 사용
            from core.security import ConfigEncryption
            from pathlib import Path
            
            encryption = ConfigEncryption()
            encryption.secure_delete(Path(session_path))
            
            # 세션 목록 업데이트
            self.update_session_list()
            
            self.log(f"🗑️ 세션 파일 '{session_file}'을 안전하게 삭제했습니다.")
            
        except Exception as e:
            self.log(f"❌ 세션 삭제 실패: {e}", is_error=True)
            QMessageBox.critical(self, "오류", f"세션 파일을 삭제하는 중 오류가 발생했습니다:\n{e}")

    def export_session(self):
        """선택된 세션 파일을 다른 위치로 내보내는 새로운 기능"""
        selected = self.session_list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "선택 오류", "내보낼 세션 파일을 목록에서 선택해주세요.")
            return
            
        session_file = selected.text()
        session_path = os.path.join(SESSIONS_DIR, session_file)
        
        if not os.path.exists(session_path):
            QMessageBox.warning(self, "파일 오류", f"세션 파일 '{session_file}'을 찾을 수 없습니다.")
            return
            
        # 저장 위치 선택
        file_dialog = QFileDialog()
        save_path, _ = file_dialog.getSaveFileName(
            self,
            "세션 파일 내보내기",
            session_file,
            "Session files (*.session);;All files (*.*)"
        )
        
        if not save_path:
            return
            
        try:
            import shutil
            shutil.copy2(session_path, save_path)
            
            self.log(f"📤 세션 파일 '{session_file}'을 '{save_path}'로 내보냈습니다.")
            
        except Exception as e:
            self.log(f"❌ 세션 내보내기 실패: {e}", is_error=True)
            QMessageBox.critical(self, "오류", f"세션 파일을 내보내는 중 오류가 발생했습니다:\n{e}")

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
