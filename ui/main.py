def setup_ui(self):
    widget = QWidget()
    layout = QVBoxLayout()
    self.phone_input = QLineEdit()
    self.phone_input.setPlaceholderText("Enter phone number (e.g., +1234567890)")
    layout.addWidget(self.phone_input)

    # 기존 코드에서 mousePressEvent 할당 방식 변경
    self.session_string = QLineEdit()
    self.session_string.setReadOnly(True)

    # 이벤트 핸들러를 메서드로 정의
    self.session_string.mousePressEvent = self.copy_session_string_event

    layout.addWidget(self.session_string)

    # 나머지 코드 동일


def copy_session_string_event(self, event: QMouseEvent):
    """마우스 클릭 이벤트 핸들러"""
    self.copy_session_string()
