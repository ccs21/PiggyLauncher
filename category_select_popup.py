"""게임에 붙일 사용자 카테고리를 선택하고 저장하는 화면.
표시 이름과 각 게임 메타데이터에 저장된 목록을 함께 살핀다.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QFont
import os, json

CATEGORY_PATH = os.path.join("configs", "user_categories.json")


class DraggableScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none;")
        self._drag_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos:
            delta = self._drag_pos.y() - event.pos().y()
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta)
            self._drag_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class CategorySelectPopup(QDialog):
    def __init__(self, game_meta, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.theme = theme_manager.theme
        self.game_meta = game_meta
        self.selected_categories = set(game_meta.get("categories", []))
        self.checkbox_keys = []
        self.current_index = 0
        self.row_widgets = {}
        self.setWindowTitle("카테고리 설정")
        self.setFixedSize(
            self.theme_manager.scale_px(600), self.theme_manager.scale_px(800)
        )
        font_cfg = self.theme.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = self.theme_manager.scale_px(font_cfg.get("size", 36))
        font_bold = font_cfg.get("bold", False)
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#000000"
        )
        self.setStyleSheet(
            f"\n            QDialog {{\n                background-color: {bg_color};\n                border: 2px solid black;\n            }}\n            QLabel {{\n                color: {font_cfg.get('color', '#000000')};\n            }}\n        "
        )
        layout = QVBoxLayout(self)
        margin = self.theme_manager.scale_px(30)
        layout.setContentsMargins(margin, margin, margin, margin)
        self.scroll = DraggableScrollArea()
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background-color: {bg_color};")
        self.scroll.setWidget(self.scroll_content)
        self.vbox = QVBoxLayout(self.scroll_content)
        self.vbox.setSpacing(0)
        layout.addWidget(self.scroll)
        self.checkboxes = {}
        self.load_categories()
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = font_cfg.get("bold", False)
        font_color = font_cfg.get("color", "#FFFFFF")
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        self.register_btn = QPushButton("등록")
        self.register_btn.setFont(font)
        self.register_btn.setFixedHeight(self.theme_manager.scale_px(70))
        btn_cfg = self.theme.get("buttons.register", {})
        btn_bg_color = btn_cfg.get("background", "#007ACC")
        btn_text_color = btn_cfg.get("text_color", font_color)
        self.register_btn.setStyleSheet(
            f"\n            background-color: {btn_bg_color};\n            color: {btn_text_color};\n            border: 3px solid transparent;\n            border-radius: {self.theme_manager.scale_px(10)}px;\n        "
        )
        self.register_btn.clicked.connect(self.apply_categories)
        layout.addWidget(self.register_btn)
        self.update_focus()

    def apply_popup_label_style(self, widget):
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = font_cfg.get("bold", False)
        font_color = font_cfg.get("color", "#FFFFFF")
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        widget.setFont(font)
        widget.setStyleSheet(
            f"color: {font_color}; background: transparent; border: none;"
        )

    def load_categories(self):
        if os.path.exists(CATEGORY_PATH):
            with open(CATEGORY_PATH, "r", encoding="utf-8") as f:
                categories = json.load(f)
        else:
            categories = []
        for name in categories:
            row = QWidget()
            row.setFocusPolicy(Qt.StrongFocus)
            self.row_widgets[name] = row
            layout = QHBoxLayout(row)
            layout.setContentsMargins(
                self.theme_manager.scale_px(10),
                self.theme_manager.scale_px(10),
                self.theme_manager.scale_px(10),
                self.theme_manager.scale_px(10),
            )
            layout.setSpacing(self.theme_manager.scale_px(10))
            checkbox = QCheckBox()
            checkbox.setChecked(name in self.selected_categories)
            self.checkboxes[name] = checkbox
            self.checkbox_keys.append(name)
            layout.addWidget(checkbox)
            label = QLabel(name)
            label.setMinimumWidth(self.theme_manager.scale_px(400))
            self.apply_popup_label_style(label)
            layout.addWidget(label)

            def make_click_handler(category_name):

                def handler(event: QMouseEvent):
                    if event.type() == QMouseEvent.MouseButtonRelease:
                        self.toggle_checkbox(category_name)
                        self.current_index = self.checkbox_keys.index(category_name)
                        self.update_focus()
                    else:
                        event.ignore()

                return handler

            row.mouseReleaseEvent = make_click_handler(name)
            self.vbox.addWidget(row)
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet(
                f"\n                background-color: #CCC;\n                min-height: {self.theme_manager.scale_px(1)}px;\n                max-height: {self.theme_manager.scale_px(1)}px;\n            "
            )
            self.vbox.addWidget(line)

    def toggle_checkbox(self, name):
        cb = self.checkboxes.get(name)
        if cb:
            cb.setChecked(not cb.isChecked())

    def apply_categories(self):
        selected = [name for (name, cb) in self.checkboxes.items() if cb.isChecked()]
        meta_path = os.path.join(
            "l_libs",
            self.game_meta["platform"],
            str(self.game_meta["appid"]),
            "meta.json",
        )
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            else:
                meta = {}
            meta["categories"] = selected
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        parent = self.parent()
        while parent:
            if hasattr(parent, "central_content"):
                parent.central_content.load_registered_games()
                current_tab_index = parent.central_content.tab_bar.currentIndex()
                parent.central_content.on_category_changed(current_tab_index)
                parent.central_content.render_cards()
                break
            parent = parent.parent()
        self.accept()

    def update_focus(self):
        list_bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#000000"
        )
        focus_color = self.theme_manager.get("background.cat_focus", {}).get(
            "value", "#e0f0ff"
        )
        for i, name in enumerate(self.checkbox_keys):
            row = self.row_widgets.get(name)
            if row:
                bg_color = focus_color if i == self.current_index else list_bg_color
                row.setStyleSheet(f"background-color: {bg_color}; border: none;")
        btn_cfg = self.theme.get("buttons.register", {})
        btn_bg_color = btn_cfg.get("background", "#007ACC")
        btn_text_color = btn_cfg.get("text_color", "#FFFFFF")
        border = (
            "5px solid orange"
            if self.current_index == len(self.checkbox_keys)
            else "3px solid transparent"
        )
        self.register_btn.setStyleSheet(
            f"\n            background-color: {btn_bg_color};\n            color: {btn_text_color};\n            font-size: {self.theme_manager.scale_px(24)}px;\n            font-weight: bold;\n            border: {border};\n            border-radius: {self.theme_manager.scale_px(10)}px;\n        "
        )

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_W:
            if self.current_index > 0:
                self.current_index -= 1
                self.update_focus()
        elif event.key() == Qt.Key_S:
            if self.current_index < len(self.checkbox_keys):
                self.current_index += 1
                self.update_focus()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.current_index < len(self.checkbox_keys):
                self.toggle_checkbox(self.checkbox_keys[self.current_index])
                self.update_focus()
            else:
                self.apply_categories()
        elif event.key() == Qt.Key_Escape:
            self.reject()

    def closeEvent(self, event):
        super().closeEvent(event)
