"""알림 큐와 화면 표시를 분리하고 일시정지·재개 시 순서를 유지한다."""

import logging
import json
import os
import threading
import winsound
from notification_popup import NotificationPopup
from theme_manager import ThemeManager
from datetime import datetime

HISTORY_PATH = os.path.join("configs", "noti_history.json")


def load_noti_history():
    """저장된 수신 이력을 읽는다. 파일 없음과 읽기 실패에는 빈 목록을 반환한다."""
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_noti_history(history_list):
    """수신 이력을 저장한다. 팝업 큐는 메모리 상태이며 이 파일과 수명이 다르다."""
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)


class NotificationManager:
    def __init__(self):
        self.queue = []
        self.active = False
        self.paused = False
        self.gp_count = 0
        self.gp_last_state = None
        self.gp_last_name = ""

    def pause(self):
        """게임 시작 직전 호출: 팝업/소리 대기"""
        self.paused = True

    def resume(self):
        """게임 종료 직후 호출: 집계 플러시 후 큐 재개"""
        self.paused = False
        self._flush_gamepad_buffer()
        self._try_show_next()

    def push(
        self,
        message,
        link=None,
        parent=None,
        theme_manager=None,
        notice_id=None,
        silent=False,
    ):
        """
        :param message: 표시할 메시지(예: "게임패드 XXX 연결됨")
        :param link: 클릭 시 열릴 링크
        :param parent: 부모 위젯
        :param theme_manager: 테마 매니저
        :param notice_id: 공지 고유 ID (중복 수신 방지 및 기록용)
        :param silent: True 시 팝업 및 알림음 생략, 기록만 남김
        """
        if notice_id:
            history = load_noti_history()
            if any((entry.get("id") == notice_id for entry in history)):
                return
            history.append(
                {
                    "id": notice_id,
                    "message": message,
                    "link": link,
                    "received_at": datetime.utcnow().isoformat(),
                    "read": False,
                }
            )
            save_noti_history(history)
        if silent:
            return
        (is_gamepad, gp_name, gp_state) = self._parse_gamepad_message(message)
        lower_msg = message.lower()
        is_legion = (
            "legion-controller" in lower_msg or "legion-controller" in gp_name.lower()
        )
        if is_gamepad and is_legion:
            return
        if self.paused:
            if is_gamepad:
                self._aggregate_gamepad(gp_name, gp_state)
                return
            else:
                self.queue.append((message, link, parent, theme_manager))
                self._try_show_next()
                return
        self.queue.append((message, link, parent, theme_manager))
        self._try_show_next()
        self._play_notify_sound_async()

    def _play_notify_sound_async(self):
        """paused가 False일 때만 알림음을 비동기 재생"""
        if self.paused:
            return

        def play_notify_sound():
            try:
                if self.paused:
                    return
                theme = ThemeManager()
                sound_path = theme.get("notify.sound", "")
                if sound_path and os.path.exists(sound_path):
                    # Windows 전용 프로젝트이므로 별도 C 확장 빌드 없이 표준 API를 쓴다.
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

        threading.Thread(target=play_notify_sound, daemon=True).start()

    def _try_show_next(self):
        """GUI 스레드에서 한 건만 표시한다. 팝업의 실제 종료 신호로 다음 건을 연다."""
        if self.active or self.paused or (not self.queue):
            return
        self.active = True
        (message, link, parent, theme_manager) = self.queue.pop(0)
        if theme_manager is None:
            theme_manager = ThemeManager()
        self.popup = NotificationPopup(
            message=message, link=link, theme_manager=theme_manager, parent=parent
        )
        self.popup.closed.connect(self._on_popup_closed)

    def _on_popup_closed(self):
        """표시 시간과 큐 타이머가 어긋나 알림이 겹치지 않도록 완료를 전달받는다."""
        self.active = False
        self._try_show_next()

    def _aggregate_gamepad(self, name: str, state: str):
        """게임 중 들어온 게임패드 노티를 큐에 넣지 않고 집계 버퍼로만 누적"""
        if not name:
            name = ""
        if state not in ("연결됨", "연결 해제됨"):
            state = "연결됨"
        self.gp_count += 1
        self.gp_last_state = state
        self.gp_last_name = name

    def _flush_gamepad_buffer(self):
        """resume 시 호출: 집계된 게임패드 노티를 요약 규칙으로 0~1건 표출"""
        if self.gp_count == 0:
            return
        name = self.gp_last_name or ""
        last_state = self.gp_last_state or "연결됨"
        is_legion = "legion-controller" in name.lower()
        if is_legion:
            self._reset_gamepad_buffer()
            return
        if last_state == "연결됨":
            self._reset_gamepad_buffer()
            return
        summary_msg = f"게임패드 {name} 연결 해제됨".strip()
        self.push(summary_msg, notice_id=None, silent=False)
        self._reset_gamepad_buffer()

    def _reset_gamepad_buffer(self):
        """게임 중 집계한 패드 변화 횟수와 마지막 상태를 함께 비운다."""
        self.gp_count = 0
        self.gp_last_state = None
        self.gp_last_name = ""

    def _parse_gamepad_message(self, message: str):
        """
        메시지가 게임패드 연결/해제 알림인지 판별하고 (is_gamepad, name, state)를 반환.
        name: 문자열, state: "연결됨" | "연결 해제됨" | None
        """
        if not message or not message.startswith("게임패드 "):
            return (False, "", None)
        state = None
        if "연결 해제됨" in message:
            state = "연결 해제됨"
        elif "연결됨" in message:
            state = "연결됨"
        try:
            after = message[len("게임패드 ") :]
            name = after.split(" 연결")[0].strip()
        except Exception:
            name = ""
        return (True, name, state)


notification_manager = NotificationManager()
