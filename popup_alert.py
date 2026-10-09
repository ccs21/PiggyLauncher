"""테마에 맞는 간단한 안내 대화상자.
호출자는 메시지와 부모를 제공하며, 창의 표시·확인 동작은 Qt 이벤트 루프에서 처리한다.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent


class CustomAlertDialog(QDialog):
    def __init__(self, title, message, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        scale_px = self.theme_manager.scale_px
        self.setWindowTitle(title)
        self.setFixedSize(scale_px(520), scale_px(300))
        self.setWindowFlags(
            Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowStaysOnTopHint
        )
        theme = self.theme_manager.get("popup", {})
        bg_color = theme.get("background_color", "#FFFFFF")
        scale_px(theme.get("font_size", 22))
        btn_bg = theme.get("confirm_button_background_color", "#007ACC")
        scale_px(theme.get("button_font_size", 20))
        border_px = scale_px(3)
        padding_px = scale_px(10)
        radius_px = scale_px(10)
        self.setStyleSheet("")
        self.setStyleSheet(f"background-color: {bg_color};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            scale_px(40), scale_px(40), scale_px(40), scale_px(40)
        )
        layout.setSpacing(scale_px(30))
        label_font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        label_family = label_font_cfg.get("family", "맑은 고딕")
        label_size = label_font_cfg.get("size", 22)
        label_bold = label_font_cfg.get("bold", False)
        label_color = label_font_cfg.get("color", "#000000")
        label_font = QFont(label_family, label_size)
        label_font.setBold(label_bold)
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setFont(label_font)
        label.setStyleSheet(
            f"\n            font-family: '{label_family}';\n            font-size: {label_size}px;\n            font-weight: {('bold' if label_bold else 'normal')};\n            color: {label_color};\n            border: none;\n        "
        )
        layout.addWidget(label)
        btn_font_cfg = self.theme_manager.get("fonts.팝업버튼", label_font_cfg)
        btn_family = btn_font_cfg.get("family", "맑은 고딕")
        btn_size = btn_font_cfg.get("size", 20)
        btn_bold = btn_font_cfg.get("bold", True)
        btn_text_color = btn_font_cfg.get("color", "#FFFFFF")
        btn_font = QFont(btn_family, btn_size)
        btn_font.setBold(btn_bold)
        self.ok_button = QPushButton("확인")
        self.ok_button.setFont(btn_font)
        self.ok_button.setFixedSize(scale_px(180), scale_px(60))
        font_weight = "700" if btn_bold else "400"
        self.ok_button.setStyleSheet(
            f"\n            QPushButton {{\n                background-color: {btn_bg};\n                color: {btn_text_color};\n                border: {border_px}px solid orange;\n                border-radius: {radius_px}px;\n                padding: {padding_px}px;\n                font-family: '{btn_family}';\n                font-size: {btn_size}px;\n                font-weight: {font_weight};\n            }}\n            QPushButton:pressed {{\n                background-color: {btn_bg};\n                color: {btn_text_color};\n                font-family: '{btn_family}';\n                font-size: {btn_size}px;\n                font-weight: {font_weight};\n            }}\n        "
        )
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, alignment=Qt.AlignCenter)
        self.ok_button.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.ok_button.click()
        elif key == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)
