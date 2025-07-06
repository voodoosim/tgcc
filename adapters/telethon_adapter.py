# adapters/telethon_adapter.py
import os

from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from ui.constants import SESSIONS_DIR


class TelethonAdapter:
    """Telethon 라이브러리를 위한 동기 방식 어댑터"""

    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash

    def _get_client(self, session_name):
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        return TelegramClient(session_path, self.api_id, self.api_hash)

    def create_session(self, session_name, phone_number, code_callback):
        client = self._get_client(session_name)
        try:
            with client:
                if not client.is_user_authorized():
                    client.send_code_request(phone_number)
                    code = code_callback("Telegram 인증 코드를 입력하세요:")
                    try:
                        client.sign_in(phone_number, code)
                    except SessionPasswordNeededError:
                        password = code_callback("2단계 인증 비밀번호를 입력하세요:")
                        client.sign_in(password=password)
            save_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
            return True, f"Telethon 세션 저장 완료: {save_path}"
        except Exception as e:
            return False, f"Telethon 오류: {e}"

    def check_session(self, session_name):
        client = self._get_client(session_name)
        try:
            with client:
                me = client.get_me()
                return True, f"세션 유효. 사용자: @{me.username}"
        except Exception as e:
            return False, f"세션 확인 오류: {e}"

    def export_session_string(self, session_name):
        client = self._get_client(session_name)
        try:
            with client:
                return StringSession.save(client.session)
        except Exception:
            return ""

    def import_session_from_string(self, session_name, session_string):
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        try:
            with TelegramClient(StringSession(session_string), self.api_id, self.api_hash) as client:
                client.session.set_filename(session_path)
                client.session.save()
            return True, f"문자열에서 세션을 '{session_path}'에 저장했습니다."
        except Exception as e:
            return False, f"문자열 가져오기 오류: {e}"
