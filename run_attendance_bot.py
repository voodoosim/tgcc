#!/usr/bin/env python3
"""
텔레그램 출석체크 봇 실행 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from attendance_bot.main import main
        import asyncio
        
        print("🤖 베로니카 텔레그램 출석체크 봇 시작...")
        print("📋 봇을 중지하려면 Ctrl+C를 누르세요.")
        print("🔧 TELEGRAM_BOT_TOKEN 환경변수가 설정되어 있는지 확인하세요.")
        print("")
        
        asyncio.run(main())
        
    except ImportError as e:
        print(f"❌ 모듈 import 오류: {e}")
        print("\n필요한 패키지를 설치해주세요:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 봇이 안전하게 종료되었습니다.")
    except Exception as e:
        print(f"❌ 봇 실행 오류: {e}")
        sys.exit(1)