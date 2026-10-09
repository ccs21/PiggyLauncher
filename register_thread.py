"""등록 작업을 Qt 작업 스레드에서 수행하고 진행 신호로 UI에 결과를 전달한다."""

from PySide6.QtCore import QThread, Signal


class RegisterThread(QThread):
    """한 플랫폼의 게임을 순차 등록한다. 위젯에는 직접 접근하지 않는다.

    crawler_fn(game, target_root)는 성공 여부를 반환한다. 인증이 필요하면
    game['auth_required']를 설정할 수 있다. 인증 재시도는 UI가 finished를
    받은 뒤 예약한다. 결과 준비와 스레드 종료는 서로 다른 사건이다.
    """

    progress = Signal(int, int)
    completed = Signal(bool)

    def __init__(
        self, games, platform, crawler_fn, target_root, fail_list=None, auth_queue=None
    ):
        super().__init__()
        self.games = games
        self.platform = platform
        self.crawler_fn = crawler_fn
        self.target_root = target_root
        # 빈 리스트도 호출자와 공유해야 한다. `value or []`는 공유를 끊는다.
        self.fail_list = fail_list if fail_list is not None else []
        self.auth_queue = auth_queue if auth_queue is not None else []
        self.success = True

    def run(self):
        """개별 실패를 기록하고 다음 게임을 계속 처리한다.

        중단 요청은 게임 사이에서 확인한다. 이미 시작한 네트워크 요청은 해당
        수집기의 timeout까지 기다릴 수 있다. quit()은 이 반복문을 중단하지 않는다.
        """
        total = len(self.games)
        for i, game in enumerate(self.games, 1):
            if self.isInterruptionRequested():
                self.success = False
                break
            game.pop("auth_required", None)
            try:
                result = self.crawler_fn(game, self.target_root)
            except Exception as error:
                self.fail_list.append(
                    (game.get("title", "이름 없음"), type(error).__name__)
                )
                self.success = False
                self.progress.emit(i, total)
                continue
            if not result and game.get("auth_required"):
                self.auth_queue.append(game)
                self.progress.emit(i, total)
                continue
            if not result:
                self.fail_list.append((game.get("title", "이름 없음"), "등록 실패"))
                self.success = False
            self.progress.emit(i, total)
        self.completed.emit(self.success)

    def get_auth_queue(self):
        """종료된 작업의 인증 대상을 복사해 반환한다. 내부 목록은 외부가 수정하지 않는다."""
        return self.auth_queue.copy()
