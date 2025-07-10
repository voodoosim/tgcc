# adapters/telethon_adapter.py
import os
import asyncio
import sentry_sdk
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyError, RPCError
from telethon.sessions import StringSession
from ui.constants import SESSIONS_DIR

# Sentry 초기화
sentry_sdk.init(
    dsn="https://7f1801913a84e667c35ba63f2d0aa344@o4509638743097344.ingest.de.sentry.io/4509641306341456",
    # 사용자 데이터 수집 (요청 헤더, IP 등)
    send_default_pii=True,
    # 성능 모니터링 설정
    traces_sample_rate=1.0,
)


class TelethonAdapter:
    """Telethon 라이브러리를 위한 동기 방식 어댑터"""

    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash

        # Sentry에 컨텍스트 정보 추가
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("component", "telethon_adapter")
            scope.set_context("telethon", {
                "api_id": str(api_id),
                "adapter_version": "1.0"
            })

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
        except RuntimeError as e:
            # 이벤트 루프 관련 에러를 Sentry에 전송
            sentry_sdk.capture_exception(e)
            # 이벤트 루프가 없으면 새로 생성
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        except (OSError, ValueError, TypeError) as e:
            # 예상 가능한 에러들을 구체적으로 처리
            sentry_sdk.capture_exception(e)
            raise

    async def _create_session_async(self, session_name, phone_number, code_callback):
        # Sentry 트랜잭션 시작
        with sentry_sdk.start_transaction(name="create_session", op="telethon_operation") as transaction:
            transaction.set_data("session_name", session_name)
            transaction.set_data("phone_number", phone_number)

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

                # 성공 이벤트 기록
                sentry_sdk.add_breadcrumb(
                    message=f"Telethon session created successfully: {session_name}",
                    level="info"
                )

                return True, f"Telethon 세션 저장 완료: {save_path}"
            except (SessionPasswordNeededError, AuthKeyError, RPCError) as e:
                # Telethon 관련 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_creation", {
                        "session_name": session_name,
                        "phone_number": phone_number,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"Telethon 인증 오류: {e}"
            except (OSError, ConnectionError, TimeoutError) as e:
                # 네트워크 관련 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_creation", {
                        "session_name": session_name,
                        "phone_number": phone_number,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"네트워크 연결 오류: {e}"

    def create_session(self, session_name, phone_number, code_callback):
        """동기 방식으로 세션 생성"""
        try:
            return self._run_async(self._create_session_async(session_name, phone_number, code_callback))
        except (ValueError, TypeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"입력 값 오류: {e}"
        except (OSError, RuntimeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"시스템 오류: {e}"

    async def _check_session_async(self, session_name):
        # Sentry 트랜잭션 시작
        with sentry_sdk.start_transaction(name="check_session", op="telethon_operation") as transaction:
            transaction.set_data("session_name", session_name)

            client = self._get_client(session_name)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    await client.disconnect()

                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Session check successful: {session_name}",
                        level="info"
                    )

                    return True, f"세션 유효. 사용자: @{me.username if me.username else '없음'}"
                else:
                    await client.disconnect()
                    # 경고 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Invalid session: {session_name}",
                        level="warning"
                    )
                    return False, "세션이 유효하지 않습니다."
            except (AuthKeyError, RPCError) as e:
                # Telethon 관련 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_check", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"세션 인증 오류: {e}"
            except (OSError, ConnectionError, TimeoutError) as e:
                # 네트워크 관련 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_check", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"네트워크 연결 오류: {e}"

    def check_session(self, session_name):
        """동기 방식으로 세션 확인"""
        try:
            return self._run_async(self._check_session_async(session_name))
        except (ValueError, TypeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"입력 값 오류: {e}"
        except (OSError, RuntimeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"시스템 오류: {e}"

    async def _export_session_string_async(self, session_name):
        with sentry_sdk.start_transaction(name="export_session_string", op="telethon_operation") as transaction:
            transaction.set_data("session_name", session_name)

            client = self._get_client(session_name)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    session_string = StringSession.save(client.session)
                    await client.disconnect()

                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Session string exported: {session_name}",
                        level="info"
                    )

                    return session_string
                await client.disconnect()
                return ""
            except (AuthKeyError, RPCError, OSError, ConnectionError) as e:
                # 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_export", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return ""

    def export_session_string(self, session_name):
        """동기 방식으로 세션 문자열 내보내기"""
        try:
            return self._run_async(self._export_session_string_async(session_name))
        except (ValueError, TypeError, OSError, RuntimeError) as e:
            sentry_sdk.capture_exception(e)
            return ""

    async def _import_session_from_string_async(self, session_name, session_string):
        with sentry_sdk.start_transaction(name="import_session_from_string", op="telethon_operation") as transaction:
            transaction.set_data("session_name", session_name)

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

                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Session imported from string: {session_name}",
                        level="info"
                    )

                    return True, f"문자열에서 세션을 '{session_path}'에 저장했습니다."
                else:
                    await string_client.disconnect()

                    # 경고 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Invalid session string for: {session_name}",
                        level="warning"
                    )

                    return False, "세션 문자열이 유효하지 않습니다."
            except (AuthKeyError, RPCError) as e:
                # Telethon 관련 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_import", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"세션 인증 오류: {e}"
            except (OSError, ConnectionError, ValueError) as e:
                # 파일/네트워크/값 관련 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_import", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })

                sentry_sdk.capture_exception(e)
                return False, f"세션 가져오기 오류: {e}"

    def import_session_from_string(self, session_name, session_string):
        """동기 방식으로 세션 문자열 가져오기"""
        try:
            return self._run_async(self._import_session_from_string_async(session_name, session_string))
        except (ValueError, TypeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"입력 값 오류: {e}"
        except (OSError, RuntimeError) as e:
            sentry_sdk.capture_exception(e)
            return False, f"시스템 오류: {e}"
