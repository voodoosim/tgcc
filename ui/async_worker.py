# ui/async_worker.py
"""비동기 작업 처리를 위한 QThread 워커"""
import asyncio
import logging

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


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

    def run(self):
        """스레드 실행"""
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

        except asyncio.CancelledError:
            logger.warning("AsyncWorker 취소됨")
            self.error.emit("작업이 취소되었습니다")

        except Exception as e:
            logger.error(f"AsyncWorker 오류: {type(e).__name__}: {str(e)}")
            if self._is_running:
                self.error.emit(f"{type(e).__name__}: {str(e)}")

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

                except Exception as e:
                    logger.error(f"루프 정리 중 오류: {e}")

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
