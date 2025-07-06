# adapters/pyrogram_adapter.py
import os

from pyrogram.client import Client
from pyrogram.errors import SessionPasswordNeeded

from ui.constants import SESSIONS_DIR


class PyrogramAdapter:
    """Pyrogram 라이브러리를 위한 동기 방식 어댑터"""

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

    def create_session(self, session_name, phone_number, code_callback):
        try:
            with self._get_client(session_name) as client:
                sent_code_info = client.send_code(phone_number)
                code = code_callback("Telegram 인증 코드를 입력하세요:")
                try:
                    client.sign_in(phone_number, sent_code_info.phone_code_hash, code)
                except SessionPasswordNeeded:
                    password = code_callback("2단계 인증 비밀번호를 입력하세요:")
                    client.check_password(password)
            save_path = os.path.join(self.workdir, f"{session_name}.session")
            return True, f"Pyrogram 세션 저장 완료: {save_path}"
        except Exception as e:
            return False, f"Pyrogram 오류: {e}"

    def check_session(self, session_name):
        try:
            with self._get_client(session_name) as client:
                me = client.get_me()
                return True, f"세션 유효. 사용자: @{me.username}"
        except Exception as e:
            return False, f"세션 확인 오류: {e}"

    def export_session_string(self, session_name):
        try:
            with self._get_client(session_name) as client:
                return client.export_session_string()
        except Exception:
            return ""

    def import_session_from_string(self, session_name, session_string):
        try:
            with self._get_client(session_name, session_string=session_string) as client:
                me = client.get_me()
            save_path = os.path.join(self.workdir, f"{session_name}.session")
            return True, f"문자열에서 세션을 '{save_path}'에 저장했습니다. (@{me.username})"
        except Exception as e:
            return False, f"문자열 가져오기 오류: {e}"
