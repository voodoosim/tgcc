#!/usr/bin/env python
"""수정 확인 테스트 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """import 테스트"""
    print("🔍 Import 테스트 시작...\n")
    
    success = True
    
    # 1. utils.phone 모듈 테스트
    try:
        from utils.phone import normalize_phone_number
        print("✅ utils.phone.normalize_phone_number import 성공")
        
        # 함수 작동 테스트
        test_result = normalize_phone_number("+880 1234 5678")
        assert test_result == "+88012345678", f"Expected '+88012345678', got '{test_result}'"
        print("✅ normalize_phone_number 함수 작동 확인")
    except Exception as e:
        print(f"❌ utils.phone 테스트 실패: {e}")
        success = False
    
    # 2. Telethon 어댑터 테스트
    try:
        from adapters.telethon_adapter import TelethonAdapter
        print("✅ TelethonAdapter import 성공")
        
        # 객체 생성 테스트
        adapter = TelethonAdapter()
        print("✅ TelethonAdapter 객체 생성 성공")
    except Exception as e:
        print(f"❌ TelethonAdapter 테스트 실패: {e}")
        success = False
    
    # 3. Pyrogram 어댑터 테스트
    try:
        from adapters.pyrogram_adapter import PyrogramAdapter
        print("✅ PyrogramAdapter import 성공")
        
        # 객체 생성 테스트
        adapter = PyrogramAdapter()
        print("✅ PyrogramAdapter 객체 생성 성공")
    except Exception as e:
        print(f"❌ PyrogramAdapter 테스트 실패: {e}")
        success = False
    
    # 4. 어댑터에서 normalize_phone_number 사용 확인
    try:
        # 파일 내용 확인
        telethon_file = Path("adapters/telethon_adapter.py")
        pyrogram_file = Path("adapters/pyrogram_adapter.py")
        
        with open(telethon_file, "r", encoding="utf-8") as f:
            telethon_content = f.read()
        
        with open(pyrogram_file, "r", encoding="utf-8") as f:
            pyrogram_content = f.read()
        
        # import 문 확인
        assert "from utils.phone import normalize_phone_number" in telethon_content
        assert "from utils.phone import normalize_phone_number" in pyrogram_content
        
        # 중복 함수가 제거되었는지 확인
        assert "def normalize_phone_number" not in telethon_content
        assert "def normalize_phone_number" not in pyrogram_content
        
        print("✅ 중복 코드가 성공적으로 제거됨")
        print("✅ 올바른 import 문 확인")
    except Exception as e:
        print(f"❌ 파일 검증 실패: {e}")
        success = False
    
    return success


def test_phone_normalization():
    """전화번호 정규화 기능 테스트"""
    print("\n📱 전화번호 정규화 테스트...\n")
    
    from utils.phone import normalize_phone_number
    
    test_cases = [
        ("+880 1234 5678", "+88012345678"),
        ("880-1234-5678", "88012345678"),
        ("(880) 1234 5678", "88012345678"),
        ("+1 (234) 567-8900", "+12345678900"),
        ("01712345678", "01712345678"),
    ]
    
    all_passed = True
    for input_phone, expected in test_cases:
        result = normalize_phone_number(input_phone)
        if result == expected:
            print(f"✅ {input_phone} → {result}")
        else:
            print(f"❌ {input_phone} → {result} (expected: {expected})")
            all_passed = False
    
    return all_passed


def main():
    print("=" * 60)
    print("🔧 베로니카 수정 확인 테스트")
    print("=" * 60)
    
    # Import 테스트
    import_success = test_imports()
    
    # 기능 테스트
    phone_success = test_phone_normalization()
    
    print("\n" + "=" * 60)
    if import_success and phone_success:
        print("✨ 모든 테스트 통과! 수정이 성공적으로 완료되었습니다.")
        print("\n💡 이제 다음 명령어로 프로그램을 실행할 수 있습니다:")
        print("   python run.py")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 위의 오류를 확인하세요.")
    print("=" * 60)


if __name__ == "__main__":
    main()
