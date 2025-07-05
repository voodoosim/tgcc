# ui/session_manager.py
"""세션 관리 비즈니스 로직"""
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pyperclip

from adapters.base_adapter import BaseAdapter
from adapters.pyrogram_adapter import PyrogramAdapter
from adapters.telethon_adapter import TelethonAdapter
from core.config import Config
from ui.async_worker import AsyncWorker
from ui.dialogs import DialogHelper
from utils.phone import format_phone_display, guess_country_from_number, normalize_phone_number, validate_phone_number

logger = logging.getLogger(__name__)


class SessionManager:
    """세션 관리 로직을 담당하는 클래스"""

    def __init__(self, parent, log_callback: Callable):
        self.parent = parent
        self.log = log_callback
        self.config = Config()
        self.adapters: Dict[str, BaseAdapter] = {"telethon": TelethonAdapter(), "pyrogram": PyrogramAdapter()}
        self.active_workers: List[AsyncWorker] = []

    def cleanup_workers(self):
        """모든 활성 워커 정리"""
        logger.info(f"활성 워커 정리 시작: {len(self.active_workers)}개")
        for worker in self.active_workers:
            if worker.isRunning():
                worker.stop()
        self.active_workers.clear()

    def get_normalized_phone(self, phone: str) -> Optional[str]:
        """전화번호 정규화 및 검증"""
        normalized = normalize_phone_number(phone)
        if not normalized:
            self.log("전화번호를 인식할 수 없습니다", "ERROR")
            self.log("지원 형식: +880 1234 5678, 880-1234-5678, (880) 1234 5678 등", "INFO")
            return None

        # 국가 정보 표시
        country = guess_country_from_number(normalized)
        if country:
            self.log(f"🌍 감지된 국가: {country}", "INFO")

        # 포맷팅된 형태로 표시
        formatted = format_phone_display(normalized)
        self.log(f"📱 정규화된 번호: {formatted}", "INFO")

        return normalized

    def get_current_api_credentials(self, api_index: int) -> Optional[Dict[str, str]]:
        """현재 선택된 API 자격증명 가져오기"""
        credentials = self.config.get_api_credentials()
        if api_index < 0 or not credentials:
            self.log("API 자격증명을 추가하고 선택해주세요", "ERROR")
            return None
        return credentials[api_index]

    def create_session(self, phone: str, api_index: int, library: str):
        """세션 생성"""
        # 전화번호 정규화
        normalized_phone = self.get_normalized_phone(phone)
        if not normalized_phone:
            # + 없이 입력된 경우 자동으로 추가 시도
            if phone and not phone.startswith("+"):
                # 방글라데시 번호 패턴 확인
                if phone.startswith("01") and len(phone) == 11:
                    # 방글라데시 로컬 번호
                    phone = "+880" + phone[1:]
                    self.log("🔄 방글라데시 번호로 자동 변환: " + phone, "INFO")
                elif phone.startswith("880"):
                    # 국가 코드는 있지만 + 없음
                    phone = "+" + phone
                    self.log("🔄 + 기호 자동 추가: " + phone, "INFO")
                elif len(phone) >= 10:
                    # 긴 번호인 경우 + 추가
                    phone = "+" + phone
                    self.log("🔄 국제 번호로 가정하여 + 추가: " + phone, "INFO")

                # 다시 정규화 시도
                normalized_phone = self.get_normalized_phone(phone)
                if not normalized_phone:
                    return
            else:
                return

        if not validate_phone_number(normalized_phone):
            self.log("전화번호가 너무 짧거나 깁니다 (4-15자리)", "ERROR")
            return
        phone = normalized_phone

        # API 자격증명 확인
        api_cred = self.get_current_api_credentials(api_index)
        if not api_cred:
            return

        adapter = self.adapters[library]
        self.log(f"{phone}에 대한 세션 생성 중... ({library} 사용)", "INFO")
        self.log(f"사용 API: {api_cred['name']} ({api_cred['api_id']})", "INFO")

        # 비동기 작업 시작
        self.cleanup_workers()  # 기존 워커 정리

        worker = AsyncWorker(adapter.create_session(phone, int(api_cred["api_id"]), api_cred["api_hash"]))

        worker.progress.connect(lambda msg: self.log(f"🔄 {msg}", "INFO"))
        worker.result.connect(lambda result: self._handle_create_session_result(result, phone, api_cred, library))
        worker.error.connect(lambda e: self.log(f"세션 생성 실패: {e}", "ERROR"))
        worker.finished.connect(lambda: self._remove_worker(worker))

        self.active_workers.append(worker)
        worker.start()

    def _handle_create_session_result(self, result: Any, phone: str, api_cred: Dict, library: str):
        """세션 생성 결과 처리"""
        # result가 dict인지 확인
        if not isinstance(result, dict):
            self.log("세션 생성 결과 형식 오류", "ERROR")
            return

        if result.get("exists", False):
            if not DialogHelper.ask_overwrite_session(self.parent, phone):
                self.log("세션 생성이 취소되었습니다", "WARNING")
                return

        code = DialogHelper.get_auth_code(self.parent)
        if not code:
            self.log("인증이 취소되었습니다", "WARNING")
            return

        adapter = self.adapters[library]
        worker = AsyncWorker(
            adapter.complete_auth(
                phone,
                int(api_cred["api_id"]),
                api_cred["api_hash"],
                code,
                result["phone_code_hash"],
            )
        )
        worker.result.connect(self._handle_auth_complete)
        worker.error.connect(lambda e: self.log(f"인증 실패: {e}", "ERROR"))
        worker.start()

    def _handle_auth_complete(self, auth_result: Any):
        """인증 완료 처리"""
        # auth_result가 dict인지 확인
        if not isinstance(auth_result, dict):
            self.log("인증 결과 형식 오류", "ERROR")
            return

        self.log("✨ 세션이 성공적으로 생성되었습니다!", "SUCCESS")
        self.log(f"사용자 ID: {auth_result.get('user_id', 'Unknown')}", "INFO")

        username = auth_result.get("username", "")
        if username:
            self.log(f"사용자명: @{username}", "INFO")
        else:
            self.log("사용자명: 설정되지 않음", "INFO")

        self.log(f"전화번호: {auth_result.get('phone', 'Unknown')}", "INFO")

    def validate_session(self, phone: str, api_index: int, library: str):
        """세션 검증"""
        normalized_phone = self.get_normalized_phone(phone)
        if not normalized_phone:
            return
        phone = normalized_phone

        api_cred = self.get_current_api_credentials(api_index)
        if not api_cred:
            return

        # 전화번호에서 가능한 파일명 패턴들 생성
        phone_digits = phone.lstrip("+")
        possible_files = [
            f"{phone}.session",
            f"{phone_digits}.session",
            f"+{phone_digits}.session",
            f"{phone.replace('+', '')}.session",  # + 없는 버전
        ]

        # 국가 코드가 880인 경우 추가 패턴
        if phone_digits.startswith("880"):
            # 880 제거한 버전도 시도
            local_number = phone_digits[3:]
            possible_files.extend(
                [
                    f"{local_number}.session",
                    f"0{local_number}.session",  # 0으로 시작하는 로컬 번호
                ]
            )

        # sessions 디렉토리의 모든 파일 확인
        sessions_dir = Path("sessions")
        session_file = None

        if sessions_dir.exists():
            for file_name in possible_files:
                test_file = sessions_dir / file_name
                if test_file.exists():
                    session_file = test_file
                    break

            # 부분 일치 검색
            if not session_file:
                for file in sessions_dir.glob("*.session"):
                    if phone_digits in file.stem or phone_digits[-4:] in file.stem:
                        session_file = file
                        self.log(f"📁 부분 일치 파일 발견: {file.name}", "INFO")
                        break

        if not session_file:
            self.log(f"❌ {phone}에 대한 세션 파일을 찾을 수 없습니다", "ERROR")
            self.log("사용 가능한 세션 파일:", "INFO")
            if sessions_dir.exists():
                for file in sessions_dir.glob("*.session"):
                    self.log(f"  • {file.name}", "INFO")
            return

        adapter = self.adapters[library]

        self.log("📍 세션 검증 시작", "INFO")
        self.log(f"📱 전화번호: {phone}", "INFO")
        self.log(f"📁 세션 파일: {session_file.name}", "INFO")
        self.log(f"🔧 라이브러리: {library}", "INFO")
        self.log(f"🔑 API: {api_cred['name']} (ID: {api_cred['api_id']})", "INFO")

        # 기존 워커 정리
        self.cleanup_workers()

        worker = AsyncWorker(adapter.validate_session(session_file, int(api_cred["api_id"]), api_cred["api_hash"]))

        # 진행 상황 연결
        worker.progress.connect(lambda msg: self.log(f"🔄 {msg}", "INFO"))

        # 결과 처리
        worker.result.connect(lambda result: self._handle_validation_result(result, phone, session_file))

        # 에러 처리
        def handle_error(error_msg):
            self.log(f"❌ 검증 실패: {error_msg}", "ERROR")
            if "SSL" in error_msg or "cryptg" in error_msg:
                self.log("💡 SSL/암호화 라이브러리 경고는 무시해도 됩니다", "INFO")
            # 워커 제거
            if worker in self.active_workers:
                self.active_workers.remove(worker)

        worker.error.connect(handle_error)

        # 완료 시 워커 제거
        worker.finished.connect(lambda: self._remove_worker(worker))

        # 워커 추가 및 시작
        self.active_workers.append(worker)
        worker.start()

        self.log("🔄 검증 작업이 백그라운드에서 실행 중입니다...", "INFO")

    def _remove_worker(self, worker: AsyncWorker):
        """완료된 워커 제거"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            logger.info(f"워커 제거됨. 남은 워커: {len(self.active_workers)}개")

    def _handle_validation_result(self, result: Any, phone: str, session_file: Path):
        """세션 검증 결과 처리"""
        # result가 bool인 경우와 dict인 경우 모두 처리
        if isinstance(result, bool):
            valid = result
        elif isinstance(result, dict):
            valid = result.get("valid", False)
        else:
            valid = False

        if valid:
            self.log(f"✅ {phone}에 대한 세션이 유효하고 활성 상태입니다", "SUCCESS")
            self.log("이제 이 세션으로 텔레그램 작업을 수행할 수 있습니다", "INFO")
            self.log(f"세션 파일: {session_file}", "INFO")
        else:
            self.log(f"❌ {phone}에 대한 세션이 유효하지 않거나 만료되었습니다", "ERROR")
            self.log("세션 상태:", "WARNING")
            self.log("• 만료됨 (다른 기기에서 로그아웃)", "WARNING")
            self.log("• 잘못된 API 자격증명", "WARNING")
            self.log("• 손상된 세션 파일", "WARNING")
            self.log("새로운 세션을 생성해주세요", "INFO")

    def copy_session_string(self, phone: str, library: str) -> str:
        """세션 문자열 복사"""
        normalized_phone = self.get_normalized_phone(phone)
        if not normalized_phone:
            return ""
        phone = normalized_phone

        session_file = Path(f"sessions/{phone.lstrip('+')}.session")
        adapter = self.adapters[library]

        try:
            session_string = adapter.session_to_string(session_file)
            pyperclip.copy(session_string)
            self.log("📋 세션 문자열이 클립보드에 복사되었습니다!", "SUCCESS")
            self.log(f"세션 대상: {phone}", "INFO")
            return session_string[:50] + "..."
        except FileNotFoundError:
            self.log(f"{phone}에 대한 세션 파일을 찾을 수 없습니다", "ERROR")
            self.log("먼저 세션을 생성해주세요", "INFO")
            return ""
        except ValueError as e:
            self.log(f"세션 문자열 복사 실패: {e}", "ERROR")
            return ""

    def import_session(self, phone: str, library: str):
        """세션 가져오기"""
        session_string = DialogHelper.get_session_string(self.parent)
        if not session_string:
            self.log("가져오기가 취소되었습니다", "WARNING")
            return

        normalized_phone = self.get_normalized_phone(phone)
        if not normalized_phone:
            self.log("먼저 전화번호를 입력해주세요", "INFO")
            return
        phone = normalized_phone

        adapter = self.adapters[library]

        try:
            session_file = adapter.string_to_session(session_string, phone)
            self.log("📥 세션을 성공적으로 가져왔습니다!", "SUCCESS")
            self.log(f"저장 위치: {session_file}", "INFO")
            self.log("이제 세션을 검증하여 작동하는지 확인할 수 있습니다", "INFO")
        except ValueError as e:
            self.log(f"가져오기 실패: {e}", "ERROR")
            self.log("세션 문자열이 유효한지 확인해주세요", "INFO")

    def load_session_file(self, file_path: str):
        """세션 파일 직접 불러오기"""
        import os
        import shutil

        try:
            # 파일명에서 전화번호 추출
            file_name = os.path.basename(file_path)
            phone_part = file_name.replace(".session", "")

            # 전화번호 형식 정리
            # (1), (2) 등의 중복 표시 제거
            phone_part = phone_part.split("(")[0]

            # + 기호 처리
            if not phone_part.startswith("+"):
                # 880으로 시작하면 방글라데시 국가코드
                if phone_part.startswith("880"):
                    phone_part = "+" + phone_part
                # 4자리 숫자만 있으면 전체 번호가 아닐 수 있음
                elif len(phone_part) <= 4:
                    self.log(f"⚠️ 파일명 '{file_name}'에서 완전한 전화번호를 추출할 수 없습니다", "WARNING")
                    self.log("전화번호를 직접 입력해주세요", "INFO")
                else:
                    phone_part = "+" + phone_part

            # sessions 디렉토리 경로
            sessions_dir = Path("sessions")
            sessions_dir.mkdir(exist_ok=True)

            # 대상 경로
            dest_path = sessions_dir / file_name
            source_path = Path(file_path).resolve()
            dest_path_resolved = dest_path.resolve()

            # 같은 파일인지 확인
            if source_path == dest_path_resolved:
                self.log("📂 이미 sessions 폴더에 있는 파일입니다", "INFO")
                self.log(f"전화번호: {phone_part}", "INFO")
                self.log("전화번호를 입력하고 '검증' 버튼을 눌러 확인하세요", "INFO")

                # 전화번호 자동 입력 시도
                if hasattr(self.parent, "phone_input") and len(phone_part) > 4:
                    self.parent.phone_input.setText(phone_part)
                    self.log(f"✅ 전화번호가 자동으로 입력되었습니다: {phone_part}", "SUCCESS")
            else:
                # 파일이 이미 존재하는지 확인
                if dest_path.exists():
                    self.log(f"⚠️ 동일한 이름의 파일이 이미 존재합니다: {file_name}", "WARNING")
                    # 새로운 이름으로 저장
                    counter = 1
                    while True:
                        new_name = f"{phone_part}_{counter}.session"
                        new_dest = sessions_dir / new_name
                        if not new_dest.exists():
                            dest_path = new_dest
                            break
                        counter += 1

                # 파일 복사
                shutil.copy2(file_path, dest_path)

                self.log("📂 세션 파일을 성공적으로 불러왔습니다!", "SUCCESS")
                self.log(f"원본 위치: {file_path}", "INFO")
                self.log(f"저장 위치: {dest_path}", "INFO")
                self.log(f"추정된 전화번호: {phone_part}", "INFO")

                # 전화번호 자동 입력
                if hasattr(self.parent, "phone_input") and len(phone_part) > 4:
                    self.parent.phone_input.setText(phone_part)
                    self.log(f"✅ 전화번호가 자동으로 입력되었습니다: {phone_part}", "SUCCESS")
                else:
                    self.log("전화번호 입력란에 번호를 입력하고 '검증' 버튼을 눌러 확인하세요", "INFO")

        except Exception as e:
            self.log(f"세션 파일 불러오기 실패: {e}", "ERROR")
