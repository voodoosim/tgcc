# 텔레그램 출석체크 봇

베로니카 프로젝트에 추가된 텔레그램 출석체크 봇 기능입니다.

## 🎯 기능

- **일일 출석체크**: `/출첵` 명령어로 하루 한 번 출석 기록
- **포인트 시스템**: 출석체크 시 100포인트 지급
- **중복 방지**: 같은 날짜에 중복 출석 불가
- **한국 시간 기준**: Asia/Seoul 시간대 사용
- **통계 조회**: 개인 포인트 및 출석 현황 확인
- **순위 시스템**: 포인트 기준 리더보드

## 🚀 사용법

### 1. 봇 토큰 설정
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 봇 실행
```bash
# 방법 1: 직접 실행
python attendance_bot/main.py

# 방법 2: 런처 스크립트 사용
python run_attendance_bot.py
```

## 📋 명령어

- `/start` - 봇 시작 및 환영 메시지
- `/출첵` - 일일 출석체크 (100포인트 획득)
- `/내정보` - 내 포인트 및 출석 현황 조회
- `/순위` - 포인트 순위 조회 (TOP 10)
- `/도움말` - 명령어 도움말

## 🗂️ 파일 구조

```
attendance_bot/
├── __init__.py       # 패키지 초기화
├── main.py          # 봇 실행 진입점
├── db.py            # SQLite 데이터베이스 모델
├── handlers.py      # 텔레그램 명령어 핸들러
└── utils.py         # 시간 및 포인트 유틸리티

data/
└── attendance.db    # SQLite 데이터베이스 파일 (자동 생성)
```

## 🧪 테스트

데이터베이스 및 유틸리티 기능 테스트:
```bash
python -c "
from attendance_bot.db import AttendanceDB
from attendance_bot.utils import get_korean_date
db = AttendanceDB('test.db')
print('✅ 데이터베이스 초기화 성공')
korean_time, date_str = get_korean_date()
print(f'📅 현재 한국 날짜: {date_str}')
"
```

## 🔧 환경 설정

### 환경 변수
- `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰 (필수)

### 데이터베이스
- SQLite 데이터베이스가 `data/attendance.db`에 자동 생성됩니다
- 데이터베이스 테이블은 첫 실행 시 자동으로 생성됩니다

## 📊 데이터베이스 스키마

### attendance 테이블
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    nickname TEXT NOT NULL,
    attendance_date DATE NOT NULL,
    points_earned INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, attendance_date)
);
```

### user_points 테이블
```sql
CREATE TABLE user_points (
    user_id INTEGER PRIMARY KEY,
    nickname TEXT NOT NULL,
    total_points INTEGER DEFAULT 0,
    attendance_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛡️ 보안 및 오류 처리

- 모든 데이터베이스 작업에 try-except 블록 적용
- SQL 인젝션 방지를 위한 파라미터화된 쿼리 사용
- 사용자 입력 데이터 유효성 검증
- 상세한 로깅 시스템

## 📝 로그

봇 실행 로그는 `attendance_bot.log` 파일에 저장됩니다.

## 🤝 기여

이 프로젝트는 베로니카 프로젝트의 일부입니다. 기여하실 때는 기존 코드 스타일을 따라주세요.

## 📄 라이선스

베로니카 프로젝트와 동일한 라이선스를 따릅니다.