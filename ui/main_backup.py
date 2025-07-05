import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, Union, Optional

import pyperclip
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from adapters.pyrogram_adapter import PyrogramAdapter
from adapters.telethon_adapter import TelethonAdapter
from core.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    전화번호를 정규화합니다.
    - 공백, 하이픈, 괄호 등 제거
    - + 기호는 유지
    - 숫자만 남김
    """
    if not phone:
        return None

    # + 기호를 임시로 보관
    has_plus = phone.startswith('+')

    # 숫자만 추출
    digits = re.sub(r'[^\d]', '', phone)

    if not digits:
        return None

    # + 기호 복원
    if has_plus:
        return '+' + digits

    return digits


def validate_phone_number(phone: str) -> bool:
    """
    전화번호 유효성 검사
    - 최소 7자리 이상
    - 숫자로만 구성 (+ 제외)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return False

    # + 제거하고 검사
    digits = normalized.lstrip('+')

    # 최소 7자리, 최대 15자리
    return digits.isdigit() and 7 <= len(digits) <= 15


# 다크 테마 스타일시트
DARK_STYLE = """
QMainWindow {
    background-color: #1a1a1a;
}

QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 14px;
}

QLineEdit {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    padding: 10px 15px;
    color: #ffffff;
    font-size: 14px;
    selection-background-color: #5c7cfa;
}

QLineEdit:focus {
    border-color: #5c7cfa;
    background-color: #333333;
}

QLineEdit:hover {
    border-color: #4d4d4d;
}

QLineEdit[readOnly="true"] {
    background-color: #252525;
    color: #888888;
}

QPushButton {
    background-color: #5c7cfa;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: bold;
    font-size: 14px;
    min-width: 120px;
}

QPushButton:hover {
    background-color: #4c6ef5;
}

QPushButton:pressed {
    background-color: #364fc7;
}

QPushButton:disabled {
    background-color: #3d3d3d;
    color: #666666;
}

QPushButton#validateBtn {
    background-color: #37b24d;
}

QPushButton#validateBtn:hover {
    background-color: #2f9e0f;
}

QPushButton#importBtn {
    background-color: #f59f00;
}

QPushButton#importBtn:hover {
    background-color: #e67700;
}

QPushButton#addApiBtn {
    background-color: #845ef7;
    min-width: 100px;
}

QPushButton#addApiBtn:hover {
    background-color: #7048e8;
}

QComboBox {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    padding: 10px 15px;
    color: #ffffff;
    font-size: 14px;
    min-width: 200px;
}

QComboBox:hover {
    border-color: #4d4d4d;
}

QComboBox:focus {
    border-color: #5c7cfa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #ffffff;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    selection-background-color: #5c7cfa;
    color: #ffffff;
    padding: 5px;
}

QTextEdit {
    background-color: #252525;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    padding: 10px;
    color: #ffffff;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}

QTextEdit:focus {
    border-color: #4d4d4d;
}

QMessageBox {
    background-color: #2d2d2d;
    color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

QInputDialog {
    background-color: #2d2d2d;
    color: #ffffff;
}

QInputDialog QLineEdit {
    background-color: #3d3d3d;
}

QLabel#titleLabel {
    font-size: 28px;
    font-weight: bold;
    color: #5c7cfa;
    padding: 20px 0px 10px 0px;
    background-color: transparent;
}

QLabel#subtitleLabel {
    font-size: 14px;
    color: #888888;
    padding-bottom: 20px;
    background-color: transparent;
}

QFrame#headerFrame {
    background-color: #1a1a1a;
    border-bottom: 2px solid #2d2d2d;
    padding: 10px;
}

/* 스크롤바 스타일 */
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4d4d4d;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5d5d5d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


class AnimatedButton(QPushButton):
    """애니메이션 효과가 있는 버튼"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(100)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        # 마우스 호버 시 살짝 커지는 효과
        self.animation.stop()
        current = self.geometry()
        self.animation.setStartValue(current)
        self.animation.setEndValue(current.adjusted(-2, -2, 2, 2))
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 마우스가 벗어날 때 원래 크기로
        self.animation.stop()
        current = self.geometry()
        self.animation.setStartValue(current)
        self.animation.setEndValue(current.adjusted(2, 2, -2, -2))
        self.animation.start()
        super().leaveEvent(event)


class AsyncWorker(QThread):
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro)
            self.result.emit(result)
        except (ValueError, RuntimeError) as e:
            self.error.emit(str(e))
        finally:
            loop.close()


