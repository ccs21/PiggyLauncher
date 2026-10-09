"""하단의 보기 전환과 교재 안내 진입점.
카드/그리드 전환은 중앙 영역에 전달하고 아이콘은 현재 보기 상태에 맞춘다.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QFont, QKeyEvent
from PySide6.QtCore import Qt, QSize, QEvent


class BottomBar(QWidget):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.central_content = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.update_available = False
        self.setup_ui()

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_Return
            and self.central_content
            and (self.central_content._focus_area == "bottom")
        ):
            from update_popup import UpdatePopup

            popup = UpdatePopup(self.theme_manager, self.window())
            popup.exec()
            return
        if event.key() == Qt.Key_W and self.central_content:
            self.central_content._focus_area = "card"
            self.clearFocus()
            self.setFocusPolicy(Qt.NoFocus)
            self.central_content.setFocus(Qt.OtherFocusReason)
            self.central_content.render_cards()

    def eventFilter(self, watched, event):
        if watched == self.btn_update and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_W and self.central_content:
                self.central_content._focus_area = "card"
                self.central_content.setFocus(Qt.OtherFocusReason)
                self.central_content.render_cards()
                return True
        return super().eventFilter(watched, event)

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(
            self.theme_manager.scale_px(40), 0, self.theme_manager.scale_px(50), 0
        )
        layout.setSpacing(self.theme_manager.scale_px(10))
        bg = self.theme_manager.get(
            "background.bottom_bar", {"type": "color", "value": "transparent"}
        )
        if bg["type"] == "color":
            self.setStyleSheet(f"background-color: {bg['value']};")
        else:
            self.setStyleSheet("background-color: transparent;")
        self.btn_update = QPushButton()
        self.btn_update.setFixedSize(
            self.theme_manager.scale_px(80), self.theme_manager.scale_px(80)
        )
        self.btn_update.setIconSize(
            QSize(self.theme_manager.scale_px(80), self.theme_manager.scale_px(80))
        )
        self.btn_update.setStyleSheet("border: none; background: transparent;")
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_update.setText("교재")
        self.btn_update.setToolTip("업데이트 API 학습 안내")
        layout.addWidget(self.btn_update)
        layout.addStretch()
        b_icon_path = self.theme_manager.get(
            "icons.view_change", "icons/view_change.png"
        )
        self.b_button_icon = QPushButton()
        self.b_button_icon.setIcon(QIcon(b_icon_path))
        self.b_button_icon.setIconSize(
            QSize(self.theme_manager.scale_px(80), self.theme_manager.scale_px(80))
        )
        self.b_button_icon.setCursor(Qt.PointingHandCursor)
        self.b_button_icon.setStyleSheet("background-color: transparent; border: none;")
        self.b_button_icon.clicked.connect(self.toggle_view_mode)
        layout.addWidget(self.b_button_icon)
        self.btn_update.setFocusPolicy(Qt.StrongFocus)
        self.btn_update.installEventFilter(self)
        self.setLayout(layout)

    def update_view_button_icon(self):
        cc = self.parent().parent().central_content
        if cc.is_grid_mode:
            icon_path = self.theme_manager.get(
                "icons.view_default", "icons/view_default.png"
            )
        else:
            icon_path = self.theme_manager.get(
                "icons.view_change", "icons/view_change.png"
            )
        self.b_button_icon.setIcon(QIcon(icon_path))

    def toggle_view_mode(self):
        central_content = self.parent().parent().central_content
        central_content._focus_area = "card"
        central_content.setFocus(Qt.OtherFocusReason)
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        central_content.keyPressEvent(event)
        self.update_view_button_icon()

    def _get_font(self, key, default_size=20):
        f = self.theme_manager.get("fonts", {}).get(key, {})
        font = QFont(f.get("family", "맑은 고딕"), f.get("size", default_size))
        font.setBold(f.get("bold", False))
        font.setItalic(f.get("italic", False))
        return font

    def on_update_clicked(self):
        from update_popup import UpdatePopup

        popup = UpdatePopup(self.theme_manager, self.window())
        popup.exec()
