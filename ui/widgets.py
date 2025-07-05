# ui/widgets.py
"""베로니카 커스텀 위젯"""
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation
from PyQt5.QtWidgets import QPushButton


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
