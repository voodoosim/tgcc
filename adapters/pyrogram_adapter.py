# adapters/pyrogram_adapter.py
import os
import logging
import sentry_sdk

from pyrogram.client import Client
from pyrogram.errors import SessionPasswordNeeded, AuthKeyInvalid, RPCError
from pyrogram.errors.exceptions.bad_request_400 import PhoneCodeInvalid, PasswordHashInvalid

from ui.constants import SESSIONS_DIR

logger = logging.getLogger(__name__)

# Sentry 초기화 (중복 방지를 위해 조건부 초기화)
if not sentry_sdk.Hub.current.client:
    sentry_sdk.init(
        dsn="https://7f1801913a84e667c35ba63f2d0aa344@o4509638743097344.ingest.de.sentry.io/4509641306341456",
        send_default_pii=True,
        traces_sample_rate=1.0,
    )


class PyrogramAdapter:
    """Pyrogram 라이브러리를 위한 동기 방식 어댑터"""

    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.workdir = os.path.abspath(SESSIONS_DIR)
        logger.info(f"PyrogramAdapter 초기화: API_ID={api_id}, workdir={self.workdir}")
        
        # Sentry 컨텍스트 설정
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("component", "pyrogram_adapter")
            scope.set_context("pyrogram", {
                "api_id": str(api_id),
                "adapter_version": "1.0"
            })

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
        logger.info(f"세션 생성 시작: {session_name}, 전화번호: {phone_number}")
        with sentry_sdk.start_transaction(name="create_session", op="pyrogram_operation") as transaction:
            transaction.set_data("session_name", session_name)
            transaction.set_data("phone_number", phone_number)
            
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
                
                # 성공 이벤트 기록
                sentry_sdk.add_breadcrumb(
                    message=f"Pyrogram session created successfully: {session_name}",
                    level="info"
                )
                
                return True, f"Pyrogram 세션 저장 완료: {save_path}"
            except (SessionPasswordNeeded, AuthKeyInvalid, PhoneCodeInvalid, PasswordHashInvalid) as e:
                # Pyrogram 관련 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_creation", {
                        "session_name": session_name,
                        "phone_number": phone_number,
                        "error_type": type(e).__name__
                    })
                
                sentry_sdk.capture_exception(e)
                return False, f"Pyrogram 인증 오류: {e}"
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

    def check_session(self, session_name):
        logger.info(f"세션 검사 시작: {session_name}")
        session_path = os.path.join(self.workdir, f"{session_name}.session")
        logger.debug(f"세션 파일 경로: {session_path}")
        logger.debug(f"파일 존재 여부: {os.path.exists(session_path)}")
        
        if not os.path.exists(session_path):
            logger.error(f"세션 파일이 존재하지 않음: {session_path}")
            return False, f"세션 파일을 찾을 수 없습니다: {session_path}"
        
        file_size = os.path.getsize(session_path)
        logger.debug(f"세션 파일 크기: {file_size} bytes")
        
        with sentry_sdk.start_transaction(name="check_session", op="pyrogram_operation") as transaction:
            transaction.set_data("session_name", session_name)
            
            try:
                logger.debug("Pyrogram 클라이언트 연결 시도...")
                with self._get_client(session_name) as client:
                    logger.debug("클라이언트 생성 성공, get_me() 호출...")
                    me = client.get_me()
                    logger.info(f"세션 인증 성공: @{me.username if me.username else '없음'}")
                    
                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Pyrogram session check successful: {session_name}",
                        level="info"
                    )
                    
                    return True, f"세션 유효. 사용자: @{me.username if me.username else '없음'}"
            except (AuthKeyInvalid, RPCError) as e:
                logger.error(f"Pyrogram 인증 오류: {type(e).__name__}: {e}", exc_info=True)
                # Pyrogram 관련 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_check", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })
                
                sentry_sdk.capture_exception(e)
                return False, f"세션 인증 오류: {e}"
            except (OSError, ConnectionError, TimeoutError) as e:
                logger.error(f"네트워크 오류: {type(e).__name__}: {e}", exc_info=True)
                # 네트워크 관련 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_check", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })
                
                sentry_sdk.capture_exception(e)
                return False, f"네트워크 연결 오류: {e}"
            except Exception as e:
                logger.error(f"예상치 못한 오류: {type(e).__name__}: {e}", exc_info=True)
                sentry_sdk.capture_exception(e)
                return False, f"세션 확인 중 오류: {type(e).__name__}: {e}"

    def export_session_string(self, session_name):
        with sentry_sdk.start_transaction(name="export_session_string", op="pyrogram_operation") as transaction:
            transaction.set_data("session_name", session_name)
            
            try:
                with self._get_client(session_name) as client:
                    session_string = client.export_session_string()
                    
                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message=f"Pyrogram session string exported: {session_name}",
                        level="info"
                    )
                    
                    return session_string
            except (AuthKeyInvalid, RPCError, OSError, ConnectionError) as e:
                # 구체적 에러 처리
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("session_export", {
                        "session_name": session_name,
                        "error_type": type(e).__name__
                    })
                
                sentry_sdk.capture_exception(e)
                return ""

    def import_session_from_string(self, session_name, session_string):
        with sentry_sdk.start_transaction(name="import_session_from_string", op="pyrogram_operation") as transaction:
            transaction.set_data("session_name", session_name)
            
            try:
                with self._get_client(session_name, session_string=session_string) as client:
                    me = client.get_me()
                save_path = os.path.join(self.workdir, f"{session_name}.session")
                
                # 성공 이벤트 기록
                sentry_sdk.add_breadcrumb(
                    message=f"Pyrogram session imported from string: {session_name}",
                    level="info"
                )
                
                return True, f"문자열에서 세션을 '{save_path}'에 저장했습니다. (@{me.username if me.username else '없음'})"
            except (AuthKeyInvalid, RPCError) as e:
                # Pyrogram 관련 구체적 에러 처리
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
