#!/usr/bin/env python
"""중복 코드 자동 제거 스크립트 - 백업 없이 직접 수정"""
from pathlib import Path


def fix_telethon_adapter():
    """telethon_adapter.py 수정"""
    file_path = Path("adapters/telethon_adapter.py")
    
    print(f"📝 {file_path} 수정 중...")
    
    # 파일 읽기
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 수정할 내용
    old_imports = """from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError, UnauthorizedError
from telethon.tl.types import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def normalize_phone_number(phone: str) -> Optional[str]:
    \"\"\"
    전화번호를 정규화합니다.
    - 공백, 하이픈, 괄호 등 제거
    - + 기호는 유지
    - 숫자만 남김
    \"\"\"
    import re

    if not phone:
        return None

    # + 기호를 임시로 보관
    has_plus = phone.startswith("+")

    # 숫자만 추출
    digits = re.sub(r"[^\\d]", "", phone)

    if not digits:
        return None

    # + 기호 복원
    if has_plus:
        return "+" + digits

    return digits"""
    
    new_imports = """from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError, UnauthorizedError
from telethon.tl.types import User

from utils.phone import normalize_phone_number

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")"""
    
    # 내용 교체
    new_content = content.replace(old_imports, new_imports)
    
    # 파일 쓰기
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("✅ telethon_adapter.py 수정 완료")


def fix_pyrogram_adapter():
    """pyrogram_adapter.py 수정"""
    file_path = Path("adapters/pyrogram_adapter.py")
    
    print(f"📝 {file_path} 수정 중...")
    
    # 파일 읽기
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 수정할 내용
    old_imports = """from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, FloodWait, PhoneCodeInvalid

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def normalize_phone_number(phone: str) -> Optional[str]:
    \"\"\"
    전화번호를 정규화합니다.
    - 공백, 하이픈, 괄호 등 제거
    - + 기호는 유지
    - 숫자만 남김
    \"\"\"
    import re

    if not phone:
        return None

    # + 기호를 임시로 보관
    has_plus = phone.startswith("+")

    # 숫자만 추출
    digits = re.sub(r"[^\\d]", "", phone)

    if not digits:
        return None

    # + 기호 복원
    if has_plus:
        return "+" + digits

    return digits"""
    
    new_imports = """from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, FloodWait, PhoneCodeInvalid

from utils.phone import normalize_phone_number

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")"""
    
    # 내용 교체
    new_content = content.replace(old_imports, new_imports)
    
    # 파일 쓰기
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("✅ pyrogram_adapter.py 수정 완료")


def verify_imports():
    """수정 확인"""
    print("\n🔍 수정 확인 중...")
    
    try:
        # import 테스트
        print("  - Telethon 어댑터 import 테스트...", end="")
        from adapters.telethon_adapter import TelethonAdapter
        print(" ✅")
        
        print("  - Pyrogram 어댑터 import 테스트...", end="")
        from adapters.pyrogram_adapter import PyrogramAdapter
        print(" ✅")
        
        print("  - 전화번호 정규화 함수 테스트...", end="")
        from utils.phone import normalize_phone_number
        test_result = normalize_phone_number("+880 1234 5678")
        assert test_result == "+88012345678"
        print(" ✅")
        
        print("\n✨ 모든 수정이 성공적으로 완료되었습니다!")
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def main():
    print("🔧 베로니카 중복 코드 제거 스크립트\n")
    
    # Telethon 어댑터 수정
    fix_telethon_adapter()
    
    # Pyrogram 어댑터 수정
    fix_pyrogram_adapter()
    
    # 수정 확인
    print("="*50)
    if verify_imports():
        print("\n💡 다음 명령어로 프로그램을 실행해보세요:")
        print("   python run.py")
    else:
        print("\n⚠️ 수정 중 문제가 발생했습니다.")
        print("파일을 확인해주세요.")


if __name__ == "__main__":
    main()
