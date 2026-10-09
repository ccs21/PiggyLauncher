"""Classic ROM 목록의 폴더 탐색·가상 행·개별 편집·실행 화면.
전체 모델과 소수의 표시 위젯을 분리한다. 실행 후 감시는 GameRunner가 맡고 복귀는 GUI 슬롯으로 전달한다.
"""

import logging
import os
import random
import json
import time
import psutil
import threading
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QMetaObject, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextBrowser,
    QDialog,
    QLineEdit,
    QMessageBox,
    QMainWindow,
    QApplication,
)
from popup_windows import BasePopup
from scraper_setting_popup import ScraperSettingPopup
from rom_edit_popup import RomEditPopup
from core_edit_popup import RomEditPopup as CoreEditPopup
from popup_alert import CustomAlertDialog
from notification_manager import notification_manager
import emulator_launcher
import re


def parse_cue_referenced_files(cue_path):
    """CUE의 FILE 항목을 읽어 실제 데이터 파일을 찾는다. CUE와 BIN을 각각 다른 게임으로 중복 표시하지 않기 위한 전처리다."""
    referenced_files = []
    try:
        with open(cue_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = re.match(
                    'FILE\\s+"(.+?)"\\s+BINARY', line.strip(), re.IGNORECASE
                )
                if match:
                    referenced_files.append(match.group(1))
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    return referenced_files


class DraggableTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.start_pos:
            dy = event.pos().y() - self.start_pos.y()
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
            self.start_pos = event.pos()
        super().mouseMoveEvent(event)


class RomListPopup(BasePopup):
    def __init__(self, meta, theme_manager, app_id, platform, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.meta = meta or {}
        self.app_id = app_id
        self.platform = platform
        self.focus_index = 0
        self.rom_widgets = []
        self.roms = []
        self.model_entries = []
        self._v_first_index = 0
        self._v_pool_size = 0
        self._v_stride = 0
        self._v_refresh_pending = False
        self.show_filename_mode = False
        self._remembered_focus_filename = None
        self.last_clicked_index = -1
        self.resize_popup()
        try:
            with open("configs/l_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            self.group_roms_by_folder = config.get("group_roms_by_folder", True)
        except Exception:
            self.group_roms_by_folder = True
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#FFFFFF"
        )
        bg = QWidget(self)
        bg.setStyleSheet(f"background-color: {bg_color};")
        bg.setGeometry(0, 0, self.width(), self.height())
        self.top_section = QWidget(bg)
        self.bottom_section = QWidget(bg)
        layout = QVBoxLayout(bg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.top_section, 1)
        layout.addWidget(self.bottom_section, 9)
        bg.setLayout(layout)
        self.build_top_section()
        self.build_bottom_section()
        if self.parent():
            geo = self.parent().window().frameGeometry()
            center = geo.center()
            self.move(center - self.rect().center())
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.show()
        self.raise_()
        self.activateWindow()

    def build_top_section(self):
        layout = QHBoxLayout(self.top_section)
        layout.setContentsMargins(
            self.theme_manager.scale_px(40),
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(40),
            self.theme_manager.scale_px(20),
        )
        layout.setSpacing(self.theme_manager.scale_px(30))
        self.top_section.setStyleSheet("background-color: transparent; border: none;")
        icon_size = self.theme_manager.scale_px(64)
        emul_icon_path = self.theme_manager.get("platform_icons.emul", None)
        if emul_icon_path and os.path.exists(emul_icon_path):
            self.platform_icon = QLabel()
            self.platform_icon.setFixedSize(icon_size, icon_size)
            self.platform_icon.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            pixmap = QPixmap(emul_icon_path)
            if not pixmap.isNull():
                scaled_icon = pixmap.scaled(
                    icon_size - self.theme_manager.scale_px(8),
                    icon_size - self.theme_manager.scale_px(8),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.platform_icon.setPixmap(scaled_icon)
            layout.addWidget(self.platform_icon)
        self.title_label = QLabel(self.meta.get("title", "NO TITLE"))
        font_cfg = self.theme_manager.get("fonts.상세_제목", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 48)
        font_bold = font_cfg.get("bold", True)
        font_color = font_cfg.get("color", "#FFFFFF")
        self.title_label.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {('bold' if font_bold else 'normal')};\n            background-color: transparent;\n            border: none;\n            "
        )
        layout.addWidget(self.title_label)
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        icon_keys = ["reflash", "scrap", "search"]
        self.icon_buttons = []
        for key in icon_keys:
            icon_path = self.theme_manager.get(f"icons.{key}", f"icons/{key}.png")
            btn = QPushButton()
            btn.setObjectName(f"{key}_btn")
            btn.setFixedSize(
                self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
            )
            btn.setIconSize(btn.size())
            btn.setStyleSheet("border: none; background-color: transparent;")
            if os.path.exists(icon_path):
                btn.setIcon(QPixmap(icon_path))
            layout.addWidget(btn)
            self.icon_buttons.append(btn)
        self.icon_buttons[0].clicked.connect(self.refresh_rom_list)
        self.icon_buttons[1].clicked.connect(self.open_scraper_setting)
        self.icon_buttons[2].clicked.connect(self.open_search_popup)
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
        self.category_label.mousePressEvent = lambda event: self.open_category_popup()
        layout.addWidget(self.category_label)
        close_btn = QPushButton()
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        close_btn.setIconSize(close_btn.size())
        close_btn.setStyleSheet("border: none; background-color: transparent;")
        close_icon = self.theme_manager.get("icons.close", "icons/close.png")
        if os.path.exists(close_icon):
            close_btn.setIcon(QPixmap(close_icon))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def open_scraper_setting(self):
        popup = ScraperSettingPopup(self.theme_manager, self.app_id, parent=self)
        popup.exec()

    def open_category_popup(self):
        from category_select_popup import CategorySelectPopup

        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                content = f.read()
                meta = json.loads(content)
        except Exception:
            return
        try:
            popup = CategorySelectPopup(
                {
                    "appid": meta.get("appid", self.app_id),
                    "platform": meta.get("platform", self.app_id),
                    "categories": meta.get("categories", []),
                },
                self.theme_manager,
                self,
            )
            popup.exec()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def navigate_folder(self, new_dir):
        self.current_dir = new_dir
        try:
            meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
            with open(meta_path, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        except Exception:
            self.meta = {}
        self.reload()

    def _compute_cue_hidden_bins(self) -> set:
        """cue가 참조하는 bin(또는 바이너리) 파일을 리스트에서 숨기기 위한 set"""
        cue_hidden_bins = set()
        try:
            for rom in self.roms:
                filename = rom.get("filename", "")
                if filename.lower().endswith(".cue"):
                    cue_dir = os.path.dirname(filename)
                    cue_path = os.path.join(self.meta.get("rom_folder", ""), filename)
                    if os.path.exists(cue_path):
                        referenced = parse_cue_referenced_files(cue_path)
                        for ref in referenced:
                            hidden_path = os.path.normpath(os.path.join(cue_dir, ref))
                            cue_hidden_bins.add(hidden_path.lower())
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        return cue_hidden_bins

    def _collect_filtered_roms_and_subfolders(self):
        """현재 current_dir + 옵션(group_roms_by_folder) 기준으로 표시 대상 목록을 계산"""
        if not hasattr(self, "current_dir"):
            self.current_dir = ""
        cue_hidden_bins = self._compute_cue_hidden_bins()
        subfolders = set()
        filtered_roms = []
        for rom in self.roms:
            rom_path = rom.get("filename", "")
            rom_dir = os.path.dirname(rom_path)
            rom_path_normalized = os.path.normpath(rom_path).lower()
            if rom_path_normalized in cue_hidden_bins:
                continue
            if self.group_roms_by_folder:
                if rom_dir == self.current_dir:
                    filtered_roms.append(rom)
                else:
                    if rom_dir and self.current_dir:
                        try:
                            rel = os.path.relpath(rom_dir, self.current_dir)
                        except ValueError:
                            rel = rom_dir
                    else:
                        rel = rom_dir
                    if rel and "/" not in rel and ("\\" not in rel):
                        subfolders.add(rel)
            else:
                filtered_roms.append(rom)
        return (filtered_roms, subfolders)

    def _make_display_name(self, rom: dict) -> str:
        """표시 모드(show_filename_mode / 폴더표시옵션 / 즐겨찾기) 반영한 문자열"""
        if self.show_filename_mode:
            title = os.path.basename(rom.get("filename", "UNKNOWN"))
        else:
            title = rom.get("title") or os.path.basename(rom.get("filename", "UNKNOWN"))
        display_name = title
        if not self.group_roms_by_folder:
            folder_name = os.path.dirname(rom.get("filename", "")).split("\\")[-1]
            if folder_name:
                display_name += f" [{folder_name}]"
        if rom.get("favorites", "False") == "True":
            display_name = f"★ {display_name}"
        return display_name

    def _rebuild_model_entries(self):
        """현재 상태 기준으로 엔트리 모델 재구성"""
        self.model_entries = []
        (filtered_roms, subfolders) = self._collect_filtered_roms_and_subfolders()
        if getattr(self, "current_dir", ""):
            self.model_entries.append(
                {
                    "type": "up",
                    "label": "⬆️ [상위 폴더로]",
                    "folder_path": "",
                    "rom": None,
                }
            )
        for folder in sorted(subfolders):
            self.model_entries.append(
                {
                    "type": "folder",
                    "label": f"📂 {folder}",
                    "folder_path": os.path.join(self.current_dir, folder)
                    if self.current_dir
                    else folder,
                    "rom": None,
                }
            )
        for rom in filtered_roms:
            self.model_entries.append(
                {
                    "type": "rom",
                    "label": self._make_display_name(rom),
                    "folder_path": "",
                    "rom": rom,
                }
            )
        if self.model_entries:
            self.focus_index = max(
                0, min(self.focus_index, len(self.model_entries) - 1)
            )
        else:
            self.focus_index = 0

    def _calc_virtual_stride(self) -> int:
        item_h = self.theme_manager.scale_px(48)
        spacing = self.theme_manager.scale_px(10)
        return item_h + spacing

    def _init_virtual_list_ui(self):
        """좌측 리스트를 스페이서+풀 구조로 구성"""
        self.rom_widgets.clear()
        self._v_stride = self._calc_virtual_stride()
        viewport_h = max(1, self.scroll_area.viewport().height())
        visible_count = max(1, int(viewport_h / max(1, self._v_stride)))
        self._v_pool_size = max(visible_count + 20, 80)
        self._v_scroll_widget = QWidget()
        self._v_layout = QVBoxLayout(self._v_scroll_widget)
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(0)
        self._v_layout.setAlignment(Qt.AlignTop)
        self._v_top_spacer = QWidget()
        self._v_top_spacer.setFixedHeight(0)
        self._v_top_spacer.setStyleSheet("background-color: transparent; border: none;")
        self._v_bottom_spacer = QWidget()
        self._v_bottom_spacer.setFixedHeight(0)
        self._v_bottom_spacer.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self._v_layout.addWidget(self._v_top_spacer)
        self._v_rows = []
        for _ in range(self._v_pool_size):
            row = QWidget()
            row.setFixedHeight(max(1, self._v_stride))
            row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row.setStyleSheet("background-color: transparent; border: none;")
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)
            row_layout.setAlignment(Qt.AlignTop)
            item = RomItemWidget("", self.theme_manager, 0, self)
            item.setFixedHeight(self.theme_manager.scale_px(48))
            spacer = QWidget()
            spacer.setFixedHeight(self.theme_manager.scale_px(10))
            spacer.setStyleSheet("background-color: transparent; border: none;")
            row_layout.addWidget(item)
            row_layout.addWidget(spacer)
            self._v_rows.append((row, item))
            self.rom_widgets.append(item)
            self._v_layout.addWidget(row)
        self._v_layout.addWidget(self._v_bottom_spacer)
        self.scroll_area.setWidget(self._v_scroll_widget)
        sb = self.scroll_area.verticalScrollBar()
        try:
            sb.valueChanged.disconnect()
        except Exception:
            pass
        sb.valueChanged.connect(self._schedule_virtual_refresh)
        self._refresh_virtual_view(force=True)

    def _schedule_virtual_refresh(self):
        """같은 이벤트 처리 중 연속으로 들어온 갱신을 한 번의 예약 작업으로 합친다."""
        if self._v_refresh_pending:
            return
        self._v_refresh_pending = True
        QTimer.singleShot(0, self._refresh_virtual_view)

    def _refresh_virtual_view(self, force: bool = False):
        """현재 스크롤 위치에 필요한 행만 재사용해 표시한다.
        전체 목록은 model_entries에 두고 작은 위젯 풀에 해당 구간을 바인딩한다.
        위·아래 여백으로 전체 길이를 표현하므로 수천 개 위젯을 동시에 만들 필요가 없다.
        """
        self._v_refresh_pending = False
        total = len(self.model_entries)
        stride = max(1, self._v_stride)
        try:
            self._v_scroll_widget.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Minimum
            )
            self._v_scroll_widget.setMinimumHeight(max(0, total * stride))
        except Exception:
            pass
        sb = self.scroll_area.verticalScrollBar()
        first = int(sb.value() / stride) if stride else 0
        first = max(0, min(first, max(0, total - 1))) if total else 0
        if not force and first == getattr(self, "_v_first_index", 0):
            self._apply_pool_selection_only()
            return
        self._v_first_index = first
        self._v_top_spacer.setFixedHeight(first * stride)
        visible_pool = min(self._v_pool_size, max(0, total - first))
        self._v_bottom_spacer.setFixedHeight(
            max(0, (total - (first + visible_pool)) * stride)
        )
        for i, (row, item) in enumerate(self._v_rows):
            entry_index = first + i
            if entry_index < total:
                row.show()
                e = self.model_entries[entry_index]
                item.bind_entry(
                    entry_index=entry_index,
                    text=e.get("label", ""),
                    rom=e.get("rom"),
                    is_folder=e.get("type") == "folder",
                    folder_path=e.get("folder_path", ""),
                    is_up_folder=e.get("type") == "up",
                )
            else:
                row.hide()
                item.bind_entry(entry_index, "", None, False, None, False)
                item.set_selected(False)
        self._apply_pool_selection_only()

    def _apply_pool_selection_only(self):
        focus = getattr(self, "focus_index", 0)
        for row, item in getattr(self, "_v_rows", []):
            item.set_selected(item.index == focus)

    def _ensure_index_visible(self, idx: int):
        """모델 인덱스와 행 높이로 스크롤 위치를 계산한다. 위젯 풀의 행 번호와 전체 모델 인덱스를 혼동하지 않는다."""
        total = len(self.model_entries)
        if total <= 0:
            return
        idx = max(0, min(idx, total - 1))
        stride = max(1, self._v_stride)
        sb = self.scroll_area.verticalScrollBar()
        viewport_h = max(1, self.scroll_area.viewport().height())
        visible_count = max(1, int(viewport_h / stride))
        first = int(sb.value() / stride)
        last = first + visible_count - 1
        if idx < first:
            sb.setValue(idx * stride)
        elif idx > last:
            sb.setValue(max(0, (idx - visible_count + 1) * stride))

    def _get_entry(self, idx: int):
        if 0 <= idx < len(self.model_entries):
            return self.model_entries[idx]
        return None

    def _find_entry_index_by_filename(self, filename: str):
        if not filename:
            return None
        for i, e in enumerate(self.model_entries):
            if e.get("type") == "rom":
                rom = e.get("rom") or {}
                if rom.get("filename") == filename:
                    return i
        return None

    def _get_focused_rom_filename(self):
        e = self._get_entry(self.focus_index)
        if not e or e.get("type") != "rom":
            return None
        return (e.get("rom") or {}).get("filename")

    def build_bottom_section(self):
        import json
        from PySide6.QtWidgets import (
            QHBoxLayout,
            QVBoxLayout,
            QScrollArea,
            QWidget,
            QLabel,
        )
        from PySide6.QtCore import Qt, QTimer

        self.title_image_path = None
        self.screenshot_path = None
        self.bottom_section.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.left_panel = QWidget(self.bottom_section)
        self.right_panel = QWidget(self.bottom_section)
        self.left_panel.setStyleSheet("background-color: transparent; border: none;")
        self.right_panel.setStyleSheet("background-color: transparent; border: none;")
        bottom_layout = QHBoxLayout(self.bottom_section)
        bottom_layout.setContentsMargins(
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(10),
        )
        bottom_layout.setSpacing(0)
        bottom_layout.addWidget(self.left_panel, 6)
        bottom_layout.addWidget(self.right_panel, 4)
        self.bottom_section.setLayout(bottom_layout)
        self.scroll_area = QScrollArea(self.left_panel)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.scroll_area)
        self.left_panel.setLayout(left_layout)
        rom_list_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        self.roms = []
        if os.path.exists(rom_list_path):
            try:
                with open(rom_list_path, "r", encoding="utf-8") as f:
                    self.roms = json.load(f) or []
            except Exception:
                self.roms = []
        fix_needed = False
        for rom in self.roms:
            core_val = rom.get("core", "")
            core_type_val = rom.get("core_type", "")
            if core_val.startswith("SA:"):
                rom["core"] = core_val[3:]
                if not core_type_val:
                    rom["core_type"] = "SA"
                fix_needed = True
            elif core_val.startswith("RA:"):
                rom["core"] = core_val[3:]
                if not core_type_val:
                    rom["core_type"] = "RA"
                fix_needed = True
        if fix_needed:
            try:
                with open(rom_list_path, "w", encoding="utf-8") as f:
                    json.dump(self.roms, f, indent=4, ensure_ascii=False)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.sort_roms()
        if not hasattr(self, "current_dir"):
            self.current_dir = ""
        self._rebuild_model_entries()
        self._init_virtual_list_ui()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(self.theme_manager.scale_px(10))
        self.right_section_1 = QWidget()
        self.right_section_2 = QWidget()
        self.right_section_3 = QWidget()
        self.right_section_4 = QWidget()
        self.right_section_1.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.right_section_2.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.right_section_3.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.right_section_4.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        right_layout.addWidget(self.right_section_1, 18)
        right_layout.addWidget(self.right_section_2, 43)
        right_layout.addWidget(self.right_section_3, 15)
        right_layout.addWidget(self.right_section_4, 24)
        self.right_panel.setLayout(right_layout)
        self.title_image_label = QLabel(self.right_section_1)
        self.title_image_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.title_image_label.setScaledContents(False)
        self.title_image_label.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        title_layout = QVBoxLayout(self.right_section_1)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_image_label)
        self.right_section_1.setLayout(title_layout)
        self.screenshot_label = QLabel(self.right_section_2)
        self.screenshot_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.screenshot_label.setScaledContents(False)
        self.screenshot_label.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        screenshot_layout = QVBoxLayout(self.right_section_2)
        screenshot_layout.setContentsMargins(0, 0, 0, 0)
        screenshot_layout.setSpacing(0)
        screenshot_layout.addWidget(self.screenshot_label)
        self.right_section_2.setLayout(screenshot_layout)
        self.meta_label_container = QWidget(self.right_section_3)
        self.meta_label_layout = QVBoxLayout(self.meta_label_container)
        self.meta_label_layout.setContentsMargins(
            self.theme_manager.scale_px(50),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(10),
        )
        self.meta_label_layout.setSpacing(self.theme_manager.scale_px(8))
        meta_wrap_layout = QVBoxLayout(self.right_section_3)
        meta_wrap_layout.setContentsMargins(0, 0, 0, 0)
        meta_wrap_layout.setSpacing(0)
        meta_wrap_layout.addWidget(self.meta_label_container)
        self.right_section_3.setLayout(meta_wrap_layout)
        desc_browser = DraggableTextBrowser(self.right_section_4)
        desc_browser.setReadOnly(True)
        desc_browser.setOpenExternalLinks(False)
        desc_browser.setTextInteractionFlags(Qt.NoTextInteraction)
        desc_browser.setStyleSheet("background-color: transparent; border: none;")
        desc_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_section_4_layout = QVBoxLayout(self.right_section_4)
        right_section_4_layout.setContentsMargins(
            self.theme_manager.scale_px(50),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(50),
            self.theme_manager.scale_px(10),
        )
        right_section_4_layout.setSpacing(0)
        right_section_4_layout.addWidget(desc_browser)
        self.right_section_4.setLayout(right_section_4_layout)
        self.desc_browser = desc_browser
        QTimer.singleShot(0, self.apply_last_played_focus)

    def apply_last_played_focus(self):
        """최근 실행 ROM을 찾아 초점을 복원한다. 정렬·폴더 이동으로 인덱스가 바뀔 수 있으므로 파일 식별자를 함께 사용한다."""
        from datetime import datetime

        rom_list_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        if not os.path.exists(rom_list_path):
            return
        try:
            with open(rom_list_path, "r", encoding="utf-8") as f:
                roms = json.load(f)
        except Exception:
            return
        latest_time = None
        latest_rom = None
        for rom in roms:
            ts = rom.get("last_played", "")
            if ts and ts != "없음":
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    if not latest_time or dt > latest_time:
                        latest_time = dt
                        latest_rom = rom
                except Exception:
                    continue
        if not latest_rom:
            if not self.roms:
                return
            if self.group_roms_by_folder and (not self.current_dir):
                self.current_dir = os.path.dirname(self.roms[0].get("filename", ""))
            self.reload()
            QTimer.singleShot(0, lambda: self.set_focus_index(0))
            return
        filename = latest_rom.get("filename", "")
        folder = os.path.dirname(filename)
        latest_rom.get("title") or os.path.basename(filename)
        if self.group_roms_by_folder:
            if self.current_dir != folder:
                self.current_dir = folder
                self.reload()
                QTimer.singleShot(0, self.apply_last_played_focus)
                return
        entry_idx = self._find_entry_index_by_filename(filename)
        if entry_idx is None:
            return
        self.set_focus_index(entry_idx)
        return

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.title_image_path and os.path.exists(self.title_image_path):
            QTimer.singleShot(0, self.update_title_image_size)
        else:
            self.title_image_label.clear()
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            QTimer.singleShot(0, self.update_screenshot_image)
        else:
            self.screenshot_label.clear()

    def update_title_image_size(self):
        if self.title_image_path and os.path.exists(self.title_image_path):
            pixmap = QPixmap(self.title_image_path)
            if not pixmap.isNull():
                target_height = self.right_section_1.height()
                if target_height > 0:
                    target_height = self.right_section_1.height()
                    target_width = self.right_section_1.width()
                    if target_height > 0 and target_width > 0:
                        scaled = pixmap.scaled(
                            target_width,
                            target_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                        self.title_image_label.setPixmap(scaled)

    def update_screenshot_image(self):
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            pixmap = QPixmap(self.screenshot_path)
            if not pixmap.isNull():
                target_height = self.right_section_2.height()
                if target_height > 0:
                    scaled = pixmap.scaledToHeight(
                        target_height, Qt.SmoothTransformation
                    )
                    self.screenshot_label.setPixmap(scaled)

    def set_focus_index(self, idx: int):
        """목록 범위에 맞춰 선택을 바꾸고 우측 정보·스크롤·행 강조를 함께 갱신한다."""
        total = len(getattr(self, "model_entries", []))
        if total <= 0:
            return
        idx = max(0, min(idx, total - 1))
        self.focus_index = idx
        if not hasattr(self, "_v_scroll_widget"):
            entry = self._get_entry(self.focus_index) or {}
            if entry.get("type") == "rom":
                filename = (entry.get("rom") or {}).get("filename", "")
                rom = next((r for r in self.roms if r.get("filename") == filename), {})
                self.update_right_section(rom)
            else:
                self.update_right_section({})
            return
        self._ensure_index_visible(self.focus_index)
        self._refresh_virtual_view(force=True)
        entry = self._get_entry(self.focus_index)
        if not entry:
            return
        if entry.get("type") in ("folder", "up"):
            self.update_right_section({})
        else:
            filename = (entry.get("rom") or {}).get("filename", "")
            rom = next((r for r in self.roms if r.get("filename") == filename), {})
            self.update_right_section(rom)

    def keyPressEvent(self, event):
        key = event.key()
        total = len(getattr(self, "model_entries", []))
        if key == Qt.Key_W:
            self.set_focus_index(max(0, self.focus_index - 1))
        elif key == Qt.Key_S:
            self.set_focus_index(min(max(0, total - 1), self.focus_index + 1))
        elif key == Qt.Key_A:
            self.set_focus_index(max(0, self.focus_index - 14))
        elif key == Qt.Key_D:
            self.set_focus_index(min(max(0, total - 1), self.focus_index + 14))
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            entry = self._get_entry(self.focus_index)
            if not entry:
                return
            etype = entry.get("type")
            if etype == "up":
                self.navigate_folder(os.path.dirname(getattr(self, "current_dir", "")))
            elif etype == "folder":
                self.navigate_folder(entry.get("folder_path", ""))
            elif etype == "rom":
                self.launch_current_rom()
            else:
                return
        elif key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_X:
            self.edit_rom_metadata()
        elif key == Qt.Key_C:
            self.toggle_favorite()
        elif key == Qt.Key_E:
            self.show_filename_mode = not self.show_filename_mode
            self.reopen_self(keep_state=True)
            return
        elif key == Qt.Key_Q:
            entry = self._get_entry(self.focus_index)
            if not entry:
                return
            if entry.get("type") != "rom":
                return
            target_filename = (entry.get("rom") or {}).get("filename")
            if not target_filename:
                return
            current_rom = next(
                (r for r in self.roms if r.get("filename") == target_filename), None
            )
            if current_rom is None:
                return
            popup = CoreEditPopup(
                self.theme_manager, self.app_id, current_rom, parent=self
            )
            popup.show()
        else:
            super().keyPressEvent(event)

    def update_right_section(self, rom):
        """선택 ROM의 텍스트와 이미지를 표시한다. 메타데이터가 없는 경우 빈 상태를 표시하는 것도 UI 갱신의 일부다."""
        self.title_image_path = ""
        title_img_rel = rom.get("title_image", "")
        title_img_path = os.path.join("l_libs", "emul", self.app_id, title_img_rel)
        if title_img_rel and os.path.exists(title_img_path):
            self.title_image_path = title_img_path
            self.update_title_image_size()
        else:
            self.title_image_label.clear()
        self.screenshot_path = ""
        screenshots = rom.get("screenshots", [])
        if screenshots:
            filename = random.choice(screenshots)
            shot_path = os.path.join("l_libs", "emul", self.app_id, filename)
            if os.path.exists(shot_path):
                self.screenshot_path = shot_path
                self.update_screenshot_image()
            else:
                self.screenshot_label.clear()
        else:
            self.screenshot_label.clear()
        for i in reversed(range(self.meta_label_layout.count())):
            item = self.meta_label_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        publisher = rom.get("publisher", "")
        release_date = rom.get("release_date", "")
        last_played = rom.get("last_played", "")
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = "bold" if font_cfg.get("bold", False) else "normal"
        font_color = font_cfg.get("color", "#000000")

        def make_label(text):
            label = QLabel(text)
            label.setStyleSheet(
                f"\n                color: {font_color};\n                font-family: '{font_family}';\n                font-size: {font_size}px;\n                font-weight: {font_bold};\n                background-color: transparent;\n                border: none;\n                "
            )
            return label

        if publisher:
            self.meta_label_layout.addWidget(make_label(f"제작/배급: {publisher}"))
        if release_date:
            self.meta_label_layout.addWidget(make_label(f"출시일: {release_date}"))
        if last_played:
            self.meta_label_layout.addWidget(make_label(f"최근 실행: {last_played}"))
        description = rom.get("description", "") or ""
        if not hasattr(self, "desc_browser") or self.desc_browser is None:
            self.desc_browser = DraggableTextBrowser(self.right_section_4)
            self.desc_browser.setReadOnly(True)
            self.desc_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.desc_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.desc_browser.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.right_section_4.layout().addWidget(self.desc_browser)
        else:
            if self.desc_browser.parent() is None:
                self.desc_browser.setParent(self.right_section_4)
            if self.right_section_4.layout().indexOf(self.desc_browser) == -1:
                self.right_section_4.layout().addWidget(self.desc_browser)
        self.desc_browser.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_bold};\n            background-color: transparent;\n            border: none;\n            "
        )
        self.desc_browser.setPlainText(description)

    def sort_roms(self):

        def sort_key(rom):
            title = rom.get("title") or rom.get("filename", "")
            title = title.strip()
            is_fav = rom.get("favorites", "False") == "True"
            is_korean = title and "가" <= title[0] <= "힣"
            return (not is_fav, not is_korean, title.lower())

        self.roms.sort(key=sort_key)

    def refresh_rom_list(self):
        """사용자 확인 후 실제 폴더와 Classic JSON 목록을 비교한다.
        기존 목록을 백업하고 살아 있는 항목의 정보를 유지하면서 새 항목을 추가한다.
        PS3/Vita 같은 디렉터리형 게임은 일반 파일형 ROM과 식별 방식이 다르다.
        이 코드는 Classic 교재용 JSON 규칙이다. 2.0의 XML 규칙으로 읽으면 안 된다.
        """
        from shutil import copyfile
        from popup_utils import ConfirmDialog
        from PySide6.QtWidgets import QDialog
        from ra_map_full import ROM_EXTENSIONS_MAP

        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        rom_list_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        backup_path = os.path.join("l_libs", "emul", self.app_id, "bkup_rom_list.json")

        def insert_breakable_path(path: str) -> str:
            return path.replace("/", "/\u200b").replace("\\", "\\\u200b")

        visible_path = insert_breakable_path(backup_path)
        msg = f"롬 리스트를 새로 만듭니다.\n기존 리스트는 다음 경로에 자동 백업 됩니다.\n\n{visible_path}"
        dlg = ConfirmDialog("롬 리스트 새로고침", msg, self.theme_manager, self)
        if dlg.exec() != QDialog.Accepted:
            return
        if os.path.exists(rom_list_path):
            try:
                copyfile(rom_list_path, backup_path)
            except Exception:
                return
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            rom_folder = meta.get("rom_folder", "")
            if not os.path.exists(rom_folder):
                return
            actual_items = []
            for root, _, files in os.walk(rom_folder):
                for fname in files:
                    actual_items.append(
                        os.path.relpath(os.path.join(root, fname), rom_folder)
                    )
            is_vita = self.app_id == "playstation_vita"
            existing = []
            existing_filenames = set()
            for rom in self.roms:
                fname = rom.get("filename")
                rom_dir = rom.get("rom_dir")
                if self.app_id == "playstation3":
                    if rom_dir and os.path.exists(rom_dir):
                        existing.append(rom)
                        existing_filenames.add(fname)
                elif fname in actual_items:
                    existing.append(rom)
                    existing_filenames.add(fname)
            new_roms = []
            if is_vita:
                import requests
                import shutil

                title_map = {}
                try:
                    response = requests.get(
                        "https://nopaystation.com/tsv/PSV_GAMES.tsv", timeout=10
                    )
                    response.encoding = "utf-8"
                    for line in response.text.splitlines():
                        parts = line.strip().split("\t")
                        if len(parts) >= 3:
                            title_map[parts[0]] = parts[2]
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
                rom_folder_path = os.path.abspath(rom_folder)
                title_dir = os.path.join("l_libs", "emul", self.app_id, "title")
                screenshot_dir = os.path.join("l_libs", "emul", self.app_id, "s_shot")
                os.makedirs(title_dir, exist_ok=True)
                os.makedirs(screenshot_dir, exist_ok=True)
                for folder_name in actual_items:
                    if folder_name in existing_filenames:
                        continue
                    full_path = os.path.join(rom_folder_path, folder_name)
                    if not os.path.isdir(full_path):
                        continue
                    title_id = folder_name
                    game_title = title_map.get(title_id, "")
                    title_image_path = os.path.join(full_path, "sce_sys", "icon0.png")
                    screenshot_path = os.path.join(full_path, "sce_sys", "pic0.png")
                    title_target = os.path.join(title_dir, f"{title_id}_title.png")
                    screenshot_target = os.path.join(
                        screenshot_dir, f"{title_id}_screenshot.png"
                    )
                    try:
                        if os.path.exists(title_image_path):
                            shutil.copyfile(title_image_path, title_target)
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
                    try:
                        if os.path.exists(screenshot_path):
                            shutil.copyfile(screenshot_path, screenshot_target)
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
                    rom_data = {
                        "title": game_title,
                        "filename": title_id,
                        "core": "",
                        "core_type": "",
                        "title_image": f"title/{title_id}_title.png"
                        if os.path.exists(title_target)
                        else "",
                        "screenshots": [f"s_shot/{title_id}_screenshot.png"]
                        if os.path.exists(screenshot_target)
                        else [],
                        "publisher": "",
                        "release_date": "",
                        "description": "",
                        "last_played": "없음",
                        "favorites": "False",
                        "emulator_path": "",
                    }
                    new_roms.append(rom_data)
            elif self.app_id == "playstation3":
                import shutil

                rom_folder_path = os.path.abspath(rom_folder)
                config_path = os.path.join("configs", "emul_config.json")
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        emul_path = config.get("executables", {}).get("RPCS3", "")
                except Exception:
                    emul_path = ""
                game_dir = os.path.join(os.path.dirname(emul_path), "dev_hdd0", "game")
                title_dir = os.path.join("l_libs", "emul", self.app_id, "title")
                screenshot_dir = os.path.join("l_libs", "emul", self.app_id, "s_shot")
                os.makedirs(title_dir, exist_ok=True)
                os.makedirs(screenshot_dir, exist_ok=True)
                all_existing_ids = {
                    rom.get("filename") for rom in self.roms if rom.get("filename")
                }
                for folder_name in os.listdir(rom_folder_path):
                    full_path = os.path.join(rom_folder_path, folder_name)
                    if not os.path.isdir(full_path):
                        continue
                    usrdir = os.path.join(full_path, "PS3_GAME", "USRDIR")
                    if not os.path.exists(os.path.join(usrdir, "EBOOT.BIN")):
                        continue
                    title_id = folder_name
                    if title_id in all_existing_ids:
                        continue
                    rom_data = {
                        "title": title_id,
                        "filename": title_id,
                        "core": "",
                        "core_type": "",
                        "title_image": "",
                        "screenshots": [],
                        "publisher": "",
                        "release_date": "",
                        "description": "",
                        "last_played": "없음",
                        "favorites": "False",
                        "emulator_path": "",
                        "rom_dir": full_path,
                    }
                    old_rom = next(
                        (r for r in self.roms if r.get("filename") == title_id), None
                    )
                    if old_rom:
                        for key in old_rom:
                            if key not in rom_data or not rom_data[key]:
                                rom_data[key] = old_rom[key]
                    new_roms.append(rom_data)
                    all_existing_ids.add(title_id)
                if os.path.exists(game_dir):
                    for folder_name in os.listdir(game_dir):
                        full_path = os.path.join(game_dir, folder_name)
                        if not os.path.isdir(full_path):
                            continue
                        usrdir = os.path.join(full_path, "USRDIR")
                        if not os.path.exists(os.path.join(usrdir, "EBOOT.BIN")):
                            continue
                        title_id = folder_name
                        if title_id in all_existing_ids:
                            continue
                        rom_data = {
                            "title": title_id,
                            "filename": title_id,
                            "core": "",
                            "core_type": "",
                            "title_image": "",
                            "screenshots": [],
                            "publisher": "",
                            "release_date": "",
                            "description": "",
                            "last_played": "없음",
                            "favorites": "False",
                            "emulator_path": "",
                            "rom_dir": full_path,
                        }
                        old_rom = next(
                            (r for r in self.roms if r.get("filename") == title_id),
                            None,
                        )
                        if old_rom:
                            for key in old_rom:
                                if key not in rom_data or not rom_data[key]:
                                    rom_data[key] = old_rom[key]
                        new_roms.append(rom_data)
                        all_existing_ids.add(title_id)
            else:
                valid_exts = ROM_EXTENSIONS_MAP.get(self.app_id, [])
                custom_exts = meta.get("ext_name", [])
                if isinstance(custom_exts, list):
                    filtered_custom_exts = [
                        ext.lower()
                        for ext in custom_exts
                        if isinstance(ext, str) and ext.startswith(".")
                    ]
                    if filtered_custom_exts:
                        valid_exts = list(set(valid_exts + filtered_custom_exts))
                for fname in actual_items:
                    full_path = os.path.join(rom_folder, fname)
                    if not os.path.isfile(full_path):
                        continue
                    if valid_exts and (
                        not any((fname.lower().endswith(ext) for ext in valid_exts))
                    ):
                        continue
                    if fname in existing_filenames:
                        continue
                    new_roms.append(
                        {
                            "title": "",
                            "filename": fname,
                            "core": "",
                            "core_type": "",
                            "title_image": "",
                            "screenshots": [],
                            "publisher": "",
                            "release_date": "",
                            "description": "",
                            "last_played": "없음",
                            "favorites": "False",
                            "emulator_path": "",
                        }
                    )
            updated_roms = existing + new_roms
            with open(rom_list_path, "w", encoding="utf-8") as f:
                json.dump(updated_roms, f, indent=4, ensure_ascii=False)
            self.roms = updated_roms
            self.sort_roms()
            self._rebuild_model_entries()
            self._refresh_virtual_view(force=True)
            self.set_focus_index(0)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def open_search_popup(self):
        dlg = QDialog(self)
        dlg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dlg.setModal(True)
        dlg.setFixedSize(
            self.theme_manager.scale_px(600), self.theme_manager.scale_px(120)
        )
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#f0f0f0"
        )
        dlg.setStyleSheet(f"background-color: {bg_color}; border: 2px solid #999;")
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_color = font_cfg.get("color", "#000000")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
        )
        layout.setSpacing(self.theme_manager.scale_px(10))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("검색어를 입력하세요 (제목 또는 파일명)")
        line_edit.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_cfg.get('family', '맑은 고딕')}';\n            font-size: {font_cfg.get('size', 22)}px;\n            font-weight: {('bold' if font_cfg.get('bold', False) else 'normal')};\n            border: 1px solid {font_color};\n            border-radius: 4px;\n            padding: {self.theme_manager.scale_px(6)}px;\n            background-color: transparent;\n            "
        )
        line_edit.returnPressed.connect(dlg.accept)
        layout.addWidget(line_edit)
        btn = QPushButton(" 확인 ")
        btn.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_cfg.get('family', '맑은 고딕')}';\n            font-size: {font_cfg.get('size', 22)}px;\n            font-weight: {('bold' if font_cfg.get('bold', False) else 'normal')};\n            border: 1px solid {font_color};\n            border-radius: 4px;\n            padding: {self.theme_manager.scale_px(6)}px {self.theme_manager.scale_px(12)}px;\n            background-color: transparent;\n            "
        )
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignRight)
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font = QFont()
        font.setFamily(font_cfg.get("family", "맑은 고딕"))
        font.setPixelSize(font_cfg.get("size", 22))
        font.setBold(font_cfg.get("bold", False))
        line_edit.setFont(font)
        btn.setFont(font)

        def on_accepted():
            keyword = line_edit.text().strip().replace(" ", "").lower()
            if not keyword:
                return
            match = None
            for rom in self.roms:
                t = rom.get("title", "").replace(" ", "").lower()
                f = rom.get("filename", "").replace(" ", "").lower()
                if keyword in t or keyword in f:
                    match = rom
                    break
            if match:
                filename = match.get("filename", "")
                folder = os.path.dirname(filename)
                if (
                    self.group_roms_by_folder
                    and getattr(self, "current_dir", "") != folder
                ):
                    self.current_dir = folder
                    self.reload()
                entry_idx = self._find_entry_index_by_filename(filename)
                if entry_idx is None:
                    entry_idx = 0
                self.set_focus_index(entry_idx)
            else:
                QMessageBox.warning(
                    self, "검색 결과 없음", "일치하는 롬을 찾을 수 없습니다."
                )

        dlg.accepted.connect(on_accepted)
        dlg.exec()

    def launch_current_rom(self):
        """ROM별 설정 → 기종 대표 설정 → 실행기 설정 순으로 빈 값을 보완한다.
        실행기와 ROM 경로를 확인한 뒤 emulator_launcher에 실행을 맡긴다. 반환된
        프로세스만으로 모든 기종 종료를 판정할 수 없어 GameRunner가 별도로 감시한다.
        """
        import json
        import os

        entry = self._get_entry(self.focus_index)
        if not entry:
            return
        if entry.get("type") != "rom":
            return
        target_filename = (entry.get("rom") or {}).get("filename")
        if not target_filename:
            return
        current_rom = next(
            (r for r in self.roms if r.get("filename") == target_filename), None
        )
        if current_rom is None:
            return
        filename = current_rom.get("filename")
        core = current_rom.get("core")
        core_type = current_rom.get("core_type")
        emulator_path = current_rom.get("emulator_path")
        rom_folder = ""
        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        config_path = os.path.join("configs", "emul_config.json")
        if not rom_folder:
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    rom_folder = meta.get("rom_folder", "")
                    if not core:
                        core = meta.get("main_core", "")
                    if not core_type:
                        core_type = meta.get("main_core_type", "")
            except Exception:
                return
        if not core or not core_type or (not emulator_path) or (not filename):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    core = core or meta.get("main_core", "")
                    core_type = core_type or meta.get("main_core_type", "")
                    rom_folder = meta.get("rom_folder", "")
            except Exception:
                return
        if not emulator_path:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    executables = config.get("executables", {})
                    if core_type == "RA":
                        emulator_path = executables.get("RetroArch", "")
                    elif core_type == "SA":
                        emulator_path = executables.get(core, "")
            except Exception:
                return
        if not core or not core_type or (not emulator_path) or (not rom_folder):
            return
        if current_rom.get("rom_dir"):
            rom_path = current_rom["rom_dir"]
        else:
            rom_path = os.path.join(rom_folder, filename)
        if not emulator_path or not os.path.exists(emulator_path):
            alert = CustomAlertDialog(
                "경로 오류",
                "에뮬레이터 실행기의 경로가 정확하지 않습니다.\n에뮬레이터 설정 또는 롬 설정을 확인 해 주세요.",
                self.theme_manager,
                self,
            )
            alert.exec()
            return
        if not rom_path or not os.path.exists(rom_path):
            alert = CustomAlertDialog(
                "경로 오류",
                "롬 파일의 경로가 정확하지 않습니다.\n롬 설정 또는 롬 리스트와 롬 파일 폴더를 확인 해 주세요.",
                self.theme_manager,
                self,
            )
            alert.exec()
            return
        notification_manager.pause()
        self.accept()
        main_launcher = None
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMainWindow) and hasattr(w, "central_content"):
                main_launcher = w
                break
        if main_launcher:
            if main_launcher.isFullScreen():
                main_launcher.showNormal()
            main_launcher.showMinimized()
            main_launcher.is_game_running = True
        bat_path = current_rom.get("bat_path", "")
        bat_process = emulator_launcher.launch_game(
            core_type, core, emulator_path, rom_path, bat_path
        )
        current_rom["exe"] = os.path.basename(emulator_path)
        runner = GameRunner(
            app_id=self.app_id,
            rom_data=current_rom,
            parent_window=self.parent().window(),
        )
        runner.update_last_played()
        processes = []
        if bat_process:
            processes.append(bat_process)
        if core_type == "SA" and core.lower() in ("pcsx2", "rpcs3"):
            threading.Thread(target=runner.wait_emulator, daemon=True).start()
            threading.Thread(
                target=runner.wait_batch, args=(bat_process,), daemon=True
            ).start()
        else:
            threading.Thread(
                target=runner.wait_all, args=(processes,), daemon=True
            ).start()

    def edit_rom_metadata(self):
        entry = self._get_entry(self.focus_index)
        if not entry:
            return
        if entry.get("type") != "rom":
            return
        target_filename = (entry.get("rom") or {}).get("filename")
        if not target_filename:
            return
        current_rom = next(
            (r for r in self.roms if r.get("filename") == target_filename), None
        )
        if current_rom is None:
            return
        popup = RomEditPopup(self.theme_manager, self.app_id, current_rom, parent=self)
        popup.show()

    def toggle_favorite(self):
        entry = self._get_entry(self.focus_index)
        if not entry:
            return
        if entry.get("type") != "rom":
            return
        target_filename = (entry.get("rom") or {}).get("filename")
        if not target_filename:
            return
        current_rom = next(
            (r for r in self.roms if r.get("filename") == target_filename), None
        )
        if current_rom is None:
            return
        current_flag = current_rom.get("favorites", "False")
        new_flag = "False" if current_flag == "True" else "True"
        current_rom["favorites"] = new_flag
        rom_list_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        try:
            with open(rom_list_path, "w", encoding="utf-8") as f:
                json.dump(self.roms, f, indent=4, ensure_ascii=False)
        except Exception:
            return
        self.sort_roms()
        self._rebuild_model_entries()
        self._refresh_virtual_view(force=True)
        new_idx = self._find_entry_index_by_filename(target_filename) or 0
        self.set_focus_index(new_idx)

    def reopen_self(self, keep_state: bool = True):
        """
        RomListPopup을 닫았다가 동일 인자로 다시 엽니다.
        keep_state=True 이면 current_dir / 포커스 filename을 최대한 복원합니다.
        """
        from PySide6.QtCore import QTimer

        backup_current_dir = getattr(self, "current_dir", "")
        backup_focus_filename = None
        if keep_state:
            backup_focus_filename = self._get_focused_rom_filename()
        meta = self.meta
        theme_manager = self.theme_manager
        app_id = self.app_id
        platform = self.platform
        parent = self.parent()
        show_filename_mode = getattr(self, "show_filename_mode", False)
        self.close()

        def _reopen():
            new_popup = RomListPopup(
                meta, theme_manager, app_id, platform, parent=parent
            )
            new_popup.show_filename_mode = show_filename_mode
            if keep_state:
                new_popup.current_dir = backup_current_dir
            new_popup.reload()
            if keep_state and backup_focus_filename:
                idx = new_popup._find_entry_index_by_filename(backup_focus_filename)
                if idx is not None:
                    new_popup.set_focus_index(idx)

        QTimer.singleShot(0, _reopen)

    def reload(self):
        """rom_list.json을 다시 읽고 좌우 UI를 갱신합니다."""
        self._remembered_focus_filename = self._get_focused_rom_filename()
        rom_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        if not os.path.exists(rom_path):
            QMessageBox.warning(
                self, "경고", f"rom_list.json이 존재하지 않습니다:\n{rom_path}"
            )
            return
        try:
            with open(rom_path, "r", encoding="utf-8") as f:
                self.roms = json.load(f) or []
        except Exception as e:
            QMessageBox.critical(self, "오류", f"rom_list.json 로드 실패: {e}")
            return
        self.sort_roms()
        if not hasattr(self, "current_dir"):
            self.current_dir = ""
        self._rebuild_model_entries()
        self._refresh_virtual_view(force=True)
        target_idx = 0
        if self._remembered_focus_filename:
            found = self._find_entry_index_by_filename(self._remembered_focus_filename)
            if found is not None:
                target_idx = found
        self.set_focus_index(target_idx)

    def closeEvent(self, event):
        for btn in getattr(self, "category_buttons", []):
            btn.deleteLater()
        self.category_buttons = []
        if hasattr(self, "category_popup_layout"):
            while self.category_popup_layout.count():
                item = self.category_popup_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
        for w in getattr(self, "rom_widgets", []):
            w.deleteLater()
        self.rom_widgets = []
        super().closeEvent(event)


