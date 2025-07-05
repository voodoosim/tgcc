#!/usr/bin/env python
"""
베로니카 프로젝트 런처
프로젝트 루트에서 간단히 실행할 수 있도록 하는 런처 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ui.main 모듈 임포트 및 실행
if __name__ == "__main__":
    try:
        from ui.main import MainWindow, QApplication

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("\nPlease make sure you have installed all requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)
