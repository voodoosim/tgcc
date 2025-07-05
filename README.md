# TGCC - 베로니카 프로젝트

텔레그램 계정 관리 및 출석체크 봇을 포함한 종합 프로젝트

## ✨ 주요 기능

### 📱 텔레그램 세션 관리 (베로니카 GUI)
- 다중 계정 세션 생성 및 관리
- Pyrogram 및 Telethon 라이브러리 지원
- 세션 유효성 검증 및 백업/복원

### 🤖 출석체크 봇 (NEW!)
- 텔레그램 봇으로 일일 출석체크 시스템
- 포인트 시스템 (1일 1회, 100포인트)
- 한국시간(KST) 기준 날짜 관리
- 개인 통계 및 리더보드 기능

## 🚀 시작하기

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 베로니카 GUI 실행
```bash
python ui/main.py
```

### 출석체크 봇 실행
```bash
python attendance_bot/main.py
# 또는
python run_attendance_bot.py
```

## 📖 자세한 문서

- [출석체크 봇 가이드](attendance_bot/README.md)
- [베로니카 GUI 사용법](ui/)

## 🎮 데모

출석체크 봇 기능을 테스트해보려면:
```bash
python demo_attendance_bot.py
```
