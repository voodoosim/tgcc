# run.py
import os
import sys

from PyQt5.QtWidgets import QApplication

# ------------------- 모든 import 오류 해결의 핵심 -------------------
# 프로그램 시작 시, 프로젝트 최상위 폴더('tgcc')를 파이썬 경로에 추가합니다.
# 이렇게 하면 어떤 하위 폴더에서든 'core', 'ui', 'adapters'를 항상 찾을 수 있습니다.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# --------------------------------------------------------------------

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
