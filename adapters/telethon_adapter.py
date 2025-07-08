# adapters/telethon_adapter.py
import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from ui.constants import SESSIONS_DIR


class TelethonAdapter:
    """Telethon 라이브러리를 위한 동기 방식 어댑터"""

    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash

    def _get_client(self, session_name):
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        return TelegramClient(session_path, self.api_id, self.api_hash)

    def _run_async(self, coro):
        """비동기 코루틴을 동기적으로 실행"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 새 루프 생성
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 이벤트 루프가 없으면 새로 생성
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

    async def _create_session_async(self, session_name, phone_number, code_callback):
        client = self._get_client(session_name)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                code = code_callback("Telegram 인증 코드를 입력하세요:")
                try:
                    await client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    password = code_callback("2단계 인증 비밀번호를 입력하세요:")
                    await client.sign_in(password=password)
            await client.disconnect()
            save_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
            return True, f"Telethon 세션 저장 완료: {save_path}"
        except Exception as e:
            return False, f"Telethon 오류: {e}"

    def create_session(self, session_name, phone_number, code_callback):
        """동기 방식으로 세션 생성"""
        return self._run_async(self._create_session_async(session_name, phone_number, code_callback))

    async def _check_session_async(self, session_name):
        client = self._get_client(session_name)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                return True, f"세션 유효. 사용자: @{me.username if me.username else '없음'}"
            else:
                await client.disconnect()
                return False, "세션이 유효하지 않습니다."
        except Exception as e:
            return False, f"세션 확인 오류: {e}"

    def check_session(self, session_name):
        """동기 방식으로 세션 확인"""
        return self._run_async(self._check_session_async(session_name))

    async def _export_session_string_async(self, session_name):
        client = self._get_client(session_name)
        try:
            await client.connect()
            if await client.is_user_authorized():
                session_string = StringSession.save(client.session)
                await client.disconnect()
                return session_string
            await client.disconnect()
            return ""
        except Exception:
            return ""

    def export_session_string(self, session_name):
        """동기 방식으로 세션 문자열 내보내기"""
        return self._run_async(self._export_session_string_async(session_name))

    async def _import_session_from_string_async(self, session_name, session_string):
        session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
        try:
            string_client = TelegramClient(StringSession(session_string), self.api_id, self.api_hash)
            await string_client.connect()
            
            if await string_client.is_user_authorized():
                # 세션 정보를 파일로 저장
                new_client = TelegramClient(session_path, self.api_id, self.api_hash)
                new_client.session.set_dc(string_client.session.dc_id, 
                                        string_client.session.server_address, 
                                        string_client.session.port)
                new_client.session.auth_key = string_client.session.auth_key
                new_client.session.save()
                await string_client.disconnect()
                return True, f"문자열에서 세션을 '{session_path}'에 저장했습니다."
            else:
                await string_client.disconnect()
                return False, "세션 문자열이 유효하지 않습니다."
        except Exception as e:
            return False, f"문자열 가져오기 오류: {e}"

    def import_session_from_string(self, session_name, session_string):
        """동기 방식으로 세션 문자열 가져오기"""
        return self._run_async(self._import_session_from_string_async(session_name, session_string))
