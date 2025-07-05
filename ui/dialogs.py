# ui/dialogs.py
"""베로니카 대화상자 헬퍼 함수"""
from typing import Optional, Tuple

from PyQt5.QtWidgets import QInputDialog, QMessageBox, QWidget


class DialogHelper:
    """대화상자 헬퍼 클래스"""

    @staticmethod
    def get_api_credentials(parent: QWidget) -> Optional[Tuple[str, str, str]]:
        """API 자격증명을 입력받는 대화상자"""
        name, ok = QInputDialog.getText(parent, "API 자격증명 추가", "이 API의 이름을 입력하세요:")
        if not ok or not name:
            return None

        api_id, ok = QInputDialog.getText(parent, "API 자격증명 추가", "API ID를 입력하세요:")
        if not ok or not api_id:
            return None

        api_hash, ok = QInputDialog.getText(parent, "API 자격증명 추가", "API Hash를 입력하세요:")
        if not ok or not api_hash:
            return None

        return name, api_id, api_hash

    @staticmethod
    def get_auth_code(parent: QWidget) -> Optional[str]:
        """인증 코드를 입력받는 대화상자"""
        code, ok = QInputDialog.getText(parent, "인증 코드", "텔레그램으로 전송된 코드를 입력하세요:")
        return code if ok and code else None

    @staticmethod
    def get_session_string(parent: QWidget) -> Optional[str]:
        """세션 문자열을 입력받는 대화상자"""
        string, ok = QInputDialog.getText(parent, "세션 가져오기", "세션 문자열을 여기에 붙여넣으세요:")
        return string if ok and string else None

    @staticmethod
    def ask_overwrite_session(parent: QWidget, phone: str) -> bool:
        """세션 덮어쓰기 확인 대화상자"""
        reply = QMessageBox.question(
            parent,
            "세션 존재",
            f"{phone}에 대한 세션이 이미 존재합니다. 덮어쓰시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        return reply == QMessageBox.Yes
