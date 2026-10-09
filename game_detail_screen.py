"""게임 상세 화면과 실행·복귀 흐름. 시작 확인과 종료 판정은 서로 다른 단계다."""

import logging
import os
import json
import random
import psutil
import win32gui
import win32process
import time
from PySide6.QtCore import (
    Qt,
    QSize,
    QMetaObject,
    QPropertyAnimation,
    QRect,
    QEasingCurve,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QApplication,
)
from PySide6.QtGui import QPixmap, QIcon
from popup_windows import BasePopup
from batch_setting_popup import BatchSettingPopup
from graphic_setting_popup import GraphicSettingPopup
from datetime import datetime
from system_config_handler import apply_preset, restore_system_settings
from notification_manager import notification_manager


class DraggableScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.pos() - self._drag_pos
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self._drag_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class GameDetailScreen(BasePopup):
    # 감시 스레드는 시그널만 보낸다. Qt 위젯과 알림 타이머는 GUI 스레드 소유다.
    restore_requested = Signal()
    reattach_requested = Signal()

    def __init__(
        self,
        game_metadata=None,
        theme_manager=None,
        app_id=None,
        platform=None,
        parent=None,
    ):
        self.theme_manager = theme_manager
        self.game_metadata = game_metadata
        self.app_id = app_id
        self.platform = platform
        self.scaled_pixmap_cache = {}
        super().__init__(parent)
        self.restore_requested.connect(self._restore_launcher_ui, Qt.QueuedConnection)
        self.reattach_requested.connect(self._reattach_ui, Qt.QueuedConnection)

    def init_ui(self):
        self.header_path = None
        try:
            meta_path = os.path.join(
                "l_libs", self.platform, str(self.app_id), "meta.json"
            )
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.header_path = os.path.join(
                    "l_libs", self.platform, str(self.app_id), meta.get("header", "")
                )
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.resize_popup()
        super().init_ui()
        theme_color = self.theme_manager.get(
            "background.game_detail.value", "#555555"
        ).lstrip("#")
        r = int(theme_color[0:2], 16)
        g = int(theme_color[2:4], 16)
        b = int(theme_color[4:6], 16)
        alpha = 0.6
        screenshot_path = self.get_random_screenshot_path()
        self.bg_color = QLabel(self)
        self.bg_color.setGeometry(0, 0, self.width(), self.height())
        self.bg_color.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {alpha});")
        self.bg_image = QLabel(self)
        self.bg_image.setObjectName("bg_image")
        self.bg_image.setGeometry(0, 0, self.width(), self.height())
        bg_pixmap = None
        if screenshot_path and os.path.exists(screenshot_path):
            bg_pixmap = QPixmap(screenshot_path)
        else:
            fallback_key = self.theme_manager.get("icons.no_bg", "")
            fallback_path = (
                os.path.join(os.getcwd(), fallback_key) if fallback_key else ""
            )
            if fallback_path and os.path.exists(fallback_path):
                bg_pixmap = QPixmap(fallback_path)
        if bg_pixmap and (not bg_pixmap.isNull()):
            key = f"{screenshot_path}|{self.width()}x{self.height()}"
            if key in self.scaled_pixmap_cache:
                scaled = self.scaled_pixmap_cache[key]
            else:
                scaled = bg_pixmap.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                self.scaled_pixmap_cache[key] = scaled
            self.bg_image.setPixmap(scaled)
        self.resize_sections()
        QTimer.singleShot(10, self.setup_top_section)
        QTimer.singleShot(0, self.clean_up_empty_labels)

    def resize_sections(self):
        if not hasattr(self, "top_section"):
            self.top_section = QWidget(self)
            self.top_section.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            self.top_section.setObjectName("top_section")
            self.middle_section = QWidget(self)
            self.middle_section.setObjectName("middle_section")
            self.middle_section.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            self.middle_left = QLabel(self.middle_section)
            self.middle_left.setObjectName("middle_left")
            self.middle_left.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            self.middle_center = QLabel(self.middle_section)
            self.middle_center.setObjectName("middle_center")
            self.middle_center.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            self.middle_right = QLabel(self.middle_section)
            self.middle_right.setObjectName("middle_right")
            self.middle_right.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            self.bottom_section = QLabel(self)
            self.bottom_section.setObjectName("bottom_section")
            self.bottom_section.setStyleSheet(
                "background-color: transparent; border: none;"
            )
        total_width = self.width()
        total_height = self.height()
        top_height = int(total_height * 0.1)
        middle_height = int(total_height * 0.4)
        bottom_height = total_height - top_height - middle_height
        self.bg_image.setGeometry(0, 0, total_width, total_height)
        self.top_section.setGeometry(0, 0, total_width, top_height)
        self.middle_section.setGeometry(0, top_height, total_width, middle_height)
        self.bottom_section.setGeometry(
            0, top_height + middle_height, total_width, bottom_height
        )
        left_width = int(total_width * 0.33)
        center_width = int(total_width * 0.17)
        right_width = total_width - left_width - center_width
        self.middle_left.setGeometry(0, 0, left_width, middle_height)
        self.middle_center.setGeometry(left_width, 0, center_width, middle_height)
        self.middle_right.setGeometry(
            left_width + center_width, 0, right_width, middle_height
        )
        header_pixmap = None
        if self.header_path and os.path.exists(self.header_path):
            header_pixmap = QPixmap(self.header_path)
        else:
            icon_path = self.theme_manager.get("icons.no_header", "")
            exe_dir = os.getcwd()
            fallback_path = os.path.join(exe_dir, icon_path)
            if fallback_path and os.path.exists(fallback_path):
                header_pixmap = QPixmap(fallback_path)
        if header_pixmap and (not header_pixmap.isNull()):
            self.header_label = QLabel(self.middle_left)
            self.header_label.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            target_width = left_width - self.theme_manager.scale_px(40)
            target_height = middle_height - self.theme_manager.scale_px(40)
            key = f"{self.header_path}|{target_width}x{target_height}"
            if key in self.scaled_pixmap_cache:
                scaled_pixmap = self.scaled_pixmap_cache[key]
            else:
                scaled_pixmap = header_pixmap.scaled(
                    target_width,
                    target_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.scaled_pixmap_cache[key] = scaled_pixmap
            self.header_label.setPixmap(scaled_pixmap)
            x_offset = (
                self.theme_manager.scale_px(20)
                + (target_width - scaled_pixmap.width()) // 2
            )
            y_offset = (
                self.theme_manager.scale_px(20)
                + (target_height - scaled_pixmap.height()) // 2
            )
            self.header_label.setGeometry(
                x_offset, y_offset, scaled_pixmap.width(), scaled_pixmap.height()
            )
            self.header_label.show()
        self.middle_center_container = QWidget(self.middle_center)
        self.middle_center_container.setGeometry(0, 0, center_width, middle_height)
        self.middle_center_container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self.middle_center_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.theme_manager.scale_px(33))
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        self.button_list = []

        def create_icon_button(icon_path, on_click):
            btn = QPushButton()
            btn.setFocusPolicy(Qt.StrongFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "\n                QPushButton {\n                    background-color: transparent;\n                    border: 2px solid transparent;\n                }\n                QPushButton:focus {\n                    border: 4px solid orange;\n                }\n            "
            )
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(
                QSize(self.theme_manager.scale_px(245), self.theme_manager.scale_px(59))
            )
            btn.setFixedSize(
                self.theme_manager.scale_px(250), self.theme_manager.scale_px(64)
            )
            btn.clicked.connect(on_click)
            self.button_list.append(btn)
            return btn

        run_icon = self.theme_manager.get("icons.run_game", "")
        batch_icon = self.theme_manager.get("icons.batch_setting", "")
        run_btn = create_icon_button(run_icon, self.run_game)
        layout.addWidget(run_btn)
        graphic_icon = self.theme_manager.get("icons.graphic_config", "")
        graphic_btn = create_icon_button(graphic_icon, self.open_graphic_setting)
        layout.addWidget(graphic_btn)
        batch_btn = create_icon_button(batch_icon, self.open_batch_setting)
        layout.addWidget(batch_btn)
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        QTimer.singleShot(50, lambda: self.button_list[0].setFocus())
        if self.bg_image.pixmap():
            self.bg_image.setPixmap(
                self.bg_image.pixmap().scaled(
                    total_width,
                    total_height,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
            )
        right_width = self.middle_right.width()
        right_height = self.middle_right.height()
        top_height = int(right_height * 1 / 3)
        bottom_height = right_height - top_height
        for child in self.middle_right.children():
            if isinstance(child, QWidget):
                child.setParent(None)
        self.top_right_section = QWidget(self.middle_right)
        self.top_right_section.setObjectName("top_right_section")
        self.top_right_section.setGeometry(0, 0, right_width, top_height)
        self.top_right_section.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        game_title = self.game_metadata.get("title", "제목 없음")
        font_cfg = self.theme_manager.get("fonts.상세_제목", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 48)
        font_bold = font_cfg.get("bold", True)
        font_weight = "bold" if font_bold else "normal"
        font_color = font_cfg.get("color", "#FFFFFF")
        self.title_label = QLabel(game_title, self.top_right_section)
        self.title_label.setObjectName("game_title_label")
        self.title_label.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_weight};\n            background-color: transparent;\n        "
        )
        self.title_label.adjustSize()
        label_width = self.title_label.width()
        section_width = self.top_right_section.width()
        section_height = self.top_right_section.height()
        right_margin = 50
        visible_width = section_width - right_margin
        if label_width <= visible_width:
            x_pos = section_width - label_width - right_margin
            y_pos = int((section_height - self.title_label.height()) / 2)
            self.title_label.move(x_pos, y_pos)
        else:
            x_pos = section_width
            y_pos = int((section_height - self.title_label.height()) / 2)
            self.title_label.setGeometry(
                x_pos, y_pos, label_width, self.title_label.height()
            )
            self.title_scroll_anim = QPropertyAnimation(self.title_label, b"geometry")
            self.title_scroll_anim.setDuration(30000)
            self.title_scroll_anim.setStartValue(
                QRect(x_pos, y_pos, label_width, self.title_label.height())
            )
            self.title_scroll_anim.setEndValue(
                QRect(-label_width, y_pos, label_width, self.title_label.height())
            )
            self.title_scroll_anim.setLoopCount(-1)
            self.title_scroll_anim.setEasingCurve(QEasingCurve.Linear)
            self.title_scroll_anim.start()
        self.bottom_right_section = QWidget(self.middle_right)
        self.bottom_right_section.setObjectName("bottom_right_section")
        self.bottom_right_section.setGeometry(0, top_height, right_width, bottom_height)
        self.bottom_right_section.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        meta_cfg = self.theme_manager.get("fonts.상세_메타", {})
        meta_font = meta_cfg.get("family", "맑은 고딕")
        meta_size = meta_cfg.get("size", 36)
        meta_bold = meta_cfg.get("bold", True)
        meta_weight = "bold" if meta_bold else "normal"
        meta_color = meta_cfg.get("color", "#CCCCCC")
        meta_path = os.path.join("l_libs", self.platform, str(self.app_id), "meta.json")
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
                developer = meta_data.get("developer", "알 수 없음")
                publisher = meta_data.get("publisher", "알 수 없음")
                release_date_raw = meta_data.get("release_date", "알 수 없음")
        except Exception:
            developer = publisher = release_date_raw = "알 수 없음"
        description = meta_data.get("description", "")
        desc_cfg = self.theme_manager.get("fonts.상세_메타", {})
        desc_font = desc_cfg.get("family", "맑은 고딕")
        desc_size = desc_cfg.get("size", 36)
        desc_bold = desc_cfg.get("bold", True)
        desc_weight = "bold" if desc_bold else "normal"
        desc_color = desc_cfg.get("color", "#000000")
        for child in self.bottom_section.children():
            if isinstance(child, QScrollArea):
                child.setParent(None)
        self.scroll_area = DraggableScrollArea(self.bottom_section)
        padding = self.theme_manager.scale_px(50)
        self.scroll_area.setGeometry(
            padding,
            0,
            self.bottom_section.width() - padding * 2,
            self.bottom_section.height(),
        )
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet(
            f"\n            color: {desc_color};\n            font-family: '{desc_font}';\n            font-size: {desc_size}px;\n            font-weight: {desc_weight};\n            background-color: transparent;\n        "
        )
        self.scroll_area.setWidget(self.description_label)
        try:
            date_obj = datetime.strptime(release_date_raw, "%d %b, %Y")
            release_date = f"{date_obj.year}년 {date_obj.month}월 {date_obj.day}일"
        except Exception:
            release_date = release_date_raw
        meta_layout = QVBoxLayout(self.bottom_right_section)
        meta_layout.setContentsMargins(0, 0, self.theme_manager.scale_px(50), 0)
        meta_layout.setSpacing(self.theme_manager.scale_px(15))

        def make_meta_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"\n                color: {meta_color};\n                font-family: '{meta_font}';\n                font-size: {meta_size}px;\n                font-weight: {meta_weight};\n                background-color: transparent;\n                qproperty-alignment: AlignRight;\n            "
            )
            lbl.setWordWrap(True)
            return lbl

        meta_layout.addWidget(make_meta_label(f"개발사 : {developer}"))
        meta_layout.addWidget(make_meta_label(f"배급사 : {publisher}"))
        meta_layout.addWidget(make_meta_label(f"출시일 : {release_date}"))
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        meta_layout.addItem(spacer)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if not hasattr(self, "button_list") or not self.button_list:
            return
        focused_index = -1
        for i, btn in enumerate(self.button_list):
            if btn.hasFocus():
                focused_index = i
                break
        if event.key() in (Qt.Key_W, Qt.Key_Up):
            next_index = max(0, focused_index - 1)
            self.button_list[next_index].setFocus()
        elif event.key() in (Qt.Key_S, Qt.Key_Down):
            next_index = min(len(self.button_list) - 1, focused_index + 1)
            self.button_list[next_index].setFocus()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if 0 <= focused_index < len(self.button_list):
                self.button_list[focused_index].click()

    def get_random_screenshot_path(self):
        """스크린샷 후보에서 표시할 이미지를 고른다. 후보가 없을 때의 기본 배경 처리는 호출부가 담당한다."""
        try:
            meta_path = os.path.join(
                "l_libs", self.platform, str(self.app_id), "meta.json"
            )
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                screenshots = meta.get("screenshots", [])
                if screenshots:
                    chosen = random.choice(screenshots)
                    return os.path.join(
                        "l_libs", self.platform, str(self.app_id), chosen
                    )
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        return None

    def setup_top_section(self):
        icon_size = self.theme_manager.scale_px(64)
        top_height = self.top_section.height()
        self.icon_label = QLabel(self.top_section)
        self.icon_label.setObjectName("platform_icon")
        self.icon_label.setFixedSize(icon_size, icon_size)
        self.icon_label.setStyleSheet("background-color: transparent; border: none;")
        icon_y = int((top_height - self.theme_manager.scale_px(60)) / 2)
        self.icon_label.move(self.theme_manager.scale_px(40), icon_y)
        platform_map = {
            "steam": "Steam",
            "epic": "Epic",
            "gog": "GOG",
            "stove": "STOVE",
            "user": "User",
        }
        platform_key = platform_map.get(self.platform.lower(), "User")
        icon_path = self.theme_manager.get(f"platform_icons.{platform_key}", None)
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            scaled_icon = pixmap.scaled(
                icon_size - self.theme_manager.scale_px(8),
                icon_size - self.theme_manager.scale_px(8),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.icon_label.setPixmap(scaled_icon)
        self.icon_label.raise_()
        self.icon_label.show()
        platform_text_map = {
            "steam": "STEAM",
            "epic": "EPIC GAMES",
            "gog": "GOG.COM",
            "stove": "STOVE",
            "user": "사용자 등록",
        }
        platform_text = platform_text_map.get(self.platform.lower(), "알 수 없음")
        font_cfg = self.theme_manager.get("fonts.상세_플랫폼", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 48)
        font_bold = font_cfg.get("bold", True)
        font_weight = "bold" if font_bold else "normal"
        font_color = font_cfg.get("color", "#000000")
        style = f"color: {font_color}; font-size: {font_size}px; font-weight: {font_weight}; font-family: '{font_family}'; background-color: transparent; border: none;"
        self.text_label = QLabel(platform_text, self.top_section)
        self.text_label.setObjectName("platform_label")
        self.text_label.setStyleSheet(style)
        self.text_label.adjustSize()
        text_x = self.theme_manager.scale_px(40 + 60 + 10)
        text_y = int((top_height - self.text_label.height()) / 2)
        self.text_label.move(text_x, text_y)
        self.text_label.raise_()
        self.text_label.show()
        self.delete_label = QLabel(self.top_section)
        self.delete_label.setObjectName("delete_button")
        self.delete_label.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        self.delete_label.setScaledContents(True)
        self.delete_label.setStyleSheet("background-color: transparent; border: none;")
        delete_path = self.theme_manager.get("icons.delete", "icons/delete.png")
        delete_pixmap = QPixmap(delete_path)
        if not delete_pixmap.isNull():
            self.delete_label.setPixmap(delete_pixmap)
        delete_x = self.top_section.width() - sum(
            [self.theme_manager.scale_px(60 + 20) * 4]
        )
        delete_y = int((top_height - self.theme_manager.scale_px(60)) / 2)
        self.delete_label.move(delete_x, delete_y)
        self.delete_label.raise_()
        self.delete_label.show()
        self.delete_label.mousePressEvent = lambda event: self.on_delete_clicked()
        self.edit_label = QLabel(self.top_section)
        self.edit_label.setObjectName("edit_button")
        self.edit_label.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        self.edit_label.setScaledContents(True)
        self.edit_label.setStyleSheet("background-color: transparent; border: none;")
        edit_path = self.theme_manager.get("icons.edit", "icons/edit.png")
        edit_pixmap = QPixmap(edit_path)
        if not edit_pixmap.isNull():
            self.edit_label.setPixmap(edit_pixmap)
        edit_x = self.top_section.width() - sum(
            [self.theme_manager.scale_px(60 + 20) * 3]
        )
        edit_y = delete_y
        self.edit_label.move(edit_x, edit_y)
        self.edit_label.raise_()
        self.edit_label.show()
        self.edit_label.mousePressEvent = lambda event: self.open_edit_popup()
        self.category_label = QLabel(self.top_section)
        self.category_label.setObjectName("category_button")
        self.category_label.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        self.category_label.setScaledContents(True)
        self.category_label.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        category_path = self.theme_manager.get("icons.category", "icons/category.png")
        category_pixmap = QPixmap(category_path)
        if not category_pixmap.isNull():
            self.category_label.setPixmap(category_pixmap)
        category_x = self.top_section.width() - sum(
            [self.theme_manager.scale_px(60 + 20) * 2]
        )
        category_y = delete_y
        self.category_label.move(category_x, category_y)
        self.category_label.raise_()
        self.category_label.show()
        self.category_label.mousePressEvent = lambda event: self.open_category_popup()
        self.close_label = QLabel(self.top_section)
        self.close_label.setObjectName("close_button")
        self.close_label.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        self.close_label.setScaledContents(True)
        self.close_label.setStyleSheet("background-color: transparent; border: none;")
        close_path = self.theme_manager.get("icons.close", "icons/close.png")
        close_pixmap = QPixmap(close_path)
        if not close_pixmap.isNull():
            self.close_label.setPixmap(close_pixmap)
        close_x = self.top_section.width() - self.theme_manager.scale_px(60 + 20)
        close_y = delete_y
        self.close_label.move(close_x, close_y)
        self.close_label.raise_()
        self.close_label.show()
        self.close_label.mousePressEvent = lambda event: self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_sections()

    def clean_up_empty_labels(self):
        for child in self.findChildren(QLabel):
            geo = child.geometry()
            size_ok = (
                geo.x() == 0
                and geo.y() == 0
                and (geo.width() == 100)
                and (geo.height() == 30)
            )
            content_empty = not child.text() and child.pixmap() is None
            name_empty = not child.objectName()
            if size_ok and content_empty and name_empty:
                child.hide()
                child.deleteLater()

    def run_game(self):
        """프리셋 적용 → 실행 → 시작 안정화 확인 → 종료 감시 순서로 진행한다.
        UI를 숨기는 일은 GUI 스레드에서, 반복 프로세스 조회는 Python Thread에서 한다.
        실행 실패도 정상 종료와 같은 복귀 경로를 사용해 볼륨·해상도·입력 상태를 복구한다.
        이 교재는 Classic의 프로세스 이름 기반 판정을 보존한다. 2.0의 종료 감지 구현은 아니다.
        """
        import subprocess, time
        from threading import Thread
        from datetime import datetime

        self.close()
        if self.parent():
            self.parent().showNormal()
            time.sleep(0.05)
            self.parent().showMinimized()
            if hasattr(self.parent(), "is_game_running"):
                self.parent().is_game_running = True
        locale_emulate = False
        locale_path = ""
        preset_result = apply_preset(
            self.platform, self.app_id, self.theme_manager, self
        )
        if not preset_result:
            self.restore_launcher()
            return
        else:
            preset_path = os.path.join(
                "configs", f"{self.platform}_{self.app_id}_preset.json"
            )
            if os.path.exists(preset_path):
                try:
                    with open(preset_path, "r", encoding="utf-8") as f:
                        preset = json.load(f)
                        locale_emulate = preset.get("locale_emulate", False)
                        locale_path = preset.get("locale_path", "").strip()
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        exe_path = self.game_metadata.get("exe_full_path") or self.game_metadata.get(
            "exe"
        )
        if not exe_path or (
            not os.path.exists(exe_path) and (not exe_path.startswith("sgup://"))
        ):
            self.restore_launcher()
            return
        notification_manager.pause()
        batch_path = os.path.join(
            "configs", f"{self.platform}_{self.app_id}_batch.json"
        )
        processes = []
        try:
            game_proc = None
            if exe_path.startswith("sgup://"):
                os.startfile(exe_path)
            else:
                import subprocess

                DETACHED_PROCESS = 8
                if locale_emulate and os.path.exists(locale_path):
                    game_proc = subprocess.Popen(
                        [locale_path, exe_path],
                        cwd=os.path.dirname(locale_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=DETACHED_PROCESS,
                    )
                else:
                    game_proc = subprocess.Popen(
                        f'"{exe_path}"',
                        shell=True,
                        cwd=os.path.dirname(exe_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=DETACHED_PROCESS,
                    )
                logging.debug(f"[▶] 게임 실행됨 : {exe_path}")
            if game_proc:
                processes.append(game_proc)
            meta_path = os.path.join(
                "l_libs", self.platform, str(self.app_id), "meta.json"
            )
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["last_played"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        except Exception:
            self.restore_launcher()
            return

        def wait_and_then_monitor(game_proc, exe_name):
            """처음 뜬 프로세스를 곧바로 시작 확정으로 보지 않는다.
            Classic은 연속 실행 시간과 인증/업데이트 창을 함께 확인한다. 확인 후 배치를 실행하고
            wait_all로 넘어간다. 대기 수치를 바꾸면 느린 PC와 재시작 게임의 판정이 달라진다.
            """
            stable_start = None
            start_check_time = time.time()
            while True:
                is_running = any(
                    (
                        proc.info["name"]
                        and proc.info["name"].lower() == exe_name.lower()
                        for proc in psutil.process_iter(["name"])
                    )
                )
                if is_running:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= 5:
                        break
                else:
                    stable_start = None
                if time.time() - start_check_time >= 20:
                    if self._is_auth_or_update_active():
                        auth_start = time.time()
                        stable_start_b = stable_start
                        while True:
                            is_running_b = any(
                                (
                                    proc.info["name"]
                                    and proc.info["name"].lower() == exe_name.lower()
                                    for proc in psutil.process_iter(["name"])
                                )
                            )
                            if is_running_b:
                                if stable_start_b is None:
                                    stable_start_b = time.time()
                                elif time.time() - stable_start_b >= 5:
                                    stable_start = time.time() - 5.0
                                    break
                            else:
                                stable_start_b = None
                            if not self._is_auth_or_update_active():
                                post_start = time.time()
                                while time.time() - post_start < 60:
                                    is_running_c = any(
                                        (
                                            proc.info["name"]
                                            and proc.info["name"].lower()
                                            == exe_name.lower()
                                            for proc in psutil.process_iter(["name"])
                                        )
                                    )
                                    if is_running_c:
                                        if stable_start_b is None:
                                            stable_start_b = time.time()
                                        elif time.time() - stable_start_b >= 5:
                                            stable_start = time.time() - 5.0
                                            break
                                    else:
                                        stable_start_b = None
                                    time.sleep(1)
                                if (
                                    stable_start is not None
                                    and time.time() - stable_start >= 5.0
                                ):
                                    break
                                self.restore_launcher()
                                self._start_post_restore_watchdog(exe_name)
                                return
                            if time.time() - auth_start >= 300:
                                self.restore_launcher()
                                self._start_post_restore_watchdog(exe_name)
                                return
                            time.sleep(1)
                        continue
                    else:
                        self.restore_launcher()
                        return
                time.sleep(1)
            if os.path.exists(batch_path):
                with open(batch_path, "r", encoding="utf-8") as f:
                    batch_data = json.load(f)
                apps = batch_data.get("apps", [])
                delay = int(batch_data.get("delay_seconds", 0))
                if apps:
                    remaining_delay = max(0, delay - 5)
                    if remaining_delay > 0:
                        time.sleep(remaining_delay)
                    for idx, app_path in enumerate(apps):
                        try:
                            if app_path.lower().endswith((".bat", ".cmd")):
                                proc = subprocess.Popen(
                                    ["cmd.exe", "/c", app_path],
                                    cwd=os.path.dirname(app_path),
                                    shell=False,
                                )
                            else:
                                proc = subprocess.Popen(
                                    app_path, cwd=os.path.dirname(app_path), shell=False
                                )
                            processes.append(proc)
                            if idx + 1 < len(apps):
                                next_delay = int(batch_data.get("delay_seconds", 0))
                                time.sleep(next_delay)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
            self.wait_all(processes)

        exe_name = os.path.basename(exe_path)
        Thread(
            target=wait_and_then_monitor, args=(game_proc, exe_name), daemon=True
        ).start()

    def wait_all(self, processes):
        """실행 게임과 연동 프로그램 이름을 모아 생존 여부를 반복 확인한다.
        cmd.exe 같은 공용 프로세스는 제외한다. 프로세스는 열거 직후 종료될 수 있으므로
        개별 조회 오류를 허용한다. 이름 기반 감시는 같은 이름의 다른 인스턴스를 구분하지 못한다.
        """
        import time
        import os

        exe_name = self.game_metadata.get("exe", "")
        if not exe_name:
            exe_full = self.game_metadata.get("exe_full_path", "")
            exe_name = os.path.basename(exe_full) if exe_full else ""
        if not exe_name:
            for proc in processes:
                proc.wait()
            self.restore_launcher()
            return
        process_names = [exe_name.lower()]
        IGNORED_NAMES = {
            "cmd.exe",
            "conhost.exe",
            "powershell.exe",
            "python.exe",
            "py.exe",
            "steam.exe",
            "steamwebhelper.exe",
            "epicgameslauncher.exe",
            "epicwebhelper.exe",
        }
        for proc in processes:
            try:
                if proc and proc.pid:
                    p = psutil.Process(proc.pid)
                    pname = p.name().lower()
                    if pname not in IGNORED_NAMES and pname not in process_names:
                        process_names.append(pname)
                if hasattr(proc, "args"):
                    fallback_name = os.path.basename(
                        proc.args if isinstance(proc.args, str) else proc.args[0]
                    ).lower()
                    if (
                        fallback_name not in process_names
                        and fallback_name not in IGNORED_NAMES
                    ):
                        process_names.append(fallback_name)
            except Exception as e:
                logging.warning(f"[⚠️] 감시 대상 이름 추출 실패: {e}")
        if self.platform.lower() == "stove":
            process_names.append("stove.exe")
        logging.debug(f"[👁️] 감시 대상 목록: {process_names}")
        while True:
            active_found = False
            for proc in psutil.process_iter(["name"]):
                try:
                    pname = proc.info["name"]
                    if pname and pname.lower() in process_names:
                        active_found = True
                        break
                except Exception:
                    continue
            if not active_found:
                self.restore_launcher()
                break
            time.sleep(2)

    def restore_launcher(self):
        """감시 스레드에서 복귀를 요청한다. 위젯은 이 함수에서 직접 조작하지 않는다."""
        self.restore_requested.emit()

    @Slot()
    def _restore_launcher_ui(self):
        """GUI 스레드에서 설정·화면·입력·알림을 순서대로 복구한다.

        Python Thread에는 Qt 이벤트 루프가 없으므로 그 안에서 singleShot을
        예약해도 실행되지 않을 수 있다. QueuedConnection으로 이 슬롯을 호출해
        위젯 접근과 타이머 소유권을 GUI 스레드에 모은다.
        """
        restore_system_settings()
        parent = self.parent()
        while parent:
            if hasattr(parent, "central_content"):
                central = parent.central_content
                central._pending_action = "game_exit"
                central._pending_focus_app = self.app_id
                central._pending_focus_platform = self.platform
                central.render_cards()
                break
            parent = parent.parent()
        main_launcher = parent or self.parent()
        if main_launcher:
            main_launcher.is_game_running = False
            main_launcher.showFullScreen()
            main_launcher.raise_()
            main_launcher.activateWindow()
            handler = getattr(main_launcher, "gamepad_handler", None)
            if handler:
                QMetaObject.invokeMethod(handler, "hard_refresh", Qt.QueuedConnection)
        notification_manager.resume()

    @Slot()
    def _reattach_ui(self):
        """늦게 시작된 게임을 발견했을 때 GUI 측 실행 상태를 다시 잠근다."""
        parent = self.parent()
        if parent:
            parent.showMinimized()
            parent.is_game_running = True
        notification_manager.pause()

    def _any_window_with_keywords(self, keywords):
        """
        키워드 리스트 중 하나라도 포함된 '인증/업데이트/VR 안내' 보이는 최상위 창이 있으면 True.
        - 파일 탐색기/일반 대화상자/런처 프로세스/헬퍼 프로세스는 제외.
        - 제목 상의 파일 브라우저 정형 문구도 제외.
        """
        if not keywords:
            return False
        lowered = [kw.lower() for kw in keywords if kw]
        hwnds = []
        IGNORE_PROC = {
            "explorer.exe",
            "steam.exe",
            "steamwebhelper.exe",
            "epicgameslauncher.exe",
            "epicwebhelper.exe",
            "conhost.exe",
            "cmd.exe",
            "powershell.exe",
            "dwm.exe",
            "werfault.exe",
            "msiexec.exe",
        }
        IGNORE_CLASS = {"cabinetwclass", "#32770"}
        IGNORE_TITLE_SUBSTR = {
            "파일 탐색기",
            "file explorer",
            "열기",
            "save as",
            "다른 이름으로 저장",
            "open",
            "browse",
            "열기(o",
            "저장(s",
        }

        def callback(hwnd, acc):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                title = win32gui.GetWindowText(hwnd) or ""
                t = title.lower().strip()
                if not t:
                    return True
                cls = (win32gui.GetClassName(hwnd) or "").lower()
                if cls in IGNORE_CLASS:
                    return True
                for s in IGNORE_TITLE_SUBSTR:
                    if s in t:
                        return True
                (_, pid) = win32process.GetWindowThreadProcessId(hwnd)
                pname = ""
                try:
                    pname = (psutil.Process(pid).name() or "").lower()
                except Exception:
                    pass
                if pname in IGNORE_PROC:
                    return True
                for kw in lowered:
                    if kw and kw in t:
                        acc.append(hwnd)
                        break
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            return True

        try:
            win32gui.EnumWindows(callback, hwnds)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        return len(hwnds) > 0

    def _is_auth_or_update_active(self):
        """
        스팀/에픽 로그인/2FA/업데이트/검증/클라우드 동기화/VR 안내 등 단계 감지
        (성공 판정 금지: 유예용 신호)
        """
        platform = (self.platform or "").lower()
        common_auth = ["로그인", "인증", "sign in", "verification", "2fa", "two-factor"]
        vr_prompt = [
            "steamvr",
            "vr",
            "headset",
            "헤드셋",
            "put on your headset",
            "vr 기기",
        ]
        steam_keywords = (
            [
                "steam",
                "steam guard",
                "preparing to launch",
                "performing first-time setup",
                "cloud",
                "updating steam",
                "steam client update",
                "게임 파일",
                "설치",
                "검증",
            ]
            + common_auth
            + vr_prompt
        )
        epic_keywords = (
            [
                "epic games",
                "epic games launcher",
                "updating",
                "downloading",
                "installing",
                "verifying",
                "cloud",
                "verification",
                "sign in",
                "로그인",
                "인증",
                "2fa",
            ]
            + common_auth
            + vr_prompt
        )
        if platform == "steam":
            return self._any_window_with_keywords(steam_keywords)
        if platform == "epic":
            return self._any_window_with_keywords(epic_keywords)
        return False

    def _start_post_restore_watchdog(self, exe_name):
        """
        복귀 후 일정 시간 감시하다가 뒤늦게 게임이 뜨면
        → 자동으로 런처 최소화 & is_game_running=True & notification pause 재적용
        + 재부착 후 종료 감시 시작(워밍업 포함)
        """
        seconds = 120
        from threading import Thread

        def watchdog():
            deadline = time.time() + seconds
            while time.time() < deadline:
                try:
                    is_running = any(
                        (
                            proc.info["name"]
                            and proc.info["name"].lower() == exe_name.lower()
                            for proc in psutil.process_iter(["name"])
                        )
                    )
                    if is_running:
                        self.reattach_requested.emit()
                        try:
                            Thread(
                                target=self._monitor_reattached_game_until_exit,
                                args=(exe_name,),
                                daemon=True,
                            ).start()
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                        return
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
                time.sleep(1)

        Thread(target=watchdog, daemon=True).start()

    def _monitor_reattached_game_until_exit(self, exe_name):
        """
        워치독이 뒤늦게 실행된 게임에 재부착한 뒤:
        1) WARMUP(연속 5초) 통과
        2) EXIT_MONITOR(연속 미감지 4초) → 종료 복귀
        """
        poll = 1.0
        warmup_need = 5.0
        missing_needed = 4.0
        stable_start = None
        while True:
            alive = any(
                (
                    proc.info["name"] and proc.info["name"].lower() == exe_name.lower()
                    for proc in psutil.process_iter(["name"])
                )
            )
            if alive:
                if stable_start is None:
                    stable_start = time.time()
                else:
                    elapsed = time.time() - stable_start
                    if elapsed >= warmup_need:
                        break
            else:
                stable_start = None
            time.sleep(poll)
        missing_acc = 0.0
        while True:
            alive = any(
                (
                    proc.info["name"] and proc.info["name"].lower() == exe_name.lower()
                    for proc in psutil.process_iter(["name"])
                )
            )
            if alive:
                missing_acc = 0.0
            else:
                missing_acc += poll
                if missing_acc >= missing_needed:
                    self.restore_launcher()
                    return
            time.sleep(poll)

    def open_graphic_setting(self):
        popup = GraphicSettingPopup(
            self.platform, self.app_id, self.theme_manager, self
        )
        popup.exec()

    def open_batch_setting(self):
        popup = BatchSettingPopup(self.platform, self.app_id, self.theme_manager, self)
        popup.exec()

    def on_delete_clicked(self):
        """삭제 확인 후 등록 데이터를 지우고 메인 목록을 갱신한다. 게임 설치 폴더 삭제와 혼동하지 않도록 경로를 읽는다."""
        from popup_utils import ConfirmDialog
        import shutil

        dialog = ConfirmDialog(
            "게임 삭제 확인",
            "해당 게임을 런처에서 삭제하시겠습니까?\n(실제 설치된 게임은 삭제되지 않습니다.)",
            self.theme_manager,
            self.parent(),
        )
        if dialog.exec():
            folder = os.path.join("l_libs", self.platform, str(self.app_id))
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            self.close()

            def delayed_refresh(target_window):
                target_window.central_content.load_registered_games()
                target_window.central_content.on_category_changed(0)
                target_window.central_content.render_cards()

            for w in QApplication.topLevelWidgets():
                if w.isVisible() and hasattr(w, "central_content"):
                    QTimer.singleShot(500, lambda w=w: delayed_refresh(w))
                    break

    def open_category_popup(self):
        from category_select_popup import CategorySelectPopup

        popup = CategorySelectPopup(self.game_metadata, self.theme_manager, self)
        popup.exec()

    def open_edit_popup(self):
        """현재 메타데이터를 편집 화면에 넘긴다. 저장은 편집 화면의 명시적 등록/수정 동작에서 이루어진다."""
        try:
            meta_path = os.path.join(
                "l_libs", self.platform, str(self.app_id), "meta.json"
            )
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            return
        from user_register_popup import GameRegisterEditPopup

        self.close()
        popup = GameRegisterEditPopup(
            parent=self.parent(),
            theme_manager=self.theme_manager,
            edit_mode=True,
            edit_data=meta,
            appid=self.app_id,
        )
        popup.exec()

    def closeEvent(self, event):
        """이미지·애니메이션 참조를 해제하는 Qt 종료 콜백이다. 감시 스레드가 사용하는 게임 식별 정보는 유지한다."""
        if hasattr(self, "title_scroll_anim"):
            self.title_scroll_anim.stop()
            self.title_scroll_anim = None
        for attr in [
            "bg_image",
            "header_label",
            "icon_label",
            "text_label",
            "delete_label",
            "edit_label",
            "category_label",
            "close_label",
        ]:
            widget = getattr(self, attr, None)
            if widget:
                if widget.parent():
                    layout = widget.parent().layout()
                    if layout:
                        layout.removeWidget(widget)
                widget.clear()
                widget.deleteLater()
                setattr(self, attr, None)
        for attr in ["bg_pixmap", "header_pixmap"]:
            if hasattr(self, attr):
                setattr(self, attr, None)
        if hasattr(self, "scaled_pixmap_cache"):
            self.scaled_pixmap_cache.clear()
            del self.scaled_pixmap_cache
        super().closeEvent(event)
