# run.py - 통합 버전
"""
베로니카 프로그램 실행 파일
두 파일(run.py, ui/main.py)의 장점을 결합
"""
import logging
import os
import sys
import warnings

# 1. 경로 설정 (중요! import 오류 방지)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 2. 경고 필터 (SSL 등 불필요한 경고 숨김)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*SSL.*")

# 3. 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG 레벨로 변경하여 더 자세한 로그 출력
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("veronica.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# 외부 라이브러리 로그 레벨 조정
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("pyrogram.crypto").setLevel(logging.ERROR)
logging.getLogger("pyrogram.session").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# PyQt5 import
from PyQt5.QtWidgets import QApplication  # noqa: E402

# 메인 윈도우 import
from ui.main_window import MainWindow  # noqa: E402


def main():
    """메인 실행 함수"""
    # 애플리케이션 생성
    app = QApplication(sys.argv)

    # 스타일 설정 (모던한 Fusion 스타일)
    app.setStyle("Fusion")

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 시작 로그
    logging.info("베로니카 프로그램 시작")

    # 이벤트 루프 실행
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
