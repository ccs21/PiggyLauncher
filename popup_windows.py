"""테마·크기·창 플래그를 준비하는 팝업 기본 클래스.
상속된 init_ui를 기본 생성자에서 호출하므로 하위 클래스의 초기화 순서가 중요하다.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import Qt


class BasePopup(QDialog):
    """공통 창 속성을 준비한 뒤 하위 클래스의 init_ui를 한 번 호출한다.

    하위 클래스는 init_ui에서 읽는 데이터를 super().__init__ 이전에 넣어야
    한다. super 호출 뒤 init_ui를 다시 호출하면 위젯·시그널이 중복 생성된다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.theme_manager = getattr(self, "theme_manager", None) or getattr(
            parent, "theme_manager", None
        )
        self.init_ui()
        self.resize_popup()
        self.setFocus()

    def init_ui(self):
        self.setLayout(QVBoxLayout())
        if self.theme_manager:
            margin = self.theme_manager.scale_px(20)
        else:
            margin = 20
        self.layout().setContentsMargins(margin, margin, margin, margin)
        popup_type = (
            "settings_popup"
            if "Settings" in self.__class__.__name__
            else "update_popup"
        )
        bg_cfg = (
            self.theme_manager.get(
                f"background.{popup_type}", {"type": "color", "value": "#FFFFFF"}
            )
            if self.theme_manager
            else {}
        )
        if bg_cfg.get("type") == "color":
            color = bg_cfg.get("value", "#FFFFFF")
            border = (
                self.theme_manager.get("focus.popup.border_color", "#888")
                if self.theme_manager
                else "#888"
            )
            border_width = (
                self.theme_manager.scale_px(
                    self.theme_manager.get("focus.popup.border_width", 2)
                )
                if self.theme_manager
                else 2
            )
            radius = (
                self.theme_manager.scale_px(
                    self.theme_manager.get("focus.popup.radius", 10)
                )
                if self.theme_manager
                else 10
            )
            self.setStyleSheet(
                f"\n                background-color: {color};\n                border: {border_width}px solid {border};\n                border-radius: {radius}px;\n            "
            )
        elif bg_cfg.get("type") == "image":
            image_path = (
                self.theme_manager.get("bg." + bg_cfg.get("value", ""))
                if self.theme_manager
                else ""
            )
            border_width = self.theme_manager.scale_px(2) if self.theme_manager else 2
            radius = self.theme_manager.scale_px(10) if self.theme_manager else 10
            self.setStyleSheet(
                f"\n                background-image: url({image_path});\n                background-position: center;\n                background-repeat: no-repeat;\n                background-size: cover;\n                border: {border_width}px solid #888;\n                border-radius: {radius}px;\n            "
            )
        else:
            border_width = self.theme_manager.scale_px(2) if self.theme_manager else 2
            radius = self.theme_manager.scale_px(10) if self.theme_manager else 10
            self.setStyleSheet(
                f"\n                background-color: white;\n                border: {border_width}px solid #888;\n                border-radius: {radius}px;\n            "
            )

    def resize_popup(self):
        screen_size = self.parent().size() if self.parent() else self.screen().size()
        self.resize(screen_size.width() * 0.9, screen_size.height() * 0.9)
        if self.parent():
            center = self.parent().geometry().center()
            geo = self.geometry()
            geo.moveCenter(center)
            self.setGeometry(geo)