class MainWindow(QMainWindow):
    """Veronica 메인 GUI - 다크 테마"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.adapters = {"telethon": TelethonAdapter(), "pyrogram": PyrogramAdapter()}
        self.setWindowTitle("🔐 베로니카 - 텔레그램 세션 관리자")
        self.setGeometry(100, 100, 800, 800)
        self.setStyleSheet(DARK_STYLE)
        self.setup_ui()

    def setup_ui(self):
        # 메인 위젯
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 헤더 프레임
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()

        # 타이틀
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

        main_layout.addWidget(header_frame)

        # 입력 섹션
        input_section = QVBoxLayout()
        input_section.setSpacing(12)

        # 전화번호 입력
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("📱 전화번호 입력 (예: +821012345678, +82 10 1234 5678)")
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

        main_layout.addLayout(input_section)

        # 버튼 섹션
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

        main_layout.addLayout(button_section)

        # 세션 문자열 표시
        self.session_string = QLineEdit()
        self.session_string.setReadOnly(True)
        self.session_string.setPlaceholderText("🔒 클릭하여 세션 문자열 복사")
        self.session_string.mousePressEvent = self.copy_session_string_event
        self.session_string.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.session_string)

        # 로그 영역
        log_label = QLabel("📋 활동 로그")
        log_label.setStyleSheet("color: #888888; font-weight: bold; padding: 5px 0;")
        main_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(350)  # 최소 높이 설정
        main_layout.addWidget(self.log_area)

        # 메인 위젯 설정
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 시작 메시지
        self.log("베로니카에 오신 것을 환영합니다! 텔레그램 세션 관리 준비가 완료되었습니다.", "INFO")

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
        name, ok = QInputDialog.getText(
            self, "API 자격증명 추가", "이 API의 이름을 입력하세요:"
        )
        if not ok or not name:
            return

        api_id, ok = QInputDialog.getText(
            self, "API 자격증명 추가", "API ID를 입력하세요:"
        )
        if not ok or not api_id:
            return

        api_hash, ok = QInputDialog.getText(
            self, "API 자격증명 추가", "API Hash를 입력하세요:"
        )
        if not ok or not api_hash:
            return

        # API 추가
        if self.config.add_api_credential(name, api_id, api_hash):
            self.log(f"✅ API '{name}'가 성공적으로 추가되었습니다", "SUCCESS")
            # 콤보박스 즉시 업데이트
            self.load_api_credentials()
            # 새로 추가된 항목 선택
            self.api_combo.setCurrentIndex(self.api_combo.count() - 1)
        else:
            self.log(f"API '{name}' 추가 실패 - 이름이 이미 존재할 수 있습니다", "ERROR")

    def log(self, message: str, level: str = "INFO"):
        colors = {
            "INFO": "#5c7cfa",
            "SUCCESS": "#37b24d",
            "WARNING": "#f59f00",
            "ERROR": "#f03e3e",
        }
        icons = {"INFO": "ℹ", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗"}
        color = colors.get(level, "#ffffff")
        icon = icons.get(level, "•")

        # 현재 시간 추가
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted_msg = f'<span style="color: #666666;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{icon} [{level}]</span> {message}'
        self.log_area.append(formatted_msg)

        # 자동 스크롤
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def create_session(self):
        phone = self.phone_input.text().strip()

        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone or not validate_phone_number(normalized_phone):
            self.log("잘못된 전화번호 형식입니다", "ERROR")
            self.log("예시: +821012345678, +82 10 1234 5678", "INFO")
            return
        phone = normalized_phone

        api_index = self.api_combo.currentIndex()
        credentials = self.config.get_api_credentials()
        if api_index < 0 or not credentials:
            self.log("API 자격증명을 추가하고 선택해주세요", "ERROR")
            return

        api_cred = credentials[api_index]
        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        adapter = self.adapters[library]

        self.log(f"{phone}에 대한 세션 생성 중... ({library} 사용)", "INFO")
        self.log(f"사용 API: {api_cred['name']} ({api_cred['api_id']})", "INFO")

        worker = AsyncWorker(
            adapter.create_session(phone, int(api_cred["api_id"]), api_cred["api_hash"])
        )
        worker.result.connect(
            lambda result: self.handle_create_session(result, phone, api_cred, library)
        )
        worker.error.connect(
            lambda e: self.log(f"세션 생성 실패: {e}", "ERROR")
        )
        worker.start()

    def handle_create_session(
        self,
        result: Dict[str, Union[str, bool]],
        phone: str,
        api_cred: Dict[str, str],
        library: str,
    ):
        if result.get("exists", False):
            reply = QMessageBox.question(
                self,
                "세션 존재",
                f"{phone}에 대한 세션이 이미 존재합니다. 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                self.log("세션 생성이 취소되었습니다", "WARNING")
                return

        code, ok = QInputDialog.getText(
            self, "인증 코드", "텔레그램으로 전송된 코드를 입력하세요:"
        )
        if not ok or not code:
            self.log("인증이 취소되었습니다", "WARNING")
            return

        adapter = self.adapters[library]
        worker = AsyncWorker(
            adapter.complete_auth(
                phone,
                int(api_cred["api_id"]),
                api_cred["api_hash"],
                code,
                result["phone_code_hash"],
            )
        )
        worker.result.connect(
            lambda auth_result: self.handle_auth_complete(auth_result, phone)
        )
        worker.error.connect(lambda e: self.log(f"인증 실패: {e}", "ERROR"))
        worker.start()

    def handle_auth_complete(self, auth_result: Dict[str, str], phone: str):
        """인증 완료 처리"""
        self.log("✨ 세션이 성공적으로 생성되었습니다!", "SUCCESS")
        self.log(f"사용자 ID: {auth_result['user_id']}", "INFO")
        self.log(f"사용자명: @{auth_result['username']}" if auth_result['username'] else "사용자명: 설정되지 않음", "INFO")
        self.log(f"전화번호: {auth_result['phone']}", "INFO")

    def validate_session(self):
        phone = self.phone_input.text().strip()

        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            self.log("잘못된 전화번호 형식입니다", "ERROR")
            return
        phone = normalized_phone

        api_index = self.api_combo.currentIndex()
        credentials = self.config.get_api_credentials()
        if api_index < 0 or not credentials:
            self.log("API 자격증명을 추가하고 선택해주세요", "ERROR")
            return

        api_cred = credentials[api_index]
        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]

        self.log(f"{phone}에 대한 세션 검증 중...", "INFO")
        self.log(f"파일 확인: {session_file}", "INFO")
        self.log(f"사용 API: {api_cred['name']} ({api_cred['api_id']})", "INFO")

        worker = AsyncWorker(
            adapter.validate_session(
                session_file, int(api_cred["api_id"]), api_cred["api_hash"]
            )
        )
        worker.result.connect(
            lambda valid: self.handle_validation_result(valid, phone, session_file)
        )
        worker.error.connect(lambda e: self.log(f"검증 실패: {e}", "ERROR"))
        worker.start()

    def handle_validation_result(self, valid: bool, phone: str, session_file: Path):
        """세션 검증 결과 처리"""
        if valid:
            self.log(f"✅ {phone}에 대한 세션이 유효하고 활성 상태입니다", "SUCCESS")
            self.log("이제 이 세션으로 텔레그램 작업을 수행할 수 있습니다", "INFO")
            self.log(f"세션 파일: {session_file}", "INFO")
        else:
            self.log(f"❌ {phone}에 대한 세션이 유효하지 않거나 만료되었습니다", "ERROR")
            self.log("세션 상태:", "WARNING")
            self.log("• 만료됨 (다른 기기에서 로그아웃)", "WARNING")
            self.log("• 잘못된 API 자격증명", "WARNING")
            self.log("• 손상된 세션 파일", "WARNING")
            self.log("새로운 세션을 생성해주세요", "INFO")

    def copy_session_string_event(self, event: QMouseEvent):
        """마우스 클릭 이벤트 핸들러"""
        self.copy_session_string()

    def copy_session_string(self):
        """세션 문자열을 클립보드에 복사"""
        phone = self.phone_input.text().strip()

        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            self.log("잘못된 전화번호 형식입니다", "ERROR")
            return
        phone = normalized_phone

        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]

        try:
            session_string = adapter.session_to_string(session_file)
            self.session_string.setText(session_string[:50] + "...")  # Show truncated
            pyperclip.copy(session_string)
            self.log("📋 세션 문자열이 클립보드에 복사되었습니다!", "SUCCESS")
            self.log(f"세션 대상: {phone}", "INFO")
        except FileNotFoundError:
            self.log(f"{phone}에 대한 세션 파일을 찾을 수 없습니다", "ERROR")
            self.log("먼저 세션을 생성해주세요", "INFO")
        except ValueError as e:
            self.log(f"세션 문자열 복사 실패: {e}", "ERROR")

    def import_session(self):
        string, ok = QInputDialog.getText(
            self, "세션 가져오기", "세션 문자열을 여기에 붙여넣으세요:"
        )
        if not ok or not string:
            self.log("가져오기가 취소되었습니다", "WARNING")
            return

        phone = self.phone_input.text().strip()

        # 전화번호 정규화
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            self.log("잘못된 전화번호 형식입니다", "ERROR")
            self.log("먼저 전화번호를 입력해주세요", "INFO")
            return
        phone = normalized_phone

        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        adapter = self.adapters[library]

        try:
            session_file = adapter.string_to_session(string, phone)
            self.log("📥 세션을 성공적으로 가져왔습니다!", "SUCCESS")
            self.log(f"저장 위치: {session_file}", "INFO")
            self.log("이제 세션을 검증하여 작동하는지 확인할 수 있습니다", "INFO")
        except ValueError as e:
            self.log(f"가져오기 실패: {e}", "ERROR")
            self.log("세션 문자열이 유효한지 확인해주세요", "INFO")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 모던한 스타일
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
