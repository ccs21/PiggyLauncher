"""Classic의 gamepad_handler 모듈. 역할과 읽는 순서는 docs/SOURCE_MAP.md를 참고한다."""

import logging
import pygame
import json
import os
import time
import sys
from PySide6.QtCore import QTimer, Qt, QObject, QEvent
from PySide6.QtGui import QKeyEvent, QGuiApplication
from PySide6.QtWidgets import QApplication
from notification_manager import notification_manager

PROFILE_FILE = os.path.join("configs", "gamepad_profiles.json")


class GamepadHandler(QObject):
    POLL_INTERVAL_MS = 100
    EVENT_SCAN_MS = 500
    HOLD_STAGE1_S = 1.0
    HOLD_STAGE2_S = 3.0
    INTERVAL_STAGE1_S = 0.3
    INTERVAL_STAGE2_S = 0.1
    MIN_DEBOUNCE_S = 0.07
    PROTECT_AFTER_REFRESH_S = 0.7
    UNBLOCK_DROP_S = 0.7

    def __init__(self, main_window, central_content, theme_manager):
        super().__init__()
        self.main_window = main_window
        self.central_content = central_content
        self.theme_manager = theme_manager
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        self.pads = []
        self.connected_guids = set()
        self.guid_name_map = {}
        self.profiles = {}
        self.prev_state = {}
        self.hold_state = {}
        self._protect_until = 0.0
        self._drop_until = 0.0
        self._last_block_log = 0.0
        self.hhc_mode_enabled = False
        self.profiles = self.load_profiles()
        self.refresh_gamepads()
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_inputs)
        self.timer.start(self.POLL_INTERVAL_MS)
        self.pygame_event_timer = QTimer()
        self.pygame_event_timer.timeout.connect(self.poll_pygame_events)
        self.pygame_event_timer.start(self.EVENT_SCAN_MS)
        self._input_blocked_state = False
        self.block_watch_timer = QTimer()
        self.block_watch_timer.timeout.connect(self._watch_block_state)
        self.block_watch_timer.start(250)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._kb_drop_count = 0
        self._kb_last_log_ts = 0.0
        self._kb_block_prev = False
        self._effective_blocked_state = False
        self._base_blocked_state = False
        self._base_block_reason = ""
        self._drop_logged_active = False
        self._last_base_blocking = True
        self._manual_block = False

    def _reset_input_states(self):
        """[추가] 홀드/연타 잔상 제거용 입력 상태 초기화"""
        try:
            if hasattr(self, "prev_state"):
                self.prev_state.clear()
            if hasattr(self, "hold_state"):
                self.hold_state.clear()
        except Exception:
            pass

    def _enter_drop_window(self):
        """[추가] 차단 해제 직후 완전 드랍 구간 진입(단발 포함)"""
        self._drop_until = self._now() + self.UNBLOCK_DROP_S

    def _in_drop_window(self) -> bool:
        """[추가] 차단 해제 직후 완전 드랍 구간인지"""
        return self._now() < getattr(self, "_drop_until", 0.0)

    def _should_drop_input_now(self) -> bool:
        """[추가] '차단'이 아니더라도, 드랍 구간이면 입력을 무조건 무시"""
        return self._in_drop_window()

    def _now(self) -> float:
        return time.perf_counter()

    def _enter_protect_window(self):
        self._protect_until = self._now() + self.PROTECT_AFTER_REFRESH_S

    def _in_protect_window(self) -> bool:
        return self._now() < self._protect_until

    def load_profiles(self):
        if not os.path.exists(PROFILE_FILE):
            return {}
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload_profiles(self):
        self.profiles = self.load_profiles()
        self.prev_state = {}
        self.hold_state = {}
        self._enter_protect_window()
        self.refresh_gamepads()

    def refresh_gamepads(self):
        count = pygame.joystick.get_count()
        all_pads = []
        guid_name_map = {}
        for i in range(count):
            try:
                js = pygame.joystick.Joystick(i)
                js.init()
                guid = js.get_guid()
                name = js.get_name() or "알 수 없음"
                all_pads.append(js)
                guid_name_map[guid] = name
            except pygame.error as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.guid_name_map = guid_name_map
        self.connected_guids = set(guid_name_map.keys())
        if self.hhc_mode_enabled and all_pads:
            preferred_index = 0
            preferred_name = None
            for idx, pad in enumerate(all_pads):
                try:
                    name = pad.get_name() or ""
                except Exception:
                    name = ""
                lname = name.lower()
                if "xinput" in lname or "xbox" in lname:
                    preferred_index = idx
                    preferred_name = name
                    try:
                        pad.get_guid()
                    except Exception:
                        pass
                    break
            if preferred_name is None and all_pads:
                pad = all_pads[preferred_index]
                try:
                    preferred_name = pad.get_name() or "알 수 없음"
                    pad.get_guid()
                except Exception:
                    preferred_name = "알 수 없음"
            self.pads = [all_pads[preferred_index]]
        else:
            self.pads = all_pads
        self._enter_protect_window()

    def poll_inputs(self):
        if self._should_block_input() or self._should_drop_input_now():
            return
        for i, pad in enumerate(self.pads):
            try:
                pad.init()
                guid = pad.get_guid()
                profile = self.profiles.get(guid)
                if not profile:
                    continue
                if guid not in self.prev_state:
                    self.prev_state[guid] = {"buttons": {}, "hat": (0, 0)}
                if guid not in self.hold_state:
                    self.hold_state[guid] = {}
                button_qt_map = {
                    "a": Qt.Key_Return,
                    "b": Qt.Key_Escape,
                    "x": Qt.Key_X,
                    "y": Qt.Key_C,
                    "lb": Qt.Key_Q,
                    "rb": Qt.Key_E,
                }
                for logical, qt_key in button_qt_map.items():
                    btn_index = profile.get(logical)
                    if btn_index is None:
                        continue
                    try:
                        pressed = bool(pad.get_button(btn_index))
                    except pygame.error:
                        pressed = False
                    was_pressed = bool(self.prev_state[guid]["buttons"].get(logical, 0))
                    self._process_hold_and_fire(
                        guid,
                        logical,
                        pressed,
                        was_pressed,
                        qt_key,
                        src=f"BTN({btn_index})",
                    )
                    self.prev_state[guid]["buttons"][logical] = 1 if pressed else 0
                if pad.get_numhats() > 0:
                    try:
                        hat = pad.get_hat(0)
                        prev_hat = self.prev_state[guid]["hat"]
                        hat_map = {
                            "hat_up": (0, 1, Qt.Key_W),
                            "hat_down": (0, -1, Qt.Key_S),
                            "hat_left": (-1, 0, Qt.Key_A),
                            "hat_right": (1, 0, Qt.Key_D),
                        }
                        for logical, (ex, ey, qt_key) in hat_map.items():
                            expected = profile.get(logical)
                            if expected is None:
                                continue
                            is_pressed = False
                            was_pressed = False
                            src = "HAT/AXIS"
                            if (
                                isinstance(expected, (list, tuple))
                                and len(expected) == 2
                            ):
                                expected_tuple = (int(expected[0]), int(expected[1]))
                                is_pressed = tuple(hat) == expected_tuple
                                prev_dir_pressed = tuple(prev_hat) == expected_tuple
                                was_pressed = prev_dir_pressed
                                src = f"HAT{expected_tuple}"
                            elif (
                                isinstance(expected, dict)
                                and expected.get("type") == "axis"
                            ):
                                axis_index = int(expected.get("axis", 0))
                                dir_sign = int(expected.get("dir", 0))
                                thr = float(expected.get("threshold", 0.3))
                                try:
                                    v = float(pad.get_axis(axis_index))
                                except Exception:
                                    v = 0.0
                                if dir_sign < 0:
                                    is_pressed = v <= -thr
                                elif dir_sign > 0:
                                    is_pressed = v >= thr
                                else:
                                    is_pressed = False
                                was_pressed = bool(
                                    self.prev_state[guid]["buttons"].get(logical, 0)
                                )
                                src = f"AXIS({axis_index},{dir_sign},thr={thr})"
                            self._process_hold_and_fire(
                                guid, logical, is_pressed, was_pressed, qt_key, src=src
                            )
                            self.prev_state[guid]["buttons"][logical] = (
                                1 if is_pressed else 0
                            )
                        self.prev_state[guid]["hat"] = hat
                    except pygame.error as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
            except pygame.error as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def _process_hold_and_fire(
        self,
        guid: str,
        logical: str,
        pressed: bool,
        was_pressed: bool,
        qt_key: int,
        src: str,
    ):
        """
        논리 입력(버튼/방향)에 대해:
          - <1s: 초발 1회만
          - 1~3s: 0.5s당 1회
          - ≥3s: 0.1s당 1회(연속입력)
        해제 시 hold 상태 초기화.
        디바운스 70ms 적용.
        리로드/재인식 직후 200ms 보호 구간: 초발 1회만 허용(반복은 시간 규칙으로만)
        """
        htable = self.hold_state[guid]
        st = htable.get(logical)
        now = self._now()
        if st is None:
            st = {"pressed": False, "hold_start": 0.0, "last_fire": 0.0}
            htable[logical] = st
        if pressed and (not was_pressed):
            st["pressed"] = True
            st["hold_start"] = now
            self._fire_key(
                qt_key,
                reason=f"press{(' (protect)' if self._in_protect_window() else '')}",
                src=src,
            )
            st["last_fire"] = now
            return
        if not pressed and was_pressed:
            st["pressed"] = False
            st["hold_start"] = 0.0
            st["last_fire"] = 0.0
            return
        if not pressed:
            return
        held_for = now - st["hold_start"] if st["hold_start"] else 0.0
        since_last = now - st["last_fire"] if st["last_fire"] else 999.0
        if since_last < self.MIN_DEBOUNCE_S:
            return
        if held_for < self.HOLD_STAGE1_S:
            return
        if held_for < self.HOLD_STAGE2_S:
            if since_last >= self.INTERVAL_STAGE1_S:
                self._fire_key(qt_key, reason="hold-0.5s", src=src)
                st["last_fire"] = now
            return
        if since_last >= self.INTERVAL_STAGE2_S:
            self._fire_key(qt_key, reason="hold-0.1s", src=src)
            st["last_fire"] = now

    def poll_pygame_events(self):
        if self._should_block_input() or self._should_drop_input_now():
            return
        try:
            if not pygame.joystick.get_init():
                return
            pygame.event.get()
        except Exception:
            return
        current_guids = set()
        guid_to_name = {}
        for i in range(pygame.joystick.get_count()):
            try:
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                current_guids.add(joystick.get_guid())
                guid_to_name[joystick.get_guid()] = joystick.get_name()
            except pygame.error:
                pass
        if current_guids != self.connected_guids:
            added = current_guids - self.connected_guids
            removed = self.connected_guids - current_guids
            for guid in added:
                name = guid_to_name.get(guid, "알 수 없음")
                self.guid_name_map[guid] = name
                try:
                    notification_manager.push(
                        f"게임패드 {name} 연결됨",
                        parent=self.main_window,
                        theme_manager=self.theme_manager,
                    )
                except Exception:
                    pass
            for guid in removed:
                name = self.guid_name_map.pop(guid, "알 수 없음")
                try:
                    notification_manager.push(
                        f"게임패드 {name} 연결 해제됨",
                        parent=self.main_window,
                        theme_manager=self.theme_manager,
                    )
                except Exception:
                    pass
            self.connected_guids = current_guids
            self.refresh_gamepads()
            self._enter_protect_window()

    def _fire_key(self, qt_key: int, reason: str, src: str):
        if self._should_block_input() or self._should_drop_input_now():
            return
        event = QKeyEvent(QKeyEvent.KeyPress, qt_key, Qt.NoModifier)
        topmost = self.get_topmost_visible_window()
        if topmost is None or topmost is self.main_window:
            focus = QApplication.focusWidget()
            if focus:
                QApplication.postEvent(focus, event)
            else:
                QApplication.postEvent(self.central_content, event)
        else:
            QApplication.postEvent(topmost, event)

    def _get_base_block_reason(self) -> str:
        """
        BASE 차단 사유 문자열을 반환합니다. (로그용)
        _should_block_input()과 "동일 조건/동일 우선순위"로 맞추는 게 중요합니다.
        """
        try:
            if getattr(self, "_manual_block", False):
                return "manual block"
            mw = getattr(self, "main_window", None)
            if mw is not None and getattr(mw, "is_game_running", False):
                return "game running"
            if mw is not None and (not self._is_launcher_foreground()):
                return "launcher not foreground"
            if mw is not None and mw.isMinimized():
                return "launcher minimized"
        except Exception:
            pass
        return ""

    def _should_block_input(self) -> bool:
        """
        런처 창이 최소화되어 있거나, 실행 중인 게임을 감시하는 동안에는
        모든 게임패드→키 입력(및 키보드 이벤트 필터)을 차단합니다.
        """
        try:
            if getattr(self, "_manual_block", False):
                return True
            mw = getattr(self, "main_window", None)
            now = time.time()
            if mw is not None and getattr(mw, "is_game_running", False):
                if now - getattr(self, "_last_block_log", 0) >= 10.0:
                    self._last_block_log = now
                return True
            if mw is not None and (not self._is_launcher_foreground()):
                if now - getattr(self, "_last_block_log", 0) >= 10.0:
                    self._last_block_log = now
                return True
            if mw is not None and mw.isMinimized():
                if now - getattr(self, "_last_block_log", 0) >= 10.0:
                    self._last_block_log = now
                return True
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        return False

    def _is_launcher_foreground(self) -> bool:
        """
        런쳐가 '포그라운드'인지 판정 (팝업/다이얼로그 포함)

        핵심:
        - "메인 윈도우가 전면인지"가 아니라
        - "우리 앱(프로세스) 소속 창이 전면인지"로 판단해야 팝업이 떠도 차단이 안 걸립니다.
        """
        try:
            if QGuiApplication.applicationState() != Qt.ApplicationActive:
                return False
            aw = QApplication.activeWindow()
            if aw is not None:
                return True
            return True
        except Exception:
            pass
        if sys.platform.startswith("win"):
            try:
                import ctypes

                user32 = ctypes.windll.user32
                fg_hwnd = user32.GetForegroundWindow()
                if not fg_hwnd:
                    return False
                pid = ctypes.c_uint32(0)
                user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(pid))
                return int(pid.value) == int(os.getpid())
            except Exception:
                return False
        return True

    def _watch_block_state(self):
        try:
            base_blocking = bool(self._should_block_input())
        except Exception:
            return
        base_reason = self._get_base_block_reason() if base_blocking else ""
        if base_blocking != getattr(self, "_base_blocked_state", False):
            self._base_blocked_state = base_blocking
            self._base_block_reason = base_reason
            if base_blocking:
                self._kb_last_log_ts = time.time()
                self._kb_drop_count = 0
            else:
                self._kb_drop_count = 0
        elif (
            base_blocking
            and base_reason
            and (base_reason != getattr(self, "_base_block_reason", ""))
        ):
            self._base_block_reason = base_reason
        if not base_blocking and getattr(self, "_last_base_blocking", True):
            self._enter_drop_window()
            self._drop_logged_active = True
        self._last_base_blocking = base_blocking
        if getattr(self, "_drop_logged_active", False) and (
            not self._should_drop_input_now()
        ):
            self._drop_logged_active = False
        effective_blocking = base_blocking or self._should_drop_input_now()
        if effective_blocking != getattr(self, "_effective_blocked_state", False):
            self._effective_blocked_state = effective_blocking
        if effective_blocking != getattr(self, "_input_blocked_state", False):
            self._input_blocked_state = effective_blocking
            self._reset_input_states()
            self._apply_polling_state(effective_blocking)

    def _apply_polling_state(self, blocking: bool):
        """
        blocking=True  => 입력 관련 폴링 타이머 정지
        blocking=False => 입력 관련 폴링 타이머 재개
        """
        if blocking:
            if (
                isinstance(getattr(self, "timer", None), QTimer)
                and self.timer.isActive()
            ):
                self.timer.stop()
            if (
                isinstance(getattr(self, "pygame_event_timer", None), QTimer)
                and self.pygame_event_timer.isActive()
            ):
                self.pygame_event_timer.stop()
        else:
            if isinstance(getattr(self, "timer", None), QTimer) and (
                not self.timer.isActive()
            ):
                self.timer.start(self.POLL_INTERVAL_MS)
            if isinstance(getattr(self, "pygame_event_timer", None), QTimer) and (
                not self.pygame_event_timer.isActive()
            ):
                self.pygame_event_timer.start(self.EVENT_SCAN_MS)

    def pause_input(self, on: bool = True):
        self._manual_block = bool(on)
        try:
            blocking = self._should_block_input()
            self._input_blocked_state = blocking
            self._apply_polling_state(blocking)
        except Exception:
            pass

    def get_topmost_visible_window(self):
        aw = QApplication.activeWindow()
        if aw is not None and aw.isVisible():
            return aw
        for widget in reversed(QApplication.topLevelWidgets()):
            try:
                if widget.isVisible():
                    return widget
            except Exception:
                pass
        return None

    def set_hhc_mode(self, enabled: bool):
        enabled = bool(enabled)
        if self.hhc_mode_enabled == enabled:
            return
        self.hhc_mode_enabled = enabled
        self.refresh_gamepads()

    def eventFilter(self, obj, event):
        """
        런처가 '블록 조건'일 때(= 현재 구조상 최소화 상태일 때),
        키보드 이벤트를 모두 무시(소비)하고, 시작/요약/해제 로그를 출력합니다.
        - 게임패드 블록과 동일한 타이밍/조건으로 동작
        - 마우스 이벤트는 차단하지 않음
        """
        et = event.type()
        BLOCK_EVENTS = (
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.Shortcut,
            QEvent.ShortcutOverride,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseButtonDblClick,
            QEvent.Wheel,
            QEvent.ContextMenu,
            QEvent.TouchBegin,
            QEvent.TouchUpdate,
            QEvent.TouchEnd,
            QEvent.Gesture,
            QEvent.NativeGesture,
        )
        if et in BLOCK_EVENTS:
            blocking = bool(getattr(self, "_effective_blocked_state", False))
            if blocking and getattr(self, "_base_block_reason", "") == "manual block":
                return False
            if blocking:
                self._kb_drop_count += 1
                now = time.time()
                if now - self._kb_last_log_ts >= 1.0:
                    self._kb_drop_count = 0
                    self._kb_last_log_ts = now
                return True
        return False