class RomItemWidget(QWidget):
    def __init__(
        self,
        text: str,
        theme_manager,
        index: int,
        parent_popup,
        rom=None,
        is_folder=False,
        folder_path=None,
        is_up_folder=False,
    ):
        self.rom = rom or {}
        super().__init__()
        self.text = text
        self.theme_manager = theme_manager
        self.index = index
        self.parent_popup = parent_popup
        self.is_folder = is_folder
        self.folder_path = folder_path
        self.is_up_folder = is_up_folder
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(theme_manager.scale_px(20), 0, 0, 0)
        self.layout.setSpacing(0)
        font_cfg = theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = "bold" if font_cfg.get("bold", False) else "normal"
        font_color = font_cfg.get("color", "#000000")
        self.label = QLabel(text)
        self.label.setStyleSheet(
            f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_bold};\n            background-color: transparent;\n            border: none;\n            "
        )
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addWidget(self.label)
        self.setFixedHeight(theme_manager.scale_px(48))
        self.set_selected(False)

    def bind_entry(
        self,
        entry_index: int,
        text: str,
        rom=None,
        is_folder: bool = False,
        folder_path=None,
        is_up_folder: bool = False,
    ):
        """(가상화) 재사용되는 위젯에 표시 내용/타입/인덱스를 다시 바인딩"""
        self.index = entry_index
        self.text = text
        self.rom = rom or {}
        self.is_folder = is_folder
        self.folder_path = folder_path
        self.is_up_folder = is_up_folder
        self.label.setText(text or "")

    def set_selected(self, selected: bool):
        self.setAttribute(Qt.WA_StyledBackground, True)
        if selected:
            cat_focus = self.theme_manager.get("background.cat_focus")
            if not cat_focus or "value" not in cat_focus:
                self.setStyleSheet("background-color: #ff0000;")
            else:
                color = cat_focus["value"]
                self.setStyleSheet(f"background-color: {color};")
        else:
            self.setStyleSheet("background-color: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            idx = self.index
            if self.parent_popup.focus_index == idx:
                if self.parent_popup.last_clicked_index == idx:
                    if self.is_up_folder:
                        self.parent_popup.navigate_folder(
                            os.path.dirname(self.parent_popup.current_dir)
                        )
                    elif self.is_folder:
                        self.parent_popup.navigate_folder(self.folder_path)
                    else:
                        self.parent_popup.launch_current_rom()
                else:
                    self.parent_popup.set_focus_index(idx)
                    self.parent_popup.last_clicked_index = idx
            else:
                self.parent_popup.set_focus_index(idx)
                self.parent_popup.last_clicked_index = idx


class GameRunner(QObject):
    """에뮬레이터와 배치 프로세스 감시 결과를 GUI 스레드에 전달한다.

    두 작업 스레드가 동시에 종료할 수 있어 완료 플래그를 잠금으로 보호한다.
    QObject 부모는 실행이 끝날 때까지 객체를 보유하고, 복귀 후 해제한다.
    """

    restore_requested = Signal()

    def __init__(self, app_id, rom_data, parent_window=None):
        super().__init__(parent_window)
        self.restore_requested.connect(self._restore_launcher_ui, Qt.QueuedConnection)
        self._completion_lock = threading.Lock()
        self._restore_queued = False
        self.app_id = app_id
        self.rom_data = rom_data
        self.parent_window = parent_window
        self.game_metadata = rom_data
        self.platform = rom_data.get("platform", "")
        self.is_emulator_closed = False
        self.is_batch_closed = False

    def update_last_played(self):
        """카드 메타데이터와 개별 ROM의 최근 실행 시간을 각각 기록한다. 두 저장 위치의 목적이 다르다."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
            with open(path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["last_played"] = now_str
            with open(path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        try:
            rom_list_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
            with open(rom_list_path, "r", encoding="utf-8") as f:
                roms = json.load(f)
            updated = False
            for rom in roms:
                if rom.get("filename") == self.game_metadata.get("filename"):
                    rom["last_played"] = now_str
                    updated = True
                    break
            if updated:
                with open(rom_list_path, "w", encoding="utf-8") as f:
                    json.dump(roms, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def wait_all(self, processes):
        exe_name = self.game_metadata.get("exe", "")
        if not exe_name:
            exe_path = self.game_metadata.get("emulator_path", "")
            exe_name = os.path.basename(exe_path) if exe_path else ""
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
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if self.platform.lower() == "stove":
            process_names.append("stove.exe")
        for _ in range(150):
            if any(
                (
                    p.name().lower() == exe_name.lower()
                    for p in psutil.process_iter(["name"])
                )
            ):
                break
            time.sleep(0.1)
        else:
            self.restore_launcher()
            return
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

    def wait_emulator(self):
        """실행기 프로세스의 시작과 종료를 확인한다. ROM 내부 종료가 아니라 에뮬레이터 프로세스를 감시한다."""
        exe_name = self.game_metadata.get("exe", "")
        if not exe_name:
            exe_path = self.game_metadata.get("emulator_path", "")
            exe_name = os.path.basename(exe_path) if exe_path else ""
        if not exe_name:
            self.is_emulator_closed = True
            self.check_restore()
            return
        for _ in range(50):
            if any(
                (
                    p.name().lower() == exe_name.lower()
                    for p in psutil.process_iter(["name"])
                )
            ):
                break
            time.sleep(0.1)
        else:
            self.is_emulator_closed = True
            self.check_restore()
            return
        while True:
            if not any(
                (
                    p.name().lower() == exe_name.lower()
                    for p in psutil.process_iter(["name"])
                )
            ):
                self.is_emulator_closed = True
                self.check_restore()
                break
            time.sleep(2)

    def wait_batch(self, bat_process):
        """배치 프로세스 종료를 기다리고 에뮬레이터 감시와 완료 상태를 합친다. GUI 스레드에서 직접 호출하지 않는다."""
        if not bat_process or not bat_process.pid:
            self.is_batch_closed = True
            self.check_restore()
            return
        try:
            bat_process.wait()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.is_batch_closed = True
        self.check_restore()

    def check_restore(self):
        """에뮬레이터와 배치가 모두 끝났을 때 복귀를 요청한다. 최종 중복 방지는 restore_launcher의 잠금이 담당한다."""
        if self.is_emulator_closed and self.is_batch_closed:
            self.restore_launcher()

    def restore_launcher(self):
        """중복 복귀를 막고 한 번만 GUI 슬롯을 예약한다."""
        with self._completion_lock:
            if self._restore_queued:
                return
            self._restore_queued = True
        self.restore_requested.emit()

    @Slot()
    def _restore_launcher_ui(self):
        """목록 갱신과 전체화면 복귀를 GUI 스레드에서 수행한다."""
        parent = self.parent_window
        while parent:
            if hasattr(parent, "central_content"):
                parent.central_content.force_reload_all()
                break
            parent = parent.parent()
        main_launcher = parent or self.parent_window
        if main_launcher:
            main_launcher.is_game_running = False
            main_launcher.showFullScreen()
            main_launcher.raise_()
            main_launcher.activateWindow()
            handler = getattr(main_launcher, "gamepad_handler", None)
            if handler:
                QMetaObject.invokeMethod(handler, "hard_refresh", Qt.QueuedConnection)
        notification_manager.resume()
        self.deleteLater()
