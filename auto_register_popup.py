"""PC 설치 검색 → 사용자 선택 → 플랫폼별 등록을 조율하는 화면.
설치 경로 탐색은 각 scanner, 정보 수집은 crawler, 반복 작업은 RegisterThread가 맡는다.
UI 콜백과 작업 종료 신호의 순서를 중심으로 읽는다.
"""

import logging
import os
import json
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QKeyEvent
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QSizePolicy,
    QApplication,
)
from popup_windows import BasePopup
from register_progress_popup import RegisterProgressPopup
from register_thread import RegisterThread
from popup_alert import CustomAlertDialog
from cdp_dom_scraper_epic import run_cdp_register_epic
from gog_crawler import register_game as register_game_gog
from cdp_dom_scraper_stove import run_cdp_register_stove


class SmartLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._press_pos = None
        self._moved = False

    def mousePressEvent(self, event):
        self._press_pos = event.pos()
        self._moved = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos:
            delta = event.pos() - self._press_pos
            if delta.manhattanLength() > 10:
                self._moved = True
                event.ignore()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self._moved:
            self.clicked.emit()
        self._press_pos = None
        self._moved = False
        super().mouseReleaseEvent(event)


class DraggableScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_pos = None
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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


class AutoRegisterPopup(BasePopup):
    def apply_popup_label_style(self, widget):
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = font_cfg.get("bold", False)
        color = font_cfg.get("color", "#FFFFFF")
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        widget.setFont(font)
        widget.setStyleSheet(
            f"\n            color: {color};\n            QCheckBox::indicator {{\n                width: {self.theme_manager.scale_px(24)}px;\n                height: {self.theme_manager.scale_px(24)}px;\n                background-color: {color};\n                border: 1px solid {color};\n            }}\n            QCheckBox::indicator:checked {{\n                background-color: {color};\n                border: 1px solid {color};\n            }}\n            "
        )

    def apply_game_list_style(self, widget):
        font_cfg = self.theme_manager.get("fonts.게임리스트", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = font_cfg.get("bold", False)
        color = font_cfg.get("color", "#FFFFFF")
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        widget.setFont(font)
        widget.setStyleSheet(f"color: {color};")

    def __init__(self, parent=None):
        self.platform_checkboxes = {}
        self.focus_index = 0
        self.focus_group = "platform"
        self.platform_widgets = []
        self.main_widgets = []
        super().__init__(parent)

    def init_ui(self):
        self.apply_background("popup")
        main_layout = QVBoxLayout()
        self.icon_map = {}
        platforms = ["Steam", "Epic", "GOG", "STOVE"]
        raw_icon_map = {}
        for platform in platforms:
            key = f"platform_icons.{platform}"
            path = self.theme_manager.get(key)
            if path:
                raw_icon_map[platform] = path
        self.icon_map = {k.upper(): v for (k, v) in raw_icon_map.items()}
        self.platform_frame = QFrame()
        platform_layout = QHBoxLayout(self.platform_frame)
        platform_layout.setSpacing(20)
        for platform in platforms:
            cb = QCheckBox()
            cb.setIcon(QIcon(self.icon_map.get(platform.upper(), "")))
            cb.setIconSize(
                QSize(self.theme_manager.scale_px(120), self.theme_manager.scale_px(80))
            )
            cb.setStyleSheet(
                f"\n                padding: 0px;\n                margin: 0px;\n                background-color: transparent;\n                border: none;\n                qproperty-iconSize: {self.theme_manager.scale_px(120)}px {self.theme_manager.scale_px(80)}px;\n            "
            )
            cb.setFixedSize(
                self.theme_manager.scale_px(140), self.theme_manager.scale_px(100)
            )
            cb.setToolTip(platform)
            self.platform_checkboxes[platform] = cb
            platform_layout.addWidget(cb)
            self.platform_widgets.append(cb)
        main_layout.addWidget(self.platform_frame)
        self.search_btn = QPushButton("검색")
        self.apply_popup_label_style(self.search_btn)
        self.search_btn.setFixedHeight(self.theme_manager.scale_px(50))
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        color = font_cfg.get("color", "#FFFFFF")
        border_width = 2
        self.search_btn.setStyleSheet(
            f"\n            font-size: {self.theme_manager.scale_px(24)}px;\n            padding: {self.theme_manager.scale_px(10)}px;\n            color: {color};\n            border: {border_width}px solid {color};\n            "
        )
        self.search_btn.clicked.connect(self.search_installed_games)
        main_layout.addWidget(self.search_btn)
        self.main_widgets.append(self.search_btn)
        self.result_area = DraggableScrollArea()
        self.result_area.setWidgetResizable(True)
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_area.setWidget(self.result_widget)
        self.select_all_checkbox = QCheckBox("전체 선택")
        self.apply_popup_label_style(self.select_all_checkbox)
        self.select_all_checkbox.setStyleSheet(
            f"font-size: {self.theme_manager.scale_px(24)}px; padding: {self.theme_manager.scale_px(10)}px; color: {color};"
        )
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_checkboxes)
        self.select_all_checkbox.clicked.connect(self.handle_select_all_click)
        main_layout.addWidget(self.select_all_checkbox)
        main_layout.addWidget(self.result_area)
        self.main_widgets.append(self.select_all_checkbox)
        self.register_btn = QPushButton("등록")
        self.apply_popup_label_style(self.register_btn)
        self.register_btn.setFixedHeight(self.theme_manager.scale_px(50))
        self.register_btn.setStyleSheet(
            f"\n            font-size: {self.theme_manager.scale_px(24)}px;\n            padding: {self.theme_manager.scale_px(10)}px;\n            color: {color};\n            border: {border_width}px solid {color};\n            "
        )
        self.register_btn.clicked.connect(self.start_register_process)
        main_layout.addWidget(self.register_btn)
        self.setLayout(main_layout)
        self.highlight_focused_widget()
        self.override_select_all_click()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
            return
        result_count = self.result_layout.count()
        if self.focus_group == "platform":
            if key in (Qt.Key_D, Qt.Key_Right):
                self.move_focus(1, self.platform_widgets)
            elif key in (Qt.Key_A, Qt.Key_Left):
                self.move_focus(-1, self.platform_widgets)
            elif key in (Qt.Key_S, Qt.Key_Down):
                self.focus_group = "main"
                self.focus_index = 0
                self.highlight_focused_widget()
        elif self.focus_group == "main":
            if key in (Qt.Key_S, Qt.Key_Down):
                if self.focus_index == 0:
                    self.focus_index = 1
                elif self.focus_index == 1:
                    if result_count > 0:
                        self.focus_group = "results"
                        self.focus_index = 0
                    else:
                        self.focus_group = "register"
                        self.focus_index = 0
                self.highlight_focused_widget()
            elif key in (Qt.Key_W, Qt.Key_Up):
                if self.focus_index == 0:
                    self.focus_group = "platform"
                    self.focus_index = 0
                elif self.focus_index == 1:
                    self.focus_index = 0
                self.highlight_focused_widget()
        elif self.focus_group == "results":
            if key in (Qt.Key_S, Qt.Key_Down):
                if self.focus_index < result_count - 1:
                    self.focus_index += 1
                else:
                    self.focus_group = "register"
                    self.focus_index = 0
                self.highlight_focused_widget()
            elif key in (Qt.Key_W, Qt.Key_Up):
                if self.focus_index > 0:
                    self.focus_index -= 1
                else:
                    self.focus_group = "main"
                    self.focus_index = 1
                self.highlight_focused_widget()
        elif self.focus_group == "register":
            if key in (Qt.Key_W, Qt.Key_Up):
                if result_count > 0:
                    self.focus_group = "results"
                    self.focus_index = result_count - 1
                else:
                    self.focus_group = "main"
                    self.focus_index = 1
                self.highlight_focused_widget()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.activate_focused_widget()
        else:
            super().keyPressEvent(event)

    def move_focus(self, direction, widget_list):
        self.focus_index = (self.focus_index + direction) % len(widget_list)
        self.highlight_focused_widget()

    def highlight_focused_widget(self):
        for w in self.platform_widgets + self.main_widgets:
            w.setStyleSheet(w.styleSheet().replace("border: 2px solid orange;", ""))
        for i in range(self.result_layout.count()):
            widget = self.result_layout.itemAt(i).widget()
            widget.setStyleSheet("")
        self.register_btn.setStyleSheet(
            self.register_btn.styleSheet().replace("border: 2px solid orange;", "")
        )
        if self.focus_group == "platform":
            current = self.platform_widgets[self.focus_index]
            current.setStyleSheet(current.styleSheet() + "border: 2px solid orange;")
        elif self.focus_group == "main":
            current = self.main_widgets[self.focus_index]
            current.setStyleSheet(current.styleSheet() + "border: 2px solid orange;")
        elif self.focus_group == "results":
            current = self.result_layout.itemAt(self.focus_index).widget()
            focus_color = self.theme_manager.get("background.cat_focus", {}).get(
                "value", "#e0f0ff"
            )
            current.setStyleSheet(f"background-color: {focus_color};")
            self.result_area.ensureWidgetVisible(current)
        elif self.focus_group == "register":
            current = self.register_btn
            current.setStyleSheet(current.styleSheet() + "border: 2px solid orange;")
        current.setFocus()

    def activate_focused_widget(self):
        if self.focus_group == "platform":
            self.platform_widgets[self.focus_index].toggle()
        elif self.focus_group == "main":
            widget = self.main_widgets[self.focus_index]
            if isinstance(widget, QCheckBox):
                if widget is self.select_all_checkbox:
                    self.handle_select_all_click(widget.isChecked())
                else:
                    widget.toggle()
            elif isinstance(widget, QPushButton):
                widget.click()
        elif self.focus_group == "results":
            widget = self.result_layout.itemAt(self.focus_index).widget()
            layout = widget.layout()
            checkbox = layout.itemAt(0).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.toggle()
        elif self.focus_group == "register":
            self.register_btn.click()

    def _get_font(self, key, default_size=22):
        f = self.theme_manager.get(f"fonts.{key}", {})
        font = QFont(f.get("family", "맑은 고딕"), f.get("size", default_size))
        font.setBold(f.get("bold", False))
        return font

    def apply_background(self, section_key):
        bg_cfg = self.theme_manager.get(f"background.{section_key}", {})
        if bg_cfg.get("type") == "color":
            color = bg_cfg.get("value", "#FFFFFF")
            self.setStyleSheet(f"background-color: {color};")
        elif bg_cfg.get("type") == "image":
            image_path = self.theme_manager.get("bg." + bg_cfg.get("value", ""), "")
            self.setStyleSheet(
                f"background-image: url({image_path}); background-position: center; background-repeat: no-repeat; background-size: cover;"
            )

    def render_results(self, results, platform):
        """설치 검색 결과를 체크 가능한 행으로 만든다. 저장에 필요한 ID·실행 경로는 행의 속성으로 보존한다."""
        for game in results:
            game_widget = QWidget()
            game_layout = QHBoxLayout(game_widget)
            game_layout.setContentsMargins(
                self.theme_manager.scale_px(20),
                self.theme_manager.scale_px(20),
                self.theme_manager.scale_px(20),
                self.theme_manager.scale_px(20),
            )
            game_layout.setSpacing(self.theme_manager.scale_px(30))
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_select_all_checkbox)
            checkbox.setToolTip(platform)
            checkbox.setIconSize(
                QSize(self.theme_manager.scale_px(24), self.theme_manager.scale_px(24))
            )
            self.apply_popup_label_style(checkbox)
            checkbox.setStyleSheet(
                checkbox.styleSheet() + "padding: 0px; margin: 0px; border: none;"
            )
            checkbox.setFocusPolicy(Qt.NoFocus)
            game_layout.addWidget(checkbox)

            def make_toggle_handler(cb):
                return lambda event: cb.setChecked(not cb.isChecked())

            platform_icon_label = QLabel()
            platform_icon_path = self.icon_map.get(
                platform.upper(), f"icons/{platform.lower()}.png"
            )
            platform_icon_label.setFixedSize(
                self.theme_manager.scale_px(48), self.theme_manager.scale_px(48)
            )
            platform_icon_label.setScaledContents(True)
            platform_icon_label.setPixmap(QPixmap(platform_icon_path))
            platform_icon_label.mousePressEvent = make_toggle_handler(checkbox)
            platform_icon_label.setFocusPolicy(Qt.NoFocus)
            game_layout.addWidget(platform_icon_label)
            icon_label = QLabel()
            icon_label.setFixedSize(
                self.theme_manager.scale_px(48), self.theme_manager.scale_px(48)
            )
            icon_label.setScaledContents(True)
            icon_label.setFocusPolicy(Qt.NoFocus)
            exe_path = game.get("exe_full_path", "")
            icon_loaded = False
            if os.path.exists(exe_path):
                try:
                    from PIL import Image
                    import win32gui
                    import win32ui
                    import win32con

                    (large, _) = win32gui.ExtractIconEx(exe_path, 0)
                    if large:
                        hicon = large[0]
                        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                        hdc_mem = hdc.CreateCompatibleDC()
                        hbmp = win32ui.CreateBitmap()
                        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
                        hdc_mem.SelectObject(hbmp)
                        win32gui.DrawIconEx(
                            hdc_mem.GetSafeHdc(),
                            0,
                            0,
                            hicon,
                            32,
                            32,
                            0,
                            0,
                            win32con.DI_NORMAL,
                        )
                        bmpinfo = hbmp.GetInfo()
                        bmpstr = hbmp.GetBitmapBits(True)
                        img = Image.frombuffer(
                            "RGBA",
                            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                            bmpstr,
                            "raw",
                            "BGRA",
                        ).copy()
                        (r, g, b, a) = img.split()
                        img = Image.merge("RGB", (r, g, b))
                        data = img.tobytes("raw", "RGB")
                        qimg = QImage(data, img.width, img.height, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        icon_label.setPixmap(pixmap)
                        icon_loaded = True
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            if not icon_loaded:
                blank = QPixmap(32, 32)
                blank.fill(Qt.transparent)
                icon_label.setPixmap(blank)
            icon_label.mousePressEvent = make_toggle_handler(checkbox)
            game_layout.addWidget(icon_label)
            title_label = SmartLabel(game["title"])
            title_label.setToolTip(game["appid"])
            self.apply_game_list_style(title_label)
            title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            title_label.clicked.connect(checkbox.toggle)
            title_label.setFocusPolicy(Qt.NoFocus)
            game_layout.addWidget(title_label)
            self.result_layout.addWidget(game_widget)
            game_widget.install_path = game["path"]
            game_widget.exe_path = game["exe_full_path"]
            game_widget.appid = game["appid"]
            game_widget.service_code = game.get("service_code", "")

    def search_installed_games(self):
        """선택된 플랫폼의 설치 흔적을 읽고 이미 등록된 경로를 제외한다.
        설치 검색과 상품 정보 수집은 별도 단계다. 이 Classic 화면의 검색 일부는 GUI에서
        동기 실행되므로 느린 디스크에서 지연될 수 있다. 작업 스레드 분리는 확장 과제다.
        """
        from steam_scanner import scan_installed_steam_games
        from epic_scanner import scan_epic_games
        from gog_scanner import scan_gog_installed_games
        from stove_scanner import scan_stove_games

        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        checked_platforms = [
            name for (name, cb) in self.platform_checkboxes.items() if cb.isChecked()
        ]
        self.progress_popup = RegisterProgressPopup(self.theme_manager, self)
        self.progress_popup.set_text("검색 중입니다...")
        self.progress_popup.show()
        QApplication.processEvents()
        if "Steam" in checked_platforms:
            try:
                steam_results = scan_installed_steam_games()
                registered_paths = set()
                libs_dir = os.path.join("l_libs", "steam")
                if os.path.exists(libs_dir):
                    for appid in os.listdir(libs_dir):
                        meta_path = os.path.join(libs_dir, appid, "meta.json")
                        if os.path.isfile(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                                    exe_path = meta.get("exe_full_path")
                                    if exe_path:
                                        registered_paths.add(exe_path.lower())
                            except Exception as e:
                                logging.getLogger(__name__).debug(
                                    "작업 실패: %s", type(e).__name__
                                )
                filtered_results = [
                    g
                    for g in steam_results
                    if g.get("exe_full_path", "").lower() not in registered_paths
                ]
                unique = {}
                for g in filtered_results:
                    exe = g.get("exe_full_path", "").lower()
                    if exe and exe not in unique:
                        unique[exe] = g
                filtered_results = list(unique.values())
                self.render_results(filtered_results, platform="steam")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if "Epic" in checked_platforms:
            try:
                manifest_path = os.path.expandvars(
                    "%ProgramData%\\Epic\\EpicGamesLauncher\\Data\\Manifests"
                )
                epic_results = scan_epic_games(manifest_path)
                registered_paths = set()
                libs_dir = os.path.join("l_libs", "epic")
                if os.path.exists(libs_dir):
                    for appid in os.listdir(libs_dir):
                        meta_path = os.path.join(libs_dir, appid, "meta.json")
                        if os.path.isfile(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                                    exe_path = meta.get("exe_full_path")
                                    if exe_path:
                                        registered_paths.add(exe_path.lower())
                            except Exception as e:
                                logging.getLogger(__name__).debug(
                                    "작업 실패: %s", type(e).__name__
                                )
                filtered_results = [
                    g
                    for g in epic_results
                    if g.get("exe_full_path", "").lower() not in registered_paths
                ]
                unique = {}
                for g in filtered_results:
                    exe = g.get("exe_full_path", "").lower()
                    if exe and exe not in unique:
                        unique[exe] = g
                filtered_results = list(unique.values())
                self.render_results(filtered_results, platform="epic")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if "GOG" in checked_platforms:
            try:
                db_path = os.path.expandvars(
                    "%ProgramData%\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
                )
                gog_results = scan_gog_installed_games(db_path)
                registered_paths = set()
                libs_dir = os.path.join("l_libs", "gog")
                if os.path.exists(libs_dir):
                    for appid in os.listdir(libs_dir):
                        meta_path = os.path.join(libs_dir, appid, "meta.json")
                        if os.path.isfile(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                                    exe_path = meta.get("exe_full_path")
                                    if exe_path:
                                        registered_paths.add(exe_path.lower())
                            except Exception as e:
                                logging.getLogger(__name__).debug(
                                    "작업 실패: %s", type(e).__name__
                                )
                filtered_results = [
                    g
                    for g in gog_results
                    if g.get("exe_full_path", "").lower() not in registered_paths
                ]
                unique = {}
                for g in filtered_results:
                    exe = g.get("exe_full_path", "").lower()
                    if exe and exe not in unique:
                        unique[exe] = g
                filtered_results = list(unique.values())
                self.render_results(filtered_results, platform="gog")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if "STOVE" in checked_platforms:
            try:
                config_path = os.path.expandvars(
                    "%LocalAppData%\\STOVE\\Config\\ClientConfig.json"
                )
                manifest_dir = os.path.expandvars("%LocalAppData%\\STOVE\\GameManifest")
                stove_results = scan_stove_games(config_path, manifest_dir)
                registered_paths = set()
                libs_dir = os.path.join("l_libs", "stove")
                if os.path.exists(libs_dir):
                    for appid in os.listdir(libs_dir):
                        meta_path = os.path.join(libs_dir, appid, "meta.json")
                        if os.path.isfile(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                                    game_path = meta.get("path")
                                    if game_path:
                                        registered_paths.add(game_path.lower())
                            except Exception as e:
                                logging.getLogger(__name__).debug(
                                    "작업 실패: %s", type(e).__name__
                                )
                filtered_results = [
                    g
                    for g in stove_results
                    if g.get("path", "").lower() not in registered_paths
                ]
                unique = {}
                for g in filtered_results:
                    p = g.get("path", "").lower()
                    if p and p not in unique:
                        unique[p] = g
                filtered_results = list(unique.values())
                self.render_results(filtered_results, platform="stove")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.progress_popup.close()

    def start_register_process(self):
        """사용자가 체크한 항목으로 새 등록 회차를 시작한다. 실패 집계와 완료 가드를 이전 회차에서 재사용하지 않는다."""
        self._register_complete_called = False
        self._close_when_finished = False
        self.platform_order = ["steam", "epic", "gog", "stove"]
        self.platform_index = 0
        self.total_fail_list = []
        self.total_auth_queue = []
        self.checked_games = self.get_checked_games()
        if not self.checked_games:
            return
        self.progress_popup = RegisterProgressPopup(self.theme_manager, self)
        self.progress_popup.set_text("등록 중입니다...")
        self.progress_popup.show()
        self.start_next_platform()

    def start_next_platform(self):
        """플랫폼별 작업을 하나씩 진행한다. 비어 있는 플랫폼은 건너뛰고 작업이 있으면 종료 신호를 연결한 뒤 시작한다."""
        if self.platform_index >= len(self.platform_order):
            self.on_register_complete()
            return
        platform = self.platform_order[self.platform_index]
        platform_games = [
            g for g in self.checked_games if g["appid"].startswith(platform)
        ]
        if not platform_games:
            self.platform_index += 1
            self.start_next_platform()
            return
        from steam_crawler import register_game as register_game_steam

        platform_map = {
            "steam": register_game_steam,
            "epic": run_cdp_register_epic,
            "gog": register_game_gog,
            "stove": run_cdp_register_stove,
        }
        crawler = platform_map.get(platform)
        if not crawler:
            self.platform_index += 1
            self.start_next_platform()
            return
        try:
            self.current_runner = RegisterThread(
                games=platform_games,
                platform=platform,
                crawler_fn=crawler,
                target_root=f"l_libs/{platform}",
            )
            self.current_runner.finished.connect(self.on_runner_finished)
            self.current_runner.start()
        except Exception:
            self.platform_index += 1
            self.start_next_platform()

    def on_runner_finished(self):
        """이전 스레드가 완전히 끝난 뒤에만 다음 스레드로 교체한다.

        auth_required와 finished 양쪽에서 current_runner를 바꾸면 이전 작업의
        finished가 새 작업을 끝난 것으로 처리할 수 있다. 종료 경로를 하나로 모은다.
        """
        runner = self.sender()
        if runner is not self.current_runner:
            return
        if getattr(self, "_close_when_finished", False):
            self.close()
            return
        self.total_fail_list.extend(runner.fail_list)
        auth_queue = runner.get_auth_queue()
        if (
            auth_queue
            and self.current_runner.platform == "steam"
            and (
                self.current_runner.crawler_fn.__name__
                != "run_single_steam_cdp_register"
            )
        ):
            runner.deleteLater()
            self.on_auth_required(auth_queue)
            return
        if auth_queue:
            self.total_fail_list.extend(
                (game.get("title", "이름 없음"), "인증 후 수집 실패")
                for game in auth_queue
            )
        runner.deleteLater()
        self.current_runner = None
        self.platform_index += 1
        self.start_next_platform()

    def on_auth_required(self, auth_queue):
        """기존 스레드가 종료된 후 Steam 인증 필요 항목만 브라우저 수집기로 재시도한다. 자동 전체 재등록은 하지 않는다."""
        if not auth_queue:
            return
        from cdp_dom_scraper_steam import run_single_steam_cdp_register
        from register_thread import RegisterThread

        self.progress_popup.set_text("등록 중입니다...")
        QApplication.processEvents()
        self.current_runner = RegisterThread(
            games=auth_queue,
            platform="steam",
            crawler_fn=run_single_steam_cdp_register,
            target_root="l_libs/steam",
        )
        self.current_runner.finished.connect(self.on_runner_finished)
        self.current_runner.start()

    def on_register_complete(self, success_override=None):
        """전체 플랫폼 실패 집계를 바탕으로 결과를 알리고 라이브러리를 다시 읽는다. 마지막 플랫폼 성공만으로 전체 성공을 판단하지 않는다."""
        if getattr(self, "_register_complete_called", False):
            return
        self._register_complete_called = True
        if success_override is not None:
            success = success_override
        else:
            success = not self.total_fail_list
        if success:
            alert = CustomAlertDialog(
                "등록 완료",
                "선택한 게임이 성공적으로 등록되었습니다!",
                self.theme_manager,
                self,
            )
            alert.exec()
        else:
            alert = CustomAlertDialog(
                "일부 등록 실패",
                "일부 게임 등록에 실패했습니다. 로그를 확인하세요.",
                self.theme_manager,
                self,
            )
            alert.exec()
        self.progress_popup.close()
        self.close()

        def delayed_refresh(target_window):
            target_window.central_content.load_registered_games()
            target_window.central_content.on_category_changed(0)
            target_window.central_content.render_cards()

        for w in QApplication.topLevelWidgets():
            if w.isVisible() and hasattr(w, "central_content"):
                QTimer.singleShot(500, lambda w=w: delayed_refresh(w))
                break

    def get_checked_games(self):
        """체크한 행에서 플랫폼별 수집기가 기대하는 사전 구조를 만든다. 화면 제목과 플랫폼 상품 ID는 별개의 값이다."""
        results = []
        for i in range(self.result_layout.count()):
            widget = self.result_layout.itemAt(i).widget()
            if not widget:
                continue
            layout = widget.layout()
            if not layout:
                continue
            checkbox = layout.itemAt(0).widget()
            title_label = layout.itemAt(3).widget()
            if checkbox and checkbox.isChecked() and title_label:
                platform = checkbox.toolTip().lower()
                appid = widget.appid
                folder_name = title_label.text()
                os.path.join(
                    os.path.expandvars("%ProgramFiles(x86)%\\Steam"),
                    "steamapps",
                    "common",
                    folder_name,
                )
                if platform == "steam":
                    results.append(
                        {
                            "appid": f"steam_{appid}",
                            "title": folder_name,
                            "librarycache_path": os.path.join(
                                os.path.expandvars("%ProgramFiles(x86)%\\Steam"),
                                "appcache",
                                "librarycache",
                                appid,
                            ),
                            "path": getattr(widget, "install_path", ""),
                            "exe_full_path": getattr(widget, "exe_path", ""),
                            "exe": os.path.basename(getattr(widget, "exe_path", "")),
                            "steam_root": os.path.expandvars(
                                "%ProgramFiles(x86)%\\Steam"
                            ),
                        }
                    )
                elif platform == "epic":
                    results.append(
                        {
                            "appid": appid,
                            "title": folder_name,
                            "path": getattr(widget, "install_path", ""),
                            "exe_full_path": getattr(widget, "exe_path", ""),
                            "exe": os.path.basename(getattr(widget, "exe_path", "")),
                        }
                    )
                elif platform == "gog":
                    results.append(
                        {
                            "appid": appid,
                            "title": folder_name,
                            "path": getattr(widget, "install_path", ""),
                            "exe_full_path": getattr(widget, "exe_path", ""),
                            "exe": os.path.basename(getattr(widget, "exe_path", "")),
                        }
                    )
                elif platform == "stove":
                    results.append(
                        {
                            "appid": appid,
                            "title": folder_name,
                            "path": getattr(widget, "install_path", ""),
                            "exe_full_path": getattr(widget, "exe_path", ""),
                            "exe": os.path.basename(getattr(widget, "exe_path", "")),
                            "service_code": getattr(widget, "service_code", ""),
                        }
                    )
        return results

    def toggle_all_checkboxes(self, state):
        """전체 체크를 바꾸는 동안 개별 시그널을 막고 마지막에 전체 선택 상태를 한 번 갱신한다."""
        checked = state == Qt.Checked
        for i in range(self.result_layout.count()):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                layout = widget.layout()
                checkbox = layout.itemAt(0).widget()
                if checkbox:
                    if checkbox.isChecked() != checked:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(checked)
                        checkbox.blockSignals(False)
        QApplication.processEvents()
        self.update_select_all_checkbox()

    def update_select_all_checkbox(self):
        total = self.result_layout.count()
        checked = 0
        for i in range(total):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                layout = widget.layout()
                checkbox = layout.itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    checked += 1
        self.select_all_checkbox.blockSignals(True)
        if checked == total and total > 0:
            self.select_all_checkbox.setTristate(False)
            self.select_all_checkbox.setCheckState(Qt.Checked)
        elif checked == 0:
            self.select_all_checkbox.setTristate(False)
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.select_all_checkbox.setTristate(True)
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def handle_select_all_click(self, checked):
        if self.select_all_checkbox.isChecked():
            self.toggle_all_checkboxes(Qt.Unchecked)
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.toggle_all_checkboxes(Qt.Checked)
            self.select_all_checkbox.setCheckState(Qt.Checked)

    def override_select_all_click(self):

        def custom_mouse_press(event):
            current_state = self.select_all_checkbox.checkState()
            if current_state == Qt.Checked:
                self.toggle_all_checkboxes(Qt.Unchecked)
                self.select_all_checkbox.setCheckState(Qt.Unchecked)
            else:
                self.toggle_all_checkboxes(Qt.Checked)
                self.select_all_checkbox.setCheckState(Qt.Checked)

        self.select_all_checkbox.mousePressEvent = custom_mouse_press

    def closeEvent(self, event):
        # GUI에서 wait()로 멈춰 있으면 취소 창마저 응답하지 않는다.
        # 실행 중인 QThread를 파괴하지 않고, 다음 작업 경계에서 종료를 기다린다.
        runner = getattr(self, "current_runner", None)
        if runner is not None and runner.isRunning():
            self._close_when_finished = True
            runner.requestInterruption()
            if getattr(self, "progress_popup", None):
                self.progress_popup.set_text("현재 게임의 처리가 끝나면 닫습니다…")
            event.ignore()
            return
        try:
            if hasattr(self, "current_runner") and self.current_runner is not None:
                self.current_runner.deleteLater()
                self.current_runner = None
            if hasattr(self, "progress_popup") and self.progress_popup:
                self.progress_popup.close()
                self.progress_popup = None
            if hasattr(self, "platform_order") and hasattr(self, "platform_index"):
                current = (
                    self.platform_order[self.platform_index]
                    if self.platform_index < len(self.platform_order)
                    else ""
                )
                if current in ("epic", "stove", "steam"):
                    from cdp_browser_controller import kill_all_cdp_chrome

                    kill_all_cdp_chrome()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        for widget in self.platform_widgets + self.main_widgets:
            widget.deleteLater()
        self.platform_widgets.clear()
        self.main_widgets.clear()
        for i in reversed(range(self.result_layout.count())):
            result_widget = self.result_layout.itemAt(i).widget()
            if result_widget:
                result_widget.deleteLater()
        super().closeEvent(event)
