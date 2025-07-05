# ui/main_window.py
"""베로니카 메인 윈도우 - 간소화 버전"""
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config import Config
from ui.dialogs import DialogHelper
from ui.session_manager import SessionManager
from ui.styles import DARK_STYLE
from ui.widgets import AnimatedButton


class MainWindow(QMainWindow):
    """베로니카 메인 GUI"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.session_manager = SessionManager(self, self.log)
        self.setWindowTitle("🔐 베로니카 - 텔레그램 세션 관리자")
        self.setGeometry(100, 100, 900, 850)
        self.setStyleSheet(DARK_STYLE)
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 헤더
        main_layout.addWidget(self._create_header())

        # 입력 섹션
        main_layout.addLayout(self._create_input_section())

        # 버튼 섹션
        main_layout.addLayout(self._create_button_section())

        # 세션 문자열 표시
        self.session_string = self._create_session_string_field()
        # 클릭 이벤트를 위한 커스텀 위젯으로 래핑
        session_container = QWidget()
        session_layout = QHBoxLayout(session_container)
        session_layout.setContentsMargins(0, 0, 0, 0)
        session_layout.addWidget(self.session_string)
        session_container.mousePressEvent = lambda event: self.copy_session_string()
        main_layout.addWidget(session_container)

        # 로그 영역
        log_label = QLabel("📋 활동 로그")
        log_label.setStyleSheet("color: #888888; font-weight: bold; padding: 5px 0; font-size: 18px;")
        main_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(400)
        main_layout.addWidget(self.log_area)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 시작 메시지
        self.log("베로니카에 오신 것을 환영합니다! 텔레그램 세션 관리 준비가 완료되었습니다.", "INFO")

    def _create_header(self) -> QFrame:
        """헤더 프레임 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()

        title_label = QLabel("⚡ 베로니카")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("텔레그램 고급 세션 관리 프로그램")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_frame.setLayout(header_layout)

        # 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(92, 124, 250, 100))
        shadow.setOffset(0, 2)
        header_frame.setGraphicsEffect(shadow)

        return header_frame

    def _create_input_section(self) -> QVBoxLayout:
        """입력 섹션 생성"""
        input_section = QVBoxLayout()
        input_section.setSpacing(12)

        # 전화번호 입력
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("📱 전화번호 입력 (+880 1234 5678, 880-1234-5678, (880) 1234 5678 등)")
        input_section.addWidget(self.phone_input)

        # API 선택 및 추가 버튼
        api_layout = QHBoxLayout()
        self.api_combo = QComboBox()
        self.load_api_credentials()
        api_layout.addWidget(self.api_combo)

        self.add_api_btn = AnimatedButton("➕ API 추가")
        self.add_api_btn.setObjectName("addApiBtn")
        self.add_api_btn.clicked.connect(self.add_new_api)
        api_layout.addWidget(self.add_api_btn)

        input_section.addLayout(api_layout)

        # 라이브러리 선택
        self.lib_combo = QComboBox()
        self.lib_combo.addItems(["🔷 telethon", "🔶 pyrogram"])
        input_section.addWidget(self.lib_combo)

        return input_section

    def _create_button_section(self) -> QHBoxLayout:
        """버튼 섹션 생성"""
        button_section = QHBoxLayout()
        button_section.setSpacing(10)

        # 세션 생성 버튼
        self.create_btn = AnimatedButton("✨ 세션 생성")
        self.create_btn.clicked.connect(self.create_session)
        button_section.addWidget(self.create_btn)

        # 세션 검증 버튼
        self.validate_btn = AnimatedButton("✓ 검증")
        self.validate_btn.setObjectName("validateBtn")
        self.validate_btn.clicked.connect(self.validate_session)
        button_section.addWidget(self.validate_btn)

        # 세션 가져오기 버튼
        self.import_btn = AnimatedButton("📥 가져오기")
        self.import_btn.setObjectName("importBtn")
        self.import_btn.clicked.connect(self.import_session)
        button_section.addWidget(self.import_btn)

        # 세션 파일 불러오기 버튼
        self.load_file_btn = AnimatedButton("📂 파일 열기")
        self.load_file_btn.setObjectName("loadFileBtn")
        self.load_file_btn.clicked.connect(self.load_session_file)
        button_section.addWidget(self.load_file_btn)

        return button_section

    def _create_session_string_field(self) -> QLineEdit:
        """세션 문자열 필드 생성"""
        session_string = QLineEdit()
        session_string.setReadOnly(True)
        session_string.setPlaceholderText("🔒 클릭하여 세션 문자열 복사")
        # mousePressEvent를 재정의하는 대신 별도 메서드 사용
        session_string.setCursor(Qt.PointingHandCursor)
        return session_string

    def load_api_credentials(self):
        """API 자격증명을 콤보박스에 로드"""
        self.api_combo.clear()
        credentials = self.config.get_api_credentials()
        for cred in credentials:
            self.api_combo.addItem(f"🔑 {cred['name']} ({cred['api_id']})")

        if not credentials:
            self.api_combo.addItem("⚠️ API 자격증명 없음 - 'API 추가' 클릭")

    def add_new_api(self):
        """새 API 자격증명 추가"""
        credentials = DialogHelper.get_api_credentials(self)
        if not credentials:
            return

        name, api_id, api_hash = credentials
        if self.config.add_api_credential(name, api_id, api_hash):
            self.log(f"✅ API '{name}'가 성공적으로 추가되었습니다", "SUCCESS")
            self.load_api_credentials()
            self.api_combo.setCurrentIndex(self.api_combo.count() - 1)
        else:
            self.log(f"API '{name}' 추가 실패 - 이름이 이미 존재할 수 있습니다", "ERROR")

    def log(self, message: str, level: str = "INFO"):
        """로그 메시지 출력"""
        colors = {
            "INFO": "#5c7cfa",
            "SUCCESS": "#37b24d",
            "WARNING": "#f59f00",
            "ERROR": "#f03e3e",
        }
        icons = {"INFO": "ℹ", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗"}
        color = colors.get(level, "#ffffff")
        icon = icons.get(level, "•")

        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = (
            f'<span style="color: #666666;">[{timestamp}]</span> '
            f'<span style="color: {color}; font-weight: bold;">'
            f"{icon} [{level}]</span> {message}"
        )
        self.log_area.append(formatted_msg)

        # 자동 스크롤
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def create_session(self):
        """세션 생성"""
        phone = self.phone_input.text().strip()
        api_index = self.api_combo.currentIndex()
        library = self.lib_combo.currentText().split()[1]
        self.session_manager.create_session(phone, api_index, library)

    def validate_session(self):
        """세션 검증"""
        phone = self.phone_input.text().strip()
        api_index = self.api_combo.currentIndex()
        library = self.lib_combo.currentText().split()[1]
        self.session_manager.validate_session(phone, api_index, library)

    def copy_session_string(self):
        """세션 문자열 복사"""
        phone = self.phone_input.text().strip()
        library = self.lib_combo.currentText().split()[1]
        session_string = self.session_manager.copy_session_string(phone, library)
        if session_string:
            self.session_string.setText(session_string)

    def import_session(self):
        """세션 가져오기"""
        phone = self.phone_input.text().strip()
        library = self.lib_combo.currentText().split()[1]
        self.session_manager.import_session(phone, library)

    def load_session_file(self):
        """세션 파일 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(self, "세션 파일 선택", "", "세션 파일 (*.session);;모든 파일 (*.*)")

        if file_path:
            self.session_manager.load_session_file(file_path)

    def closeEvent(self, event):
        """프로그램 종료 시 정리 작업"""
        self.log("프로그램을 종료하는 중...", "INFO")

        # 모든 워커 정리
        self.session_manager.cleanup_workers()

        # 이벤트 수락
        event.accept()
