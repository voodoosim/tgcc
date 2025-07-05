import asyncio
import logging
from pathlib import Path
from typing import Dict, Union

import pyperclip
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QInputDialog,
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
    """Veronica 메인 GUI"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.adapters = {"telethon": TelethonAdapter(), "pyrogram": PyrogramAdapter()}
        self.setWindowTitle("Veronica - Telegram Session Manager")
        self.setGeometry(100, 100, 600, 400)
        self.setup_ui()

    def setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number (e.g., +1234567890)")
        layout.addWidget(self.phone_input)
        self.api_combo = QComboBox()
        self.load_api_credentials()
        layout.addWidget(self.api_combo)
        self.lib_combo = QComboBox()
        self.lib_combo.addItems(["telethon", "pyrogram"])
        layout.addWidget(self.lib_combo)
        self.create_btn = QPushButton("Create Session")
        self.create_btn.clicked.connect(self.create_session)
        layout.addWidget(self.create_btn)
        self.validate_btn = QPushButton("Validate Session")
        self.validate_btn.clicked.connect(self.validate_session)
        layout.addWidget(self.validate_btn)
        self.session_string = QLineEdit()
        self.session_string.setReadOnly(True)
        self.session_string.mousePressEvent = self.copy_session_string
        layout.addWidget(self.session_string)
        self.import_btn = QPushButton("Import Session String")
        self.import_btn.clicked.connect(self.import_session)
        layout.addWidget(self.import_btn)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def load_api_credentials(self):
        self.api_combo.clear()
        credentials = self.config.get_api_credentials()
        for cred in credentials:
            self.api_combo.addItem(f"{cred['name']} ({cred['api_id']})")

    def log(self, message: str, level: str = "INFO"):
        self.log_area.append(f"[{level}] {message}")

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
        library = self.lib_combo.currentText()
        adapter = self.adapters[library]
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
        code, ok = QInputDialog.getText(self, "Authentication Code", "Enter code:")
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
                f"Session created for {auth_result['phone']}", "SUCCESS"
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
        library = self.lib_combo.currentText()
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]
        worker = AsyncWorker(
            adapter.validate_session(
                session_file, int(api_cred["api_id"]), api_cred["api_hash"]
            )
        )
        worker.result.connect(
            lambda valid: self.log(
                "Session valid" if valid else "Session invalid", "INFO"
            )
        )
        worker.error.connect(lambda e: self.log(f"Validation failed: {e}", "ERROR"))
        worker.start()

    def copy_session_string(self, _a0: QMouseEvent):
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return
        library = self.lib_combo.currentText()
        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]
        try:
            session_string = adapter.session_to_string(session_file)
            self.session_string.setText(session_string)
            pyperclip.copy(session_string)
            self.log("Session string copied to clipboard", "INFO")
        except FileNotFoundError:
            self.log("Session file not found", "ERROR")
        except ValueError as e:
            self.log(f"Failed to copy session string: {e}", "ERROR")

    def import_session(self):
        string, ok = QInputDialog.getText(
            self, "Import Session", "Enter session string:"
        )
        if not ok or not string:
            self.log("Import cancelled", "WARNING")
            return
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Phone number required", "ERROR")
            return
        library = self.lib_combo.currentText()
        adapter = self.adapters[library]
        try:
            session_file = adapter.string_to_session(string, phone)
            self.log(f"Session imported to {session_file}", "SUCCESS")
        except ValueError as e:
            self.log(f"Import failed: {e}", "ERROR")
