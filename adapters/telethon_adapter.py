# adapters/telethon_adapter.py
import os

from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from ui.constants import SESSIONS_DIR


class TelethonAdapter:
    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash

    def _get_client(self, session_name):
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        # Telethon.sync에서 가져온 TelegramClient는 동기적으로 작동합니다.
        return TelegramClient(session_path, self.api_id, self.api_hash)

    def create_session(self, session_name, phone_number, password_callback, qr_callback=None):
        """세션을 생성하고 디스크에 저장합니다."""
        # 'qr_callback'은 Pyrogram과의 호환성을 위해 존재하며, 여기서는 사용되지 않습니다.
        client = self._get_client(session_name)
        try:
            # 동기 클라이언트는 명시적인 connect/disconnect가 with 문으로 관리됩니다.
            with client:
                if not client.is_user_authorized():
                    client.send_code_request(phone_number)
                    # GUI 앱에서는 input()을 사용할 수 없으므로, 이 부분은 GUI에서 처리해야 합니다.
                    # 여기서는 개념 증명을 위해 남겨둡니다. 실제로는 UI에서 코드를 받아야 합니다.
                    code = password_callback("Telegram에서 받은 인증 코드를 입력하세요:")
                    try:
                        client.sign_in(phone_number, code)
                    except SessionPasswordNeededError:
                        password = password_callback("2단계 인증 비밀번호를 입력하세요:")
                        client.sign_in(password=password)

            save_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
            return True, f"Telethon 세션 저장 완료: {save_path}"
        except Exception as e:
            return False, f"Telethon 오류: {e}"

    def check_session(self, session_name):
        """세션 파일의 유효성을 확인합니다."""
        client = self._get_client(session_name)
        try:
            with client:
                me = client.get_me()
                if me:
                    return True, f"세션 유효. 사용자: @{me.username}"
            return False, "세션이 유효하지 않습니다."
        except Exception as e:
            return False, f"세션 확인 오류: {e}"

    def export_session_string(self, session_name):
        """세션을 문자열로 내보냅니다."""
        client = self._get_client(session_name)
        try:
            with client:
                return StringSession.save(client.session)
        except Exception:
            return ""

    def import_session_from_string(self, session_name, session_string):
        """세션 문자열로부터 .session 파일을 생성합니다."""
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        try:
            # 문자열로 임시 클라이언트를 만들고, 그 세션을 파일로 저장합니다.
            with TelegramClient(StringSession(session_string), self.api_id, self.api_hash) as client:
                # 파일 이름을 명시적으로 지정하고 저장
                client.session.set_filename(session_path)
                client.session.save()
            return True, f"문자열에서 세션을 '{session_path}'에 저장했습니다."
        except Exception as e:
            return False, f"문자열 가져오기 오류: {e}"

    def disconnect(self):
        # 'with' 구문이 자동으로 연결을 관리하므로 별도의 disconnect는 필요 없습니다.
        pass
