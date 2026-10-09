"""사용할 게임패드를 선택하고 매핑 화면으로 전달하는 대화상자.
장치 선택과 실제 버튼 학습은 분리되어 있다.
"""

import logging
import pygame
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import QTimer, Qt


class GamepadConfigPopup(QDialog):
    def __init__(self, pad_list, on_guid_selected, parent=None):
        super().__init__(parent)
        self.theme_manager = getattr(parent, "theme_manager", None)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("게임패드 매핑 시작")
        self.setWindowIcon(QIcon("icon/PiggyLauncher.ico"))
        if self.theme_manager:
            bg_color = self.theme_manager.get("background.popup")
            if isinstance(bg_color, dict):
                color_value = bg_color.get("value", "#000000")
                self.setStyleSheet(f"background-color: {color_value};")
        self.pad_list = pad_list
        self.on_guid_selected = on_guid_selected
        layout = QVBoxLayout(self)
        self.label = QLabel(
            "🎮 새로운 게임패드가 검색되었습니다.\n\n복수의 게임패드가 연결되어 있는 경우 하나씩 차례로 맵핑해 주세요.\n\nA버튼을 눌러주세요",
            self,
        )
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        font_conf = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_conf.get("family", "맑은 고딕")
        font_size = font_conf.get("size", 18)
        font_bold = font_conf.get("bold", False)
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
        self.setFixedHeight(self.height())
        self.setFixedWidth(max(600, self.label.sizeHint().width() + 100))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_inputs)
        self.timer.start(100)

    def check_inputs(self):
        pygame.event.pump()
        for joystick, guid, name in self.pad_list:
            try:
                if not joystick.get_init():
                    joystick.init()
                if joystick.get_button(0):
                    self.timer.stop()
                    self.accept()
                    self.on_guid_selected(joystick, guid, name)
                    return
            except pygame.error as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
