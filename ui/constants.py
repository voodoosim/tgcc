# ui/constants.py
"""UI 상수 및 스타일 정의"""

# 다크 테마 스타일시트
DARK_STYLE = """
QMainWindow {
    background-color: #1a1a1a;
}

QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
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

QPushButton#deleteBtn {
    background-color: #f03e3e;
}

QPushButton#deleteBtn:hover {
    background-color: #c92a2a;
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
    font-family: 'D2Coding', 'Consolas', monospace;
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

# 로그 레벨별 색상
LOG_COLORS = {
    "INFO": "#5c7cfa",
    "SUCCESS": "#37b24d",
    "WARNING": "#f59f00",
    "ERROR": "#f03e3e"
}

# 로그 레벨별 아이콘
LOG_ICONS = {
    "INFO": "ℹ",
    "SUCCESS": "✓",
    "WARNING": "⚠",
    "ERROR": "✗"
}

# UI 텍스트
UI_TEXTS = {
    "TITLE": "⚡ VERONICA",
    "SUBTITLE": "텔레그램 세션 관리자",
    "PHONE_PLACEHOLDER": "📱 전화번호 입력 (예: +821012345678)",
    "CREATE_SESSION": "✨ 세션 생성",
    "VALIDATE_SESSION": "✓ 세션 확인",
    "IMPORT_SESSION": "📥 가져오기",
    "EXPORT_SESSION": "📤 내보내기",
    "MANAGE_API": "🔑 API 관리",
    "SESSION_STRING_PLACEHOLDER": "🔒 클릭하여 세션 문자열 복사",
    "ACTIVITY_LOG": "📋 활동 기록",
    "WELCOME_MSG": "Veronica에 오신 것을 환영합니다! 텔레그램 세션을 관리할 준비가 되었습니다.",
    "PHONE_REQUIRED": "전화번호를 입력해주세요",
    "API_REQUIRED": "API 자격 증명을 선택해주세요",
    "SESSION_EXISTS": "세션이 이미 존재합니다",
    "OVERWRITE_CONFIRM": "의 세션이 이미 존재합니다. 덮어쓰시겠습니까?",
    "AUTH_CODE_TITLE": "인증 코드",
    "AUTH_CODE_MSG": "텔레그램으로 전송된 코드를 입력하세요:",
    "AUTH_CANCELLED": "인증이 취소되었습니다",
    "SESSION_CREATED": "✨ 세션이 성공적으로 생성되었습니다: ",
    "SESSION_VALID": "✓ 세션이 유효하고 활성 상태입니다",
    "SESSION_INVALID": "✗ 세션이 유효하지 않거나 만료되었습니다",
    "SESSION_COPIED": "📋 세션 문자열이 클립보드에 복사되었습니다!",
    "SESSION_NOT_FOUND": "세션 파일을 찾을 수 없습니다",
    "IMPORT_TITLE": "세션 가져오기",
    "IMPORT_MSG": "세션 문자열을 붙여넣으세요:",
    "IMPORT_SUCCESS": "📥 세션을 성공적으로 가져왔습니다: ",
    "IMPORT_CANCELLED": "가져오기가 취소되었습니다",
    "CREATING_SESSION": "세션을 생성하는 중...",
    "VALIDATING_SESSION": "세션을 확인하는 중...",
    "API_NAME": "API 이름",
    "API_ID": "API ID",
    "API_HASH": "API Hash",
    "ADD_API": "추가",
    "DELETE_API": "삭제",
    "API_ADDED": "API 자격 증명이 추가되었습니다",
    "API_DELETED": "API 자격 증명이 삭제되었습니다",
    "API_EXISTS": "이미 존재하는 API 이름입니다",
    "SELECT_FILE": "파일 선택",
    "SESSION_FILES": "세션 파일 (*.session)",
    "LOAD_SESSION": "📂 세션 파일 열기",
    "SESSION_LOADED": "세션 파일을 불러왔습니다"
}
