# ui/async_worker.py
"""비동기 작업 처리를 위한 QThread 워커"""
import asyncio
import logging
import sentry_sdk

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# Sentry 초기화 (중복 방지를 위해 조건부 초기화)
if not sentry_sdk.Hub.current.client:
    sentry_sdk.init(
        dsn="https://7f1801913a84e667c35ba63f2d0aa344@o4509638743097344.ingest.de.sentry.io/4509641306341456",
        send_default_pii=True,
        traces_sample_rate=1.0,
    )


class AsyncWorker(QThread):
    """비동기 코루틴을 실행하는 워커 스레드"""

    result = pyqtSignal(object)  # dict -> object로 변경 (모든 타입 허용)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        self._is_running = True
        self.loop = None
        
        # Sentry 컨텍스트 설정
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("component", "async_worker")
            scope.set_context("worker", {
                "coroutine": str(coro),
                "worker_version": "1.0"
            })

    def run(self):
        """스레드 실행"""
        with sentry_sdk.start_transaction(name="async_worker_run", op="qt_operation") as transaction:
            try:
                logger.info("AsyncWorker 시작")
                self.progress.emit("작업 시작...")

                # 새로운 이벤트 루프 생성
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

                # 코루틴 실행
                result = self.loop.run_until_complete(self.coro)

                if self._is_running:
                    logger.info("AsyncWorker 완료")
                    self.result.emit(result)
                    
                    # 성공 이벤트 기록
                    sentry_sdk.add_breadcrumb(
                        message="AsyncWorker completed successfully",
                        level="info"
                    )

            except asyncio.CancelledError as e:
                logger.warning("AsyncWorker 취소됨")
                self.error.emit("작업이 취소되었습니다")
                
                # 취소 이벤트 기록
                sentry_sdk.add_breadcrumb(
                    message="AsyncWorker cancelled",
                    level="warning"
                )
                sentry_sdk.capture_exception(e)

            except (RuntimeError, OSError, ValueError) as e:
                # 시스템 관련 구체적 에러 처리
                logger.error("AsyncWorker 시스템 오류: %s: %s", type(e).__name__, str(e))
                if self._is_running:
                    self.error.emit(f"시스템 오류: {type(e).__name__}: {str(e)}")
                
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("worker_error", {
                        "error_type": type(e).__name__,
                        "is_running": self._is_running
                    })
                
                sentry_sdk.capture_exception(e)

            except (TypeError, AttributeError) as e:
                # 코드 관련 구체적 에러 처리
                logger.error("AsyncWorker 코드 오류: %s: %s", type(e).__name__, str(e))
                if self._is_running:
                    self.error.emit(f"코드 오류: {type(e).__name__}: {str(e)}")
                
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("worker_error", {
                        "error_type": type(e).__name__,
                        "is_running": self._is_running
                    })
                
                sentry_sdk.capture_exception(e)

            finally:
                # 이벤트 루프 정리
                if self.loop:
                    try:
                        # 남은 태스크 취소
                        pending = asyncio.all_tasks(self.loop)
                        for task in pending:
                            task.cancel()

                        # 루프 종료
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        self.loop.close()

                    except (RuntimeError, OSError) as e:
                        logger.error("루프 정리 중 오류: %s", e)
                        sentry_sdk.capture_exception(e)

                logger.info("AsyncWorker 종료")

    def stop(self):
        """스레드 중지"""
        logger.info("AsyncWorker 중지 요청")
        self._is_running = False

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # 스레드 종료 대기
        if self.isRunning():
            self.quit()
            if not self.wait(5000):  # 5초 대기
                logger.warning("AsyncWorker 강제 종료")
                self.terminate()
                self.wait()
