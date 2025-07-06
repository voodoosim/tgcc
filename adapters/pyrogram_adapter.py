# adapters/pyrogram_adapter.py
import os

# Pylance가 제안한 대로, 정확한 경로에서 Client를 가져옵니다.
from pyrogram.client import Client
from pyrogram.errors import SessionPasswordNeeded

from ui.constants import SESSIONS_DIR


class PyrogramAdapter:
    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.workdir = os.path.abspath(SESSIONS_DIR)

    def _get_client(self, session_name, session_string=None):
        if session_string:
            return Client(
                session_name,
                session_string=session_string,
                api_id=self.api_id,
                api_hash=self.api_hash,
                workdir=self.workdir,
            )
        return Client(session_name, api_id=self.api_id, api_hash=self.api_hash, workdir=self.workdir)

    def create_session(self, session_name, phone_number, password_callback, qr_callback=None):
        """세션을 생성하고 디스크에 저장합니다."""
        try:
            # with 문을 사용하여 클라이언트 연결을 안전하게 관리합니다.
            with self._get_client(session_name) as client:
                if not client.is_user_authorized():
                    sent_code_info = client.send_code(phone_number)
                    code = password_callback("Telegram에서 받은 인증 코드를 입력하세요:")
                    try:
                        client.sign_in(phone_number, sent_code_info.phone_code_hash, code)
                    except SessionPasswordNeeded:
                        password = password_callback("2단계 인증 비밀번호를 입력하세요:")
                        client.check_password(password)

            save_path = os.path.join(self.workdir, f"{session_name}.session")
            return True, f"Pyrogram 세션 저장 완료: {save_path}"
        except Exception as e:
            return False, f"Pyrogram 오류: {e}"

    def check_session(self, session_name):
        """세션 파일의 유효성을 확인합니다."""
        try:
            with self._get_client(session_name) as client:
                me = client.get_me()
                return True, f"세션 유효. 사용자: @{me.username}"
        except Exception as e:
            return False, f"세션 확인 오류: {e}"

    def export_session_string(self, session_name):
        """세션을 문자열로 내보냅니다."""
        # Pyrogram은 인스턴스 메서드로 세션 문자열 내보내기를 제공합니다.
        try:
            with self._get_client(session_name) as client:
                return client.export_session_string()
        except Exception:
            return ""

    def import_session_from_string(self, session_name, session_string):
        """세션 문자열로부터 .session 파일을 생성합니다."""
        try:
            with self._get_client(session_name, session_string=session_string) as client:
                me = client.get_me()  # 세션이 유효한지 테스트
            save_path = os.path.join(self.workdir, f"{session_name}.session")
            return True, f"문자열에서 세션을 '{save_path}'에 저장했습니다. (@{me.username})"
        except Exception as e:
            return False, f"문자열 가져오기 오류: {e}"

    def disconnect(self):
        pass  # 'with' 구문이 자동으로 연결을 관리
