"""패드 버튼을 하나씩 입력받아 GUID별 매핑을 저장하는 화면.
같은 제품명이라도 GUID가 다르면 다른 매핑일 수 있다. 공개본은 장치 정보를 외부로 전송하지 않는다.
"""

import logging
import pygame
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QTimer
import json
import os

PROFILE_FILE = os.path.join("configs", "gamepad_profiles.json")


class ButtonMappingPopup(QDialog):
    def __init__(self, joystick, guid, name, parent=None, main_widget=None):
        super().__init__(parent)
        self.joystick = joystick
        self.guid = guid
        self.name = name
        self.main_widget = main_widget
        self.theme_manager = parent.theme_manager
        scale_px = self.theme_manager.scale_px
        self.setWindowTitle(f"{name} 버튼 매핑")
        self.setWindowIcon(QIcon("icon/PiggyLauncher.ico"))
        self.mapping = {}
        self.step = 0
        self.waiting_for_release = False
        self.axis_neutral = []
        try:
            if not self.joystick.get_init():
                self.joystick.init()
            pygame.event.pump()
            self.axis_neutral = [
                float(self.joystick.get_axis(i))
                for i in range(self.joystick.get_numaxes())
            ]
        except Exception:
            self.axis_neutral = []
        self.button_order = [
            ("a", "A 버튼을 눌러주세요"),
            ("b", "B 버튼을 눌러주세요"),
            ("x", "X 버튼을 눌러주세요"),
            ("y", "Y 버튼을 눌러주세요"),
            ("lb", "L 버튼을 눌러주세요"),
            ("rb", "R 버튼을 눌러주세요"),
            ("hat_up", "방향키 ↑ 를 눌러주세요"),
            ("hat_down", "방향키 ↓ 를 눌러주세요"),
            ("hat_left", "방향키 ← 를 눌러주세요"),
            ("hat_right", "방향키 → 를 눌러주세요"),
        ]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            scale_px(40), scale_px(40), scale_px(40), scale_px(40)
        )
        layout.setSpacing(scale_px(20))
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        font_conf = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_conf.get("family", "맑은 고딕")
        font_size = font_conf.get("size", 18)
        font_bold = font_conf.get("bold", True)
        font_color = font_conf.get("color", "#FFFFFF")
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        self.label.setFont(font)
        font_weight = "bold" if font_bold else "normal"
        self.label.setStyleSheet(
            f"\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_weight};\n            color: {font_color};\n            border: none;\n        "
        )
        layout.addWidget(self.label)
        self.adjustSize()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_input)
        self.timer.start(100)
        self.show_next_prompt()

    def show_next_prompt(self):
        if self.step < len(self.button_order):
            (_, text) = self.button_order[self.step]
            self.label.setText(text)
            self.adjustSize()
        else:
            self.save_profile()
            self.timer.stop()
            if self.main_widget and hasattr(self.main_widget, "gamepad_handler"):
                self.main_widget.gamepad_handler.reload_profiles()
            self.accept()

    def check_input(self):
        if self.step >= len(self.button_order):
            return
        pygame.event.pump()
        try:
            if not self.joystick.get_init():
                self.joystick.init()
        except pygame.error:
            return
        (key, _) = self.button_order[self.step]
        try:
            if self.waiting_for_release:
                buttons_released = all(
                    (
                        self.joystick.get_button(i) == 0
                        for i in range(self.joystick.get_numbuttons())
                    )
                )
                hat_released = (
                    self.joystick.get_hat(0) == (0, 0)
                    if self.joystick.get_numhats() > 0
                    else True
                )
                axis_released = True
                for ai in range(self.joystick.get_numaxes()):
                    try:
                        v = float(self.joystick.get_axis(ai))
                    except Exception:
                        v = 0.0
                    if self.axis_neutral and ai < len(self.axis_neutral):
                        neutral = float(self.axis_neutral[ai])
                        if abs(v - neutral) >= 0.3:
                            axis_released = False
                            break
                    elif abs(v) >= 0.3:
                        axis_released = False
                        break
                if buttons_released and hat_released and axis_released:
                    self.waiting_for_release = False
                return
            if key.startswith("hat"):
                hat = (
                    self.joystick.get_hat(0)
                    if self.joystick.get_numhats() > 0
                    else (0, 0)
                )
                expected = {
                    "hat_up": (0, 1),
                    "hat_down": (0, -1),
                    "hat_left": (-1, 0),
                    "hat_right": (1, 0),
                }[key]
                if hat == expected:
                    self.mapping[key] = hat
                    self.step += 1
                    self.waiting_for_release = True
                    self.show_next_prompt()
                    return
                best_axis = None
                best_delta = 0.0
                for ai in range(self.joystick.get_numaxes()):
                    try:
                        v = float(self.joystick.get_axis(ai))
                    except Exception:
                        continue
                    if self.axis_neutral and ai < len(self.axis_neutral):
                        neutral = float(self.axis_neutral[ai])
                        delta = v - neutral
                    else:
                        delta = v
                    if abs(delta) > abs(best_delta):
                        best_delta = delta
                        best_axis = ai
                if best_axis is not None and abs(best_delta) >= 0.3:
                    direction = 1 if best_delta > 0 else -1
                    self.mapping[key] = {
                        "type": "axis",
                        "axis": int(best_axis),
                        "dir": int(direction),
                        "threshold": 0.3,
                    }
                    self.step += 1
                    self.waiting_for_release = True
                    self.show_next_prompt()
                    return
            else:
                for i in range(self.joystick.get_numbuttons()):
                    if self.joystick.get_button(i):
                        self.mapping[key] = i
                        self.step += 1
                        self.waiting_for_release = True
                        self.show_next_prompt()
                        break
        except pygame.error as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def save_profile(self):
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data[self.guid] = self.mapping
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def closeEvent(self, event):
        try:
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        super().closeEvent(event)
