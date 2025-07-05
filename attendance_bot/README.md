# 📱 텔레그램 출석체크 봇

베로니카 프로젝트에 통합된 텔레그램 출석체크 봇입니다.

## ✨ 기능

- **출석체크**: `/출첵` 명령어로 하루 한 번 출석체크 (100포인트 지급)
- **통계 조회**: `/통계` 명령어로 개인 출석 통계 확인
- **리더보드**: `/순위` 명령어로 상위 10명 랭킹 확인
- **한국 시간 기준**: Asia/Seoul 타임존 사용으로 정확한 날짜 관리
- **중복 방지**: 하루에 한 번만 출석체크 가능

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 봇 토큰 설정

`.env` 파일을 생성하거나 환경변수로 설정:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
DB_PATH=attendance.db
```

### 3. 봇 실행

```bash
# 직접 실행
python attendance_bot/main.py

# 또는 전용 스크립트 사용
python run_attendance_bot.py
```

## 📋 사용법

### 봇 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 시작 및 환영 메시지 |
| `/help` | 도움말 보기 |
| `/출첵` | 출석체크하기 (1일 1회, 100포인트) |
| `/통계` | 개인 출석 통계 조회 |
| `/순위` | 리더보드 (Top 10) 조회 |

### 사용 예시

1. **첫 출석체크**
   ```
   사용자: /출첵
   봇: ✅ 출석체크 완료!
       👤 닉네임: 홍길동
       🎁 오늘 획득: 100포인트
       💰 총 포인트: 100포인트
       📅 총 출석: 1일
   ```

2. **중복 출석 시도**
   ```
   사용자: /출첵
   봇: ⚠️ 이미 출석체크를 완료했습니다!
       👤 닉네임: 홍길동
       💰 총 포인트: 100포인트
       내일 다시 출석체크해주세요! 😊
   ```

## 🏗️ 프로젝트 구조

```
attendance_bot/
├── __init__.py          # 패키지 초기화
├── main.py             # 메인 진입점
├── db.py               # SQLite 데이터베이스 관리
├── handlers.py         # 텔레그램 명령어 핸들러
└── utils.py            # 유틸리티 함수 (시간, 포인트)
```

## 🗄️ 데이터베이스 스키마

### attendance 테이블
- `id`: 자동 증가 기본키
- `user_id`: 텔레그램 사용자 ID (TEXT)
- `nickname`: 사용자 닉네임 (TEXT)
- `attendance_date`: 출석 날짜 (DATE)
- `points`: 획득 포인트 (INTEGER)
- `created_at`: 생성 시간 (TIMESTAMP)

### users 테이블
- `user_id`: 텔레그램 사용자 ID (TEXT, 기본키)
- `nickname`: 사용자 닉네임 (TEXT)
- `total_points`: 총 포인트 (INTEGER)
- `total_attendance`: 총 출석 횟수 (INTEGER)
- `first_attendance`: 첫 출석 날짜 (DATE)
- `last_attendance`: 마지막 출석 날짜 (DATE)
- `created_at`: 생성 시간 (TIMESTAMP)
- `updated_at`: 수정 시간 (TIMESTAMP)

## 🔧 환경 설정

### 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 (필수) | - |
| `DB_PATH` | SQLite 데이터베이스 파일 경로 | `attendance.db` |
| `WEBHOOK_URL` | 웹훅 URL (프로덕션 배포용) | - |
| `PORT` | 웹훅 포트 | `8443` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

### 프로덕션 배포

웹훅 모드로 실행하려면:

```bash
export WEBHOOK_URL=https://your-domain.com/webhook
export PORT=8443
python attendance_bot/main.py
```

## 🧪 테스트

```bash
# 데이터베이스 테스트
python -c "
from attendance_bot.db import AttendanceDB
db = AttendanceDB('test.db')
print('✅ Database test passed')
"

# 유틸리티 함수 테스트
python -c "
from attendance_bot.utils import get_korean_date_string
print(f'✅ Korean date: {get_korean_date_string()}')
"

# 패키지 임포트 테스트
python -c "
import attendance_bot
print('✅ Package import successful')
"
```

## 🔗 베로니카 GUI 통합

이 봇은 베로니카 프로젝트의 일부로 설계되었으며, 기존 GUI와 독립적으로 실행되거나 통합하여 사용할 수 있습니다.

### 통합 예시

```python
from attendance_bot import AttendanceBot, AttendanceDB

# GUI 애플리케이션에서 봇 상태 모니터링
db = AttendanceDB()
stats = db.get_top_users(5)  # 상위 5명 조회
```

## 📝 로그

봇 실행 로그는 `attendance_bot.log` 파일에 저장됩니다.

## 🛠️ 개발

### 코드 스타일
- PEP8 준수
- Type hints 사용
- Docstring 작성 (Google 스타일)

### 의존성
- `python-telegram-bot==20.8` - 텔레그램 봇 API
- `pytz==2024.1` - 시간대 처리
- `python-dotenv==1.0.0` - 환경변수 관리

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 등록해주세요.