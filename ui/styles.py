# ui/styles.py
"""베로니카 UI 스타일시트"""

DARK_STYLE = """
QMainWindow {
    background-color: #1a1a1a;
}

QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 16px;
}

QLineEdit {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 10px;
    padding: 15px 20px;
    color: #ffffff;
    font-size: 16px;
    selection-background-color: #5c7cfa;
    min-height: 30px;
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
    border-radius: 12px;
    padding: 18px 35px;
    font-weight: bold;
    font-size: 18px;
    min-width: 150px;
    min-height: 55px;
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
    min-width: 130px;
}

QPushButton#addApiBtn:hover {
    background-color: #7048e8;
}

QPushButton#loadFileBtn {
    background-color: #e64980;
}

QPushButton#loadFileBtn:hover {
    background-color: #c2255c;
}

QComboBox {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 10px;
    padding: 15px 20px;
    color: #ffffff;
    font-size: 16px;
    min-width: 250px;
    min-height: 30px;
}

QComboBox:hover {
    border-color: #4d4d4d;
}

QComboBox:focus {
    border-color: #5c7cfa;
}

QComboBox::drop-down {
    border: none;
    padding-right: 15px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid #ffffff;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
    selection-background-color: #5c7cfa;
    color: #ffffff;
    padding: 5px;
    font-size: 16px;
}

QTextEdit {
    background-color: #252525;
    border: 2px solid #3d3d3d;
    border-radius: 10px;
    padding: 15px;
    color: #ffffff;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 15px;
}

QTextEdit:focus {
    border-color: #4d4d4d;
}

QMessageBox {
    background-color: #2d2d2d;
    color: #ffffff;
    font-size: 16px;
}

QMessageBox QPushButton {
    min-width: 100px;
    padding: 10px 20px;
}

QInputDialog {
    background-color: #2d2d2d;
    color: #ffffff;
    font-size: 16px;
}

QInputDialog QLineEdit {
    background-color: #3d3d3d;
}

QLabel#titleLabel {
    font-size: 36px;
    font-weight: bold;
    color: #5c7cfa;
    padding: 25px 0px 15px 0px;
    background-color: transparent;
}

QLabel#subtitleLabel {
    font-size: 18px;
    color: #888888;
    padding-bottom: 25px;
    background-color: transparent;
}

QFrame#headerFrame {
    background-color: #1a1a1a;
    border-bottom: 2px solid #2d2d2d;
    padding: 15px;
}

/* 스크롤바 스타일 */
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #4d4d4d;
    border-radius: 7px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5d5d5d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
