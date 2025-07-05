import asyncio
import logging
from pathlib import Path
from typing import Dict, Union

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
        self.setWindowTitle("🔐 Veronica - Telegram Session Manager")
        self.setGeometry(100, 100, 700, 600)
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
        title_label = QLabel("⚡ VERONICA")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Advanced Telegram Session Manager")
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
        self.phone_input.setPlaceholderText("📱 Enter phone number (e.g., +1234567890)")
        input_section.addWidget(self.phone_input)

        # API 선택
        self.api_combo = QComboBox()
        self.load_api_credentials()
        input_section.addWidget(self.api_combo)

        # 라이브러리 선택
        self.lib_combo = QComboBox()
        self.lib_combo.addItems(["🔷 telethon", "🔶 pyrogram"])
        input_section.addWidget(self.lib_combo)

        main_layout.addLayout(input_section)

        # 버튼 섹션
        button_section = QHBoxLayout()
        button_section.setSpacing(10)

        # 세션 생성 버튼
        self.create_btn = AnimatedButton("✨ Create Session")
        self.create_btn.clicked.connect(self.create_session)
        button_section.addWidget(self.create_btn)

        # 세션 검증 버튼
        self.validate_btn = AnimatedButton("✓ Validate")
        self.validate_btn.setObjectName("validateBtn")
        self.validate_btn.clicked.connect(self.validate_session)
        button_section.addWidget(self.validate_btn)

        # 세션 가져오기 버튼
        self.import_btn = AnimatedButton("📥 Import")
        self.import_btn.setObjectName("importBtn")
        self.import_btn.clicked.connect(self.import_session)
        button_section.addWidget(self.import_btn)

        main_layout.addLayout(button_section)

        # 세션 문자열 표시
        self.session_string = QLineEdit()
        self.session_string.setReadOnly(True)
        self.session_string.setPlaceholderText("🔒 Click here to copy session string")
        self.session_string.mousePressEvent = self.copy_session_string_event
        self.session_string.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.session_string)

        # 로그 영역
        log_label = QLabel("📋 Activity Log")
        log_label.setStyleSheet("color: #888888; font-weight: bold; padding: 5px 0;")
        main_layout.addWidget(log_label)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        main_layout.addWidget(self.log_area)

        # 메인 위젯 설정
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 시작 메시지
        self.log("Welcome to Veronica! Ready to manage your Telegram sessions.", "INFO")

    def load_api_credentials(self):
        self.api_combo.clear()
        credentials = self.config.get_api_credentials()
        for cred in credentials:
            self.api_combo.addItem(f"🔑 {cred['name']} ({cred['api_id']})")

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

        formatted_msg = f'<span style="color: {color}; font-weight: bold;">{icon} [{level}]</span> {message}'
        self.log_area.append(formatted_msg)

    def create_session(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return

        api_index = self.api_combo.currentIndex()
        if api_index < 0:
            self.log("Select API credentials", "ERROR")
            return

        api_cred = self.config.get_api_credentials()[api_index]
        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        adapter = self.adapters[library]

        self.log(f"Creating session for {phone}...", "INFO")

        worker = AsyncWorker(
            adapter.create_session(phone, int(api_cred["api_id"]), api_cred["api_hash"])
        )
        worker.result.connect(
            lambda result: self.handle_create_session(result, phone, api_cred, library)
        )
        worker.error.connect(
            lambda e: self.log(f"Session creation failed: {e}", "ERROR")
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
                "Session Exists",
                f"Session for {phone} already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                self.log("Session creation cancelled", "WARNING")
                return

        code, ok = QInputDialog.getText(
            self, "Authentication Code", "Enter the code sent to your Telegram:"
        )
        if not ok or not code:
            self.log("Authentication cancelled", "WARNING")
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
            lambda auth_result: self.log(
                f"✨ Session created successfully for {auth_result['phone']}", "SUCCESS"
            )
        )
        worker.error.connect(lambda e: self.log(f"Authentication failed: {e}", "ERROR"))
        worker.start()

    def validate_session(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return

        api_index = self.api_combo.currentIndex()
        if api_index < 0:
            self.log("Select API credentials", "ERROR")
            return

        api_cred = self.config.get_api_credentials()[api_index]
        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]

        self.log(f"Validating session for {phone}...", "INFO")

        worker = AsyncWorker(
            adapter.validate_session(
                session_file, int(api_cred["api_id"]), api_cred["api_hash"]
            )
        )
        worker.result.connect(
            lambda valid: self.log(
                (
                    "✓ Session is valid and active"
                    if valid
                    else "✗ Session is invalid or expired"
                ),
                "SUCCESS" if valid else "ERROR",
            )
        )
        worker.error.connect(lambda e: self.log(f"Validation failed: {e}", "ERROR"))
        worker.start()

    def copy_session_string_event(self, event: QMouseEvent):
        """마우스 클릭 이벤트 핸들러"""
        self.copy_session_string()

    def copy_session_string(self):
        """세션 문자열을 클립보드에 복사"""
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return

        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]

        try:
            session_string = adapter.session_to_string(session_file)
            self.session_string.setText(session_string[:50] + "...")  # Show truncated
            pyperclip.copy(session_string)
            self.log("📋 Session string copied to clipboard!", "SUCCESS")
        except FileNotFoundError:
            self.log("Session file not found", "ERROR")
        except ValueError as e:
            self.log(f"Failed to copy session string: {e}", "ERROR")

    def import_session(self):
        string, ok = QInputDialog.getText(
            self, "Import Session", "Paste your session string here:"
        )
        if not ok or not string:
            self.log("Import cancelled", "WARNING")
            return

        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return

        library = self.lib_combo.currentText().split()[1]  # Remove emoji
        adapter = self.adapters[library]

        try:
            session_file = adapter.string_to_session(string, phone)
            self.log(f"📥 Session imported successfully to {session_file}", "SUCCESS")
        except ValueError as e:
            self.log(f"Import failed: {e}", "ERROR")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 모던한 스타일
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
