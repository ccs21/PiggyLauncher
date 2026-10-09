"""Classic의 central_content 모듈. 역할과 읽는 순서는 docs/SOURCE_MAP.md를 참고한다."""

import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTabBar,
    QDialog,
    QGridLayout,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QEvent, QTimer, Slot, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QPixmap, QFont
import os
import json
from popup_utils import ConfirmDialog
import shutil
from collections import OrderedDict


class CentralContent(QWidget):
    @Slot()
    def load_registered_games(self):
        """플랫폼별 meta.json을 카드용 모델로 변환한다.
        PC 이미지는 게임 폴더 기준, 에뮬레이터 이미지는 테마 기준으로 경로를 해석한다.
        한 파일이 손상되어도 다른 게임은 계속 읽는다. 이 단계에서는 위젯을 만들지 않는다.
        """
        self.games = []
        platforms = ["steam", "epic", "gog", "stove", "user", "emul"]
        for platform in platforms:
            root = os.path.join("l_libs", platform)
            if not os.path.exists(root):
                continue
            for folder in os.listdir(root):
                meta_path = os.path.join(root, folder, "meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            thumb = meta.get("thumbnail", "")
                            if not os.path.isabs(thumb):
                                if platform == "emul":
                                    if thumb.startswith("theme/"):
                                        thumb_path = os.path.abspath(thumb)
                                    else:
                                        thumb_path = os.path.abspath(
                                            os.path.join("theme", thumb)
                                        )
                                else:
                                    thumb_path = os.path.join(root, folder, thumb)
                            else:
                                thumb_path = thumb
                            self.games.append(
                                {
                                    "appid": meta.get("appid", ""),
                                    "title": meta.get("title", ""),
                                    "platform": meta.get("platform", platform),
                                    "thumbnail": thumb_path,
                                    "exe_full_path": meta.get("exe_full_path", ""),
                                    "last_played": meta.get("last_played", "없음"),
                                    "categories": meta.get("categories", []),
                                }
                            )
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )

    from game_detail_screen import GameDetailScreen

    def keyPressEvent(self, event):
        if not hasattr(self, "_focus_area"):
            self._focus_area = "card"
        if self._focus_area != "card" and event.key() in [
            Qt.Key_A,
            Qt.Key_D,
            Qt.Key_Q,
            Qt.Key_E,
        ]:
            return
        if event.key() == Qt.Key_D:
            if self._focus_area == "card":
                max_idx = len(self.visible_games) - 1
                if self.is_grid_mode:
                    if self.selected_game_index < max_idx:
                        self.selected_game_index += 1
                elif self.selected_game_index < max_idx:
                    self.selected_game_index += 1
                else:
                    self.selected_game_index = 0
                item = self.card_layout.itemAt(self.selected_game_index)
                if item:
                    card = item.widget()
                    self.focused_app_id = card.property("appid")
                    self.focused_platform = card.property("platform")
                self._fast_hint = True
                self._pending_action = None
                self._pending_focus_app = None
                self.render_cards()
                self.ensure_card_visible()
                return
        elif event.key() == Qt.Key_A:
            if self._focus_area == "card":
                if self.is_grid_mode:
                    if self.selected_game_index > 0:
                        self.selected_game_index -= 1
                elif self.selected_game_index > 0:
                    self.selected_game_index -= 1
                else:
                    self.selected_game_index = len(self.visible_games) - 1
                item = self.card_layout.itemAt(self.selected_game_index)
                if item:
                    card = item.widget()
                    self.focused_app_id = card.property("appid")
                    self.focused_platform = card.property("platform")
                self._fast_hint = True
                self._pending_action = None
                self._pending_focus_app = None
                self.render_cards()
                self.ensure_card_visible()
                return
        if self._focus_area == "card":
            if event.key() == Qt.Key_E:
                if self.selected_category_index < len(self.categories) - 1:
                    self.selected_category_index += 1
                else:
                    self.selected_category_index = 0
                self.tab_bar.setCurrentIndex(self.selected_category_index)
                self.ensure_tab_visible()
                return
            elif event.key() == Qt.Key_Q:
                if self.selected_category_index > 0:
                    self.selected_category_index -= 1
                else:
                    self.selected_category_index = len(self.categories) - 1
                self.tab_bar.setCurrentIndex(self.selected_category_index)
                self.ensure_tab_visible()
                return
        if event.key() == Qt.Key_Return:
            if self._focus_area == "top" and self.btn_profile:
                from settings_popup import SettingsPopup

                popup = SettingsPopup(self.main_widget)
                popup.setFocus()
                popup.exec()
            elif self._focus_area == "bottom" and self.btn_update:
                from update_popup import UpdatePopup

                parent_window = self.window()
                popup = UpdatePopup(
                    self.theme_manager, parent_window, parent=parent_window
                )
                popup.setFocus()
                popup.exec()
            elif self._focus_area == "card" and self.selected_game_index is not None:
                item = self.card_layout.itemAt(self.selected_game_index)
                if item is not None:
                    card = item.widget()
                    app_id = card.property("appid")
                    platform = card.property("platform")
                    meta_path = os.path.join(
                        "l_libs", platform, str(app_id), "meta.json"
                    )
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            from popup_loading_launcher import launch_popup_with_loading

                            if platform == "emul":
                                from rom_list_popup import RomListPopup

                                launch_popup_with_loading(
                                    RomListPopup,
                                    meta,
                                    self.theme_manager,
                                    app_id,
                                    platform,
                                    parent=self.main_widget,
                                )
                            else:
                                from game_detail_screen import GameDetailScreen

                                launch_popup_with_loading(
                                    GameDetailScreen,
                                    meta,
                                    self.theme_manager,
                                    app_id,
                                    platform,
                                    parent=self.main_widget,
                                )
                            self.focused_app_id = app_id
                            self.focused_platform = platform
                            self._fast_hint = True
                            self._pending_action = None
                            self._pending_focus_app = None
                            self.render_cards()
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
        elif event.key() == Qt.Key_Escape:
            if self._focus_area in ["top", "bottom"]:
                self._focus_area = "card"
                self.setFocus(Qt.OtherFocusReason)
                self.render_cards()
            else:
                self.is_grid_mode = not self.is_grid_mode
                self.bottom_bar.update_view_button_icon()
                self._fast_hint = False
                self._pending_action = None
                self._pending_focus_app = None
                self.render_cards()
                QTimer.singleShot(0, self.ensure_card_visible)
                QTimer.singleShot(50, self.ensure_card_visible)
            return
        if event.key() == Qt.Key_X:
            if self._focus_area == "card" and self.visible_games:
                game = self.visible_games[self.selected_game_index]
                app_id = game["appid"]
                platform = game["platform"]
                dialog = ConfirmDialog(
                    "게임 삭제 확인",
                    "해당 게임을 런처에서 삭제하시겠습니까?\n(실제 설치된 게임은 삭제되지 않습니다.)",
                    self.theme_manager,
                    self.main_widget,
                )
                if dialog.exec() == QDialog.Accepted:
                    folder = os.path.join("l_libs", platform, str(app_id))
                    if os.path.exists(folder):
                        try:
                            shutil.rmtree(folder)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                    self.load_registered_games()
                    self.on_category_changed(self.selected_category_index)
        if event.key() == Qt.Key_C:
            if self._focus_area == "card" and self.visible_games:
                from category_select_popup import CategorySelectPopup

                game = self.visible_games[self.selected_game_index]
                popup = CategorySelectPopup(
                    game_meta=game,
                    theme_manager=self.theme_manager,
                    parent=self.main_widget,
                )
                popup.setWindowModality(Qt.ApplicationModal)
                popup.setFocus()
                popup.activateWindow()
                popup.raise_()
                popup.exec()
            return
        if event.key() == Qt.Key_W:
            if self._focus_area == "card":
                if self.is_grid_mode:
                    if self.selected_game_index >= 12:
                        self.selected_game_index -= 12
                        item = self.card_layout.itemAt(self.selected_game_index)
                        if item:
                            card = item.widget()
                            self.focused_app_id = card.property("appid")
                            self.focused_platform = card.property("platform")
                        self._fast_hint = True
                        self._pending_action = None
                        self._pending_focus_app = None
                        self.render_cards()
                        self.ensure_card_visible()
                        return
                    elif 0 < self.selected_game_index < 12:
                        self.selected_game_index = 0
                        item = self.card_layout.itemAt(self.selected_game_index)
                        if item:
                            card = item.widget()
                            self.focused_app_id = card.property("appid")
                            self.focused_platform = card.property("platform")
                        self._fast_hint = True
                        self._pending_action = None
                        self._pending_focus_app = None
                        self.render_cards()
                        self.ensure_card_visible()
                        return
                    elif self.selected_game_index == 0:
                        self._last_focused_game_index = self.selected_game_index
                        self._focus_area = "top"
                        self.clear_card_focus()
                        self._fast_hint = True
                        self._pending_action = None
                        self._pending_focus_app = None
                        self.render_cards()

                        def try_focus():
                            if not self.btn_profile:
                                return
                            self.btn_profile.setFocusPolicy(Qt.StrongFocus)
                            self.btn_profile.setEnabled(True)
                            self.btn_profile.setVisible(True)
                            self.btn_profile.raise_()
                            self.btn_profile.activateWindow()
                            if self.main_widget:
                                self.main_widget.raise_()
                                self.main_widget.activateWindow()
                            QTimer.singleShot(0, lambda: self.clearFocus())
                            QTimer.singleShot(
                                10, lambda: self.btn_profile.setFocus(Qt.TabFocusReason)
                            )
                            QTimer.singleShot(
                                50,
                                lambda: print("포커스 이동 직후:", self.focusWidget()),
                            )

                        QTimer.singleShot(50, try_focus)
                        return
                    else:
                        self.selected_game_index -= 12
                        item = self.card_layout.itemAt(self.selected_game_index)
                        if item:
                            card = item.widget()
                            self.focused_app_id = card.property("appid")
                            self.focused_platform = card.property("platform")
                        self._fast_hint = True
                        self._pending_action = None
                        self._pending_focus_app = None
                        self.render_cards()
                        self.ensure_card_visible()
                        return
                else:
                    self._last_focused_game_index = self.selected_game_index
                    self._focus_area = "top"
                    self.clear_card_focus()
                    self._fast_hint = True
                    self._pending_action = None
                    self._pending_focus_app = None
                    self.render_cards()

                    def try_focus():
                        if not self.btn_profile:
                            return
                        self.btn_profile.setFocusPolicy(Qt.StrongFocus)
                        self.btn_profile.setEnabled(True)
                        self.btn_profile.setVisible(True)
                        self.btn_profile.raise_()
                        self.btn_profile.activateWindow()
                        if self.main_widget:
                            self.main_widget.raise_()
                            self.main_widget.activateWindow()
                        QTimer.singleShot(0, lambda: self.clearFocus())
                        QTimer.singleShot(
                            10, lambda: self.btn_profile.setFocus(Qt.TabFocusReason)
                        )
                        QTimer.singleShot(
                            50, lambda: print("포커스 이동 직후:", self.focusWidget())
                        )

                    QTimer.singleShot(50, try_focus)
            elif self._focus_area == "bottom":
                self._focus_area = "card"
                self.selected_game_index = getattr(self, "_last_focused_game_index", 0)
                if self.btn_update:
                    self.btn_update.clearFocus()
                self.setFocus(Qt.OtherFocusReason)
                self._fast_hint = True
                self._pending_action = None
                self._pending_focus_app = None
                self.render_cards()
                self.ensure_card_visible()
            return
        elif event.key() == Qt.Key_S:
            if self._focus_area == "card":
                if self.is_grid_mode:
                    max_index = len(self.visible_games) - 1
                    if self.selected_game_index + 12 > max_index:
                        if self.selected_game_index < max_index:
                            self.selected_game_index = max_index
                            item = self.card_layout.itemAt(self.selected_game_index)
                            if item:
                                card = item.widget()
                                self.focused_app_id = card.property("appid")
                                self.focused_platform = card.property("platform")
                            self._fast_hint = True
                            self._pending_action = None
                            self._pending_focus_app = None
                            self.render_cards()
                            self.ensure_card_visible()
                            return
                        else:
                            self._last_focused_game_index = self.selected_game_index
                            self._focus_area = "bottom"

                            def try_focus_bottom():
                                if self.btn_update:
                                    self.btn_update.setFocusPolicy(Qt.StrongFocus)
                                    self.btn_update.setEnabled(True)
                                    self.btn_update.setVisible(True)
                                    self.btn_update.raise_()
                                    if self.main_widget:
                                        self.main_widget.raise_()
                                        self.main_widget.activateWindow()
                                    self.clearFocus()
                                    QTimer.singleShot(
                                        10,
                                        lambda: self.btn_update.setFocus(
                                            Qt.TabFocusReason
                                        ),
                                    )
                                    QTimer.singleShot(
                                        50,
                                        lambda: print(
                                            "포커스 이동 직후:", self.focusWidget()
                                        ),
                                    )

                            QTimer.singleShot(50, try_focus_bottom)
                            self.clear_card_focus()
                            self._fast_hint = True
                            self._pending_action = None
                            self._pending_focus_app = None
                            self.render_cards()
                            return
                    else:
                        self.selected_game_index += 12
                        item = self.card_layout.itemAt(self.selected_game_index)
                        if item:
                            card = item.widget()
                            self.focused_app_id = card.property("appid")
                            self.focused_platform = card.property("platform")
                        self._fast_hint = True
                        self._pending_action = None
                        self._pending_focus_app = None
                        self.render_cards()
                        self.ensure_card_visible()
                        return
                else:
                    self._last_focused_game_index = self.selected_game_index
                    self._focus_area = "bottom"

                    def try_focus_bottom():
                        if self.btn_update:
                            self.btn_update.setFocusPolicy(Qt.StrongFocus)
                            self.btn_update.setEnabled(True)
                            self.btn_update.setVisible(True)
                            self.btn_update.raise_()
                            if self.main_widget:
                                self.main_widget.raise_()
                                self.main_widget.activateWindow()
                            self.clearFocus()
                            QTimer.singleShot(
                                10, lambda: self.btn_update.setFocus(Qt.TabFocusReason)
                            )
                            QTimer.singleShot(
                                50,
                                lambda: print("포커스 이동 직후:", self.focusWidget()),
                            )

                    QTimer.singleShot(50, try_focus_bottom)
                    self.clear_card_focus()
                    self._fast_hint = True
                    self._pending_action = None
                    self._pending_focus_app = None
                    self.render_cards()
            elif self._focus_area == "top":
                self._focus_area = "card"
                self.selected_game_index = getattr(self, "_last_focused_game_index", 0)
                if self.btn_profile:
                    self.btn_profile.clearFocus()
                self.setFocus(Qt.OtherFocusReason)
                self._fast_hint = True
                self._pending_action = None
                self._pending_focus_app = None
                self.render_cards()
                self.ensure_card_visible()
            return
        if hasattr(self, "btn_profile"):
            self.btn_profile.setStyleSheet(
                "border: 4px solid orange; background: transparent;"
                if self._focus_area == "top"
                else "border: none; background: transparent;"
            )
        if hasattr(self, "btn_update"):
            self.btn_update.setStyleSheet(
                "border: 4px solid orange; background: transparent;"
                if self._focus_area == "bottom"
                else "border: none; background: transparent;"
            )

    def eventFilter(self, source, event):
        if source == self.tab_bar:
            if (
                event.type() == QEvent.MouseButtonPress
                and event.buttons() == Qt.LeftButton
            ):
                self._tab_drag_start_x = event.globalPosition().x()
            elif event.type() == QEvent.MouseMove and hasattr(
                self, "_tab_drag_start_x"
            ):
                delta = self._tab_drag_start_x - event.globalPosition().x()
                self.tab_scroll.horizontalScrollBar().setValue(
                    self.tab_scroll.horizontalScrollBar().value() + delta
                )
                self._tab_drag_start_x = event.globalPosition().x()
            elif event.type() == QEvent.MouseButtonRelease:
                if hasattr(self, "_tab_drag_start_x"):
                    del self._tab_drag_start_x
        return super().eventFilter(source, event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.is_grid_mode:
            self._drag_start_y = event.globalPosition().y()
        else:
            self._drag_start_x = event.globalPosition().x()

    def load_categories(self):
        self.categories = ["전체 게임", "최근 실행"]
        path = "configs/user_categories.json"
        if os.path.exists(path):
            try:
                import json

                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.categories.extend(loaded)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def __init__(
        self, theme_manager, btn_profile=None, btn_update=None, bottom_bar=None
    ):
        self.main_widget = None
        super().__init__()
        self.theme_manager = theme_manager
        self.selected_category_index = 0
        self.selected_game_index = 0
        self.games = []
        self.RENDER_DEBOUNCE_MS = 500
        self.FADE_OUT_MS = 500
        self.FADE_IN_MS = 300
        self._pending_action = None
        self._pending_focus_app = None
        self._fast_hint = False
        self._pending_focus_platform = None
        self._focus_lock_once = False
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_render_cards)
        self._fade_eff = None
        self._fade_anim = None
        self._fade_state = "Idle"
        self.max_cache_size = 100
        self.pixmap_cache = OrderedDict()
        self.btn_profile = btn_profile
        if self.btn_profile:
            self.btn_profile.setFocusPolicy(Qt.ClickFocus)
            self.btn_profile.setFocusProxy(self)
        self.btn_update = btn_update
        if self.btn_update:
            self.btn_update.setFocusPolicy(Qt.ClickFocus)
            self.btn_update.setFocusProxy(self)
        self.focused_app_id = None
        self.focused_platform = None
        self._focus_area = "card"
        self.is_grid_mode = False
        self.bottom_bar = bottom_bar
        self.init_ui()
        self.load_registered_games()
        self.on_category_changed(0)
        self.setFocusPolicy(Qt.StrongFocus)
        QTimer.singleShot(0, self.setFocus)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(
            self.theme_manager.scale_px(20), 0, self.theme_manager.scale_px(20), 0
        )
        self.layout.setSpacing(self.theme_manager.scale_px(5))
        self.tab_scroll = QScrollArea()
        self.tab_scroll.setStyleSheet("background-color: transparent; border: none;")
        self.tab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tab_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tab_scroll.setWidgetResizable(True)
        self.tab_scroll.setFixedHeight(self.theme_manager.scale_px(80))
        self.tab_bar = QTabBar()
        self.tab_bar.installEventFilter(self)
        self.tab_bar.setShape(QTabBar.RoundedSouth)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setMovable(False)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setUsesScrollButtons(True)
        self.tab_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.tab_bar.setElideMode(Qt.ElideNone)
        self.tab_bar.setFocusPolicy(Qt.NoFocus)
        tab_wrapper = QWidget()
        tab_wrapper_layout = QHBoxLayout(tab_wrapper)
        tab_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        tab_wrapper_layout.addStretch()
        tab_wrapper_layout.addWidget(self.tab_bar)
        tab_wrapper_layout.addStretch()
        self.tab_scroll.setWidget(tab_wrapper)
        tab_selected = self.theme_manager.get("tabs.selected", {})
        tab_unselected = self.theme_manager.get("tabs.unselected", {})
        tab_font = self.theme_manager.get("fonts.탭", {})
        font_size = tab_font.get("size", 28)
        font_family = tab_font.get("family", "맑은 고딕")
        font_weight = "bold" if tab_font.get("bold", False) else "normal"
        pad_v = self.theme_manager.scale_px(10)
        pad_h = self.theme_manager.scale_px(30)
        margin = self.theme_manager.scale_px(2)
        radius = self.theme_manager.scale_px(8)
        height_sel = self.theme_manager.scale_px(50)
        height_unsel = self.theme_manager.scale_px(30)
        border_w_sel = self.theme_manager.scale_px(tab_selected.get("border_width", 2))
        border_w_unsel = self.theme_manager.scale_px(
            tab_unselected.get("border_width", 0)
        )
        self.tab_bar.setStyleSheet(
            f"\n            QTabBar::tab {{\n                font-size: {font_size}px;\n                font-family: '{font_family}';\n                font-weight: {font_weight};\n                padding: {pad_v}px {pad_h}px;\n                margin: {margin}px;\n                border-radius: {radius}px;\n                min-width: 10px;\n            }}\n            QTabBar::tab:selected {{\n                background: {self._get_background_value(tab_selected.get('background', {}))};\n                color: {tab_selected.get('text_color', '#000000')};\n                height: {height_sel}px;\n                border: {border_w_sel}px solid {tab_selected.get('border_color', 'black')};\n            }}\n            QTabBar::tab:!selected {{\n                background: {self._get_background_value(tab_unselected.get('background', {}))};\n                color: {tab_unselected.get('text_color', '#000000')};\n                height: {height_unsel}px;\n                border: {border_w_unsel}px solid {tab_unselected.get('border_color', 'transparent')};\n            }}\n        "
        )
        self.load_categories()
        for name in self.categories:
            self.tab_bar.addTab(name)
        self.tab_bar.setCurrentIndex(0)
        self.tab_bar.currentChanged.connect(self.on_category_changed)
        font_cfg = self.theme_manager.get("fonts.카드정보", {})
        font = QFont(font_cfg.get("family", "맑은 고딕"), font_cfg.get("size", 24))
        font.setBold(font_cfg.get("bold", False))
        font.setItalic(font_cfg.get("italic", False))
        self.info_layout = QHBoxLayout()
        self.info_layout.setContentsMargins(0, self.theme_manager.scale_px(10), 0, 0)
        self.info_layout.setSpacing(self.theme_manager.scale_px(12))
        self.info_layout.setAlignment(Qt.AlignVCenter)
        self.info_icon_label = QLabel()
        self.info_icon_label.setFixedSize(
            self.theme_manager.scale_px(36), self.theme_manager.scale_px(36)
        )
        self.info_icon_label.setScaledContents(True)
        font_cfg = self.theme_manager.get("fonts.카드정보", {})
        font = QFont(font_cfg.get("family", "맑은 고딕"), font_cfg.get("size", 24))
        font.setBold(font_cfg.get("bold", False))
        font.setItalic(font_cfg.get("italic", False))
        self.info_text_label = QLabel("플랫폼 | 제목 | 최근 실행: -")
        self.info_text_label.setFont(font)
        font_color = font_cfg.get("color", "#FFFFFF")
        self.info_text_label.setStyleSheet(f"color: {font_color};")
        self.info_layout.addWidget(self.info_icon_label)
        self.info_layout.addWidget(self.info_text_label)
        self.layout.addLayout(self.info_layout)
        self.card_scroll = QScrollArea()
        self.card_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.card_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setStyleSheet("background-color: transparent; border: none;")
        self.card_container = QWidget()
        self.card_container.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.card_layout = QHBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(self.theme_manager.scale_px(20))
        self.card_scroll.setWidget(self.card_container)
        self._fade_eff = QGraphicsOpacityEffect(self.card_container)
        self.card_container.setGraphicsEffect(self._fade_eff)
        self._fade_eff.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._fade_eff, b"opacity", self)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self.layout.addWidget(self.card_scroll, stretch=1)
        self.layout.addWidget(self.tab_scroll)
        self.refresh_tab_bar()
        self.render_cards()

    def force_reload_all(self):
        """파일을 다시 읽고 현재 카테고리를 재적용한다. 저장 직후 모델과 화면이 어긋나지 않도록 함께 갱신한다."""
        self.load_registered_games()
        self.on_category_changed(self.selected_category_index)

    def refresh_tab_bar(self):
        while self.tab_bar.count() > 0:
            self.tab_bar.removeTab(0)
        self.load_categories()
        for name in self.categories:
            self.tab_bar.addTab(name)

    def on_category_changed(self, index):
        """카테고리 전환과 선택 위치 복원을 처리한다. 탭 값을 코드로 바꿀 때는 신호를 잠시 막아 재진입을 피한다."""
        if hasattr(self, "tab_bar") and self.tab_bar.currentIndex() != index:
            self.tab_bar.blockSignals(True)
            try:
                self.tab_bar.setCurrentIndex(index)
            finally:
                self.tab_bar.blockSignals(False)
        prev_cat = getattr(self, "selected_category_index", 0)
        same_cat = index == prev_cat
        prev_app = getattr(self, "focused_app_id", None)
        prev_plat = getattr(self, "focused_platform", None)
        self.selected_category_index = index
        selected_cat = (
            self.categories[self.selected_category_index]
            if self.categories
            else "전체 게임"
        )
        if selected_cat == "전체 게임":
            no_play = [
                g for g in self.games if g.get("last_played") in [None, "", "없음"]
            ]
            has_play = [
                g for g in self.games if g.get("last_played") not in [None, "", "없음"]
            ]
            has_play.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = no_play + has_play
        elif selected_cat == "최근 실행":
            vg = [
                g for g in self.games if g.get("last_played") not in [None, "", "없음"]
            ]
            vg.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = vg
        else:
            games_in_cat = [
                g for g in self.games if selected_cat in g.get("categories", [])
            ]
            has_play = [
                g
                for g in games_in_cat
                if g.get("last_played") not in [None, "", "없음"]
            ]
            no_play = [
                g for g in games_in_cat if g.get("last_played") in [None, "", "없음"]
            ]
            has_play.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = has_play + no_play

        def _find_index_by(app, plat):
            if app is None or not self.visible_games:
                return -1
            app_s = str(app)
            for i, g in enumerate(self.visible_games):
                ga = str(g.get("appid"))
                gp = str(g.get("platform"))
                if ga == app_s and (plat is None or gp.lower() == str(plat).lower()):
                    return i
            for i, g in enumerate(self.visible_games):
                if str(g.get("appid")) == app_s:
                    return i
            return -1

        target_idx = -1
        if self._focus_lock_once:
            target_idx = _find_index_by(prev_app, prev_plat)
        elif same_cat:
            target_idx = _find_index_by(prev_app, prev_plat)
        else:
            target_idx = 0 if self.visible_games else -1
        if target_idx >= 0 and self.visible_games:
            self.selected_game_index = target_idx
            g = self.visible_games[target_idx]
            self.focused_app_id = g.get("appid")
            self.focused_platform = g.get("platform")
        else:
            self.selected_game_index = 0
            if self.visible_games:
                g0 = self.visible_games[0]
                self.focused_app_id = g0.get("appid")
                self.focused_platform = g0.get("platform")
            else:
                self.focused_app_id = None
                self.focused_platform = None
        self._focus_lock_once = False
        self._pending_action = None
        self._pending_focus_app = None
        self._pending_focus_platform = None
        self._fast_hint = True
        self.render_cards()

    @Slot()
    def render_cards(self):
        """여러 입력에서 오는 렌더 요청을 짧은 타이머로 합친다.
        일반 경로는 페이드아웃 후 재구성하며, _fast_hint는 즉시 갱신 경로다.
        요청을 합치는 것과 백그라운드 스레드에서 그리는 것은 다르다. 실제 Qt 위젯은 GUI에서 만든다.
        """
        is_fast = getattr(self, "_fast_hint", False)
        if is_fast:
            if hasattr(self, "_render_timer") and self._render_timer.isActive():
                self._render_timer.stop()
            if getattr(self, "_fade_anim", None):
                self._fade_anim.stop()
            if getattr(self, "_fade_eff", None):
                self._fade_eff.setOpacity(1.0)
            if hasattr(self, "card_container"):
                self.card_container.setEnabled(True)
            self._fade_state = "Idle"
            self._build_cards_ui(self.visible_games)
            self._fast_hint = False
            return
        self._fast_hint = False
        self._render_timer.start(self.RENDER_DEBOUNCE_MS)
        if self._fade_state in ("Idle", "FadingIn"):
            self._start_fade_out()
            self._fade_state = "FadingOut"
        else:
            pass

    def _do_render_cards(self):
        """최신 모델을 읽고 등록·삭제·실행 복귀에 맞춰 선택 위치를 계산한다.
        인덱스만 저장하면 정렬 후 다른 게임을 가리키므로 appid와 platform을 함께 사용한다.
        페이드 상태를 확인한 뒤 UI를 재구성한다. 호출 시점과 실제 그리기 시점이 다를 수 있다.
        """
        if self._fade_state == "FadingOut" and self._fade_eff.opacity() > 0.05:
            QTimer.singleShot(50, self._do_render_cards)
            return
        self._fade_state = "Rendering"
        try:
            self.load_registered_games()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        action = self._pending_action
        focus_app = self._pending_focus_app
        if action == "register_new":
            self.selected_category_index = 0
            if hasattr(self, "tab_bar"):
                self.tab_bar.blockSignals(True)
                try:
                    self.tab_bar.setCurrentIndex(0)
                finally:
                    self.tab_bar.blockSignals(False)
            self._recompute_visible_games_for_current_category()
            self.selected_game_index = 0
            if self.visible_games:
                g0 = self.visible_games[0]
                self.focused_app_id = g0["appid"]
                self.focused_platform = g0["platform"]
            self._focus_lock_once = False
        else:
            self._recompute_visible_games_for_current_category()
            if focus_app is not None:
                focus_app_str = str(focus_app)
                focus_plat = getattr(self, "_pending_focus_platform", None)
                idx = next(
                    (
                        i
                        for (i, g) in enumerate(self.visible_games)
                        if str(g.get("appid")) == focus_app_str
                        and (
                            focus_plat is None
                            or str(g.get("platform")).lower() == str(focus_plat).lower()
                        )
                    ),
                    -1,
                )
                if idx < 0:
                    idx = next(
                        (
                            i
                            for (i, g) in enumerate(self.visible_games)
                            if str(g.get("appid")) == focus_app_str
                        ),
                        -1,
                    )
                if idx >= 0:
                    self.selected_game_index = idx
                    self.focused_app_id = self.visible_games[idx].get("appid")
                    self.focused_platform = self.visible_games[idx].get("platform")
                else:
                    self.selected_game_index = 0
                    if self.visible_games:
                        self.focused_app_id = self.visible_games[0].get("appid")
                        self.focused_platform = self.visible_games[0].get("platform")
                    self._focus_lock_once = True
            else:
                if self.selected_game_index >= len(self.visible_games):
                    self.selected_game_index = 0
                if self.visible_games and (
                    not hasattr(self, "focused_app_id") or self.focused_app_id is None
                ):
                    g0 = self.visible_games[self.selected_game_index]
                    self.focused_app_id = g0["appid"]
                    self.focused_platform = g0["platform"]
        visible_games = self.visible_games
        self.update_button_styles()
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.clearFocus()
                widget.deleteLater()
            del item
        old_layout = self.card_container.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)
        if self.is_grid_mode:
            self.card_layout = QGridLayout()
            self.card_layout.setSpacing(self.theme_manager.scale_px(12))
        else:
            self.card_layout = QHBoxLayout()
            self.card_layout.setSpacing(self.theme_manager.scale_px(20))
        self.card_container.setLayout(self.card_layout)
        if not visible_games:
            empty_path = self.theme_manager.get(
                "empty_game", "theme/default/empty_game.png"
            )
            empty_card = QLabel()
            empty_card.setPixmap(
                QPixmap(empty_path).scaled(
                    self.theme_manager.scale_px(500),
                    self.theme_manager.scale_px(500),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            self.card_layout.addWidget(empty_card)
            self._start_fade_in()
            return
        for game in visible_games:
            card = QLabel()
            focused = hasattr(self, "_focus_area") and self._focus_area == "card"
            app_id = game["appid"]
            platform = game["platform"]
            is_selected = (
                focused
                and self.focused_app_id == app_id
                and (self.focused_platform == platform)
            )
            thumb_path = game["thumbnail"]
            abs_path = os.path.abspath(thumb_path)
            if self.is_grid_mode:
                scaled_w = self.theme_manager.scale_px(200)
                scaled_h = self.theme_manager.scale_px(200)
            else:
                scaled_w = self.theme_manager.scale_px(500 if is_selected else 400)
                scaled_h = self.theme_manager.scale_px(500 if is_selected else 400)
            cache_key = f"{abs_path}|{scaled_w}x{scaled_h}"
            if cache_key in self.pixmap_cache:
                pixmap = self.pixmap_cache.pop(cache_key)
                self.pixmap_cache[cache_key] = pixmap
            else:
                pixmap = QPixmap(abs_path)
                if pixmap.isNull():
                    fallback = self.theme_manager.get(
                        "icons.no_img", "theme/default/no_img.png"
                    )
                    pixmap = QPixmap(fallback)
                pixmap = pixmap.scaled(
                    scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.pixmap_cache[cache_key] = pixmap
                if len(self.pixmap_cache) > self.max_cache_size:
                    self.pixmap_cache.popitem(last=False)
            card.setPixmap(pixmap)
            card.setFixedSize(pixmap.size())
            card.setStyleSheet(self.get_card_style(is_selected))
            card.setProperty("appid", app_id)
            card.setProperty("platform", platform)
            card.mousePressEvent = lambda event, c=card: self.set_clicked_card(event, c)
            if self.is_grid_mode:
                idx = self.card_layout.count()
                row = idx // 12
                col = idx % 12
                self.card_layout.addWidget(card, row, col)
            else:
                self.card_layout.addWidget(card)
        self.update_info_label(visible_games)
        QTimer.singleShot(0, self.ensure_card_visible)
        self._start_fade_in()
        self._pending_action = None
        self._pending_focus_app = None
        self._fade_state = "FadingIn"

    def _build_cards_ui(self, visible_games):
        """현재 표시 모델을 카드 또는 그리드 위젯으로 만든다.
        기존 위젯은 deleteLater로 이벤트 처리 후 해제한다. 이미지 캐시 키에는 경로와
        축소 크기를 함께 넣어 같은 이미지의 선택/비선택 크기를 구분한다.
        """
        if hasattr(self, "update_button_styles"):
            self.update_button_styles()
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.clearFocus()
                w.deleteLater()
            del item
        old_layout = self.card_container.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)
        if self.is_grid_mode:
            self.card_layout = QGridLayout()
            self.card_layout.setSpacing(self.theme_manager.scale_px(12))
        else:
            self.card_layout = QHBoxLayout()
            self.card_layout.setSpacing(self.theme_manager.scale_px(20))
        self.card_container.setLayout(self.card_layout)
        if not visible_games:
            empty_path = self.theme_manager.get(
                "empty_game", "theme/default/empty_game.png"
            )
            empty_card = QLabel()
            empty_card.setPixmap(
                QPixmap(empty_path).scaled(
                    self.theme_manager.scale_px(500),
                    self.theme_manager.scale_px(500),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            self.card_layout.addWidget(empty_card)
            if hasattr(self, "update_info_label"):
                self.update_info_label([])
            return
        for game in visible_games:
            card = QLabel()
            focused = hasattr(self, "_focus_area") and self._focus_area == "card"
            app_id = game["appid"]
            platform = game["platform"]
            is_selected = (
                focused
                and self.focused_app_id == app_id
                and (self.focused_platform == platform)
            )
            thumb_path = game["thumbnail"]
            abs_path = os.path.abspath(thumb_path)
            if self.is_grid_mode:
                scaled_w = self.theme_manager.scale_px(200)
                scaled_h = self.theme_manager.scale_px(200)
            else:
                scaled_w = self.theme_manager.scale_px(500 if is_selected else 400)
                scaled_h = self.theme_manager.scale_px(500 if is_selected else 400)
            cache_key = f"{abs_path}|{scaled_w}x{scaled_h}"
            if cache_key in self.pixmap_cache:
                pixmap = self.pixmap_cache.pop(cache_key)
                self.pixmap_cache[cache_key] = pixmap
            else:
                pixmap = QPixmap(abs_path)
                if pixmap.isNull():
                    fallback = self.theme_manager.get(
                        "icons.no_img", "theme/default/no_img.png"
                    )
                    pixmap = QPixmap(fallback)
                pixmap = pixmap.scaled(
                    scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.pixmap_cache[cache_key] = pixmap
                if len(self.pixmap_cache) > self.max_cache_size:
                    self.pixmap_cache.popitem(last=False)
            card.setPixmap(pixmap)
            card.setFixedSize(pixmap.size())
            if hasattr(self, "get_card_style"):
                card.setStyleSheet(self.get_card_style(is_selected))
            card.setProperty("appid", app_id)
            card.setProperty("platform", platform)
            if hasattr(self, "set_clicked_card"):
                card.mousePressEvent = lambda ev, c=card: self.set_clicked_card(ev, c)
            if self.is_grid_mode:
                idx = self.card_layout.count()
                row = idx // 12
                col = idx % 12
                self.card_layout.addWidget(card, row, col)
            else:
                self.card_layout.addWidget(card)
        if hasattr(self, "update_info_label"):
            self.update_info_label(visible_games)
        QTimer.singleShot(0, self.ensure_card_visible)

    def _start_fade_out(self):
        try:
            self.card_container.setEnabled(False)
        except Exception:
            pass
        curr = float(self._fade_eff.opacity()) if self._fade_eff else 1.0
        self._fade_anim.stop()
        self._fade_anim.setStartValue(curr)
        self._fade_anim.setEndValue(0.0)
        duration = int(self.FADE_OUT_MS * curr)
        self._fade_anim.setDuration(max(80, duration))
        self._fade_anim.start()

    def _start_fade_in(self):
        curr = float(self._fade_eff.opacity()) if self._fade_eff else 0.0
        self._fade_anim.stop()
        self._fade_anim.setStartValue(curr)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setDuration(self.FADE_IN_MS)
        self._fade_anim.start()

    def _on_fade_finished(self):
        """애니메이션 완료를 다음 렌더 상태로 연결하는 Qt 시그널 슬롯이다. 타이머와 함께 상태 전이를 읽는다."""
        if self._fade_eff and abs(self._fade_eff.opacity() - 1.0) < 0.001:
            try:
                self.card_container.setEnabled(True)
            except Exception:
                pass
            self._fade_state = "Idle"
        elif self._render_timer.isActive():
            self._fade_state = "WaitingDebounce"
        else:
            self._do_render_cards()

    def _recompute_visible_games_for_current_category(self):
        """전체 games에서 현재 카테고리에 해당하는 visible_games를 계산한다. 원본 목록과 화면 필터를 분리한다."""
        selected_cat = (
            self.categories[self.selected_category_index]
            if self.categories
            else "전체 게임"
        )
        if selected_cat == "전체 게임":
            no_play = [
                g for g in self.games if g.get("last_played") in [None, "", "없음"]
            ]
            has_play = [
                g for g in self.games if g.get("last_played") not in [None, "", "없음"]
            ]
            has_play.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = no_play + has_play
        elif selected_cat == "최근 실행":
            vg = [
                g for g in self.games if g.get("last_played") not in [None, "", "없음"]
            ]
            vg.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = vg
        else:
            games_in_cat = [
                g for g in self.games if selected_cat in g.get("categories", [])
            ]
            has_play = [
                g
                for g in games_in_cat
                if g.get("last_played") not in [None, "", "없음"]
            ]
            no_play = [
                g for g in games_in_cat if g.get("last_played") in [None, "", "없음"]
            ]
            has_play.sort(key=lambda g: g["last_played"], reverse=True)
            self.visible_games = has_play + no_play

    def _get_selected_card_widget(self):
        """현재 선택된(포커스된) 카드 위젯을 레이아웃에서 찾아 반환"""
        if not hasattr(self, "card_layout") or self.card_layout is None:
            return None
        target_app = str(getattr(self, "focused_app_id", ""))
        target_plat = str(getattr(self, "focused_platform", ""))
        for i in range(self.card_layout.count()):
            item = self.card_layout.itemAt(i)
            w = item.widget()
            if not w:
                continue
            app = str(w.property("appid"))
            plat = str(w.property("platform"))
            if app == target_app and plat == target_plat:
                return w
        return None

    def set_clicked_card(self, event, card):
        self._clicked_card = card
        if self.is_grid_mode:
            self._drag_start_y = event.globalPosition().y()
        else:
            self._drag_start_x = event.globalPosition().x()

    def get_card_style(self, selected):
        focus_cfg = self.theme_manager.get("focus.card", {})
        border_color = focus_cfg.get("border_color", "orange")
        border_width = focus_cfg.get("border_width", self.theme_manager.scale_px(6))
        border_radius = focus_cfg.get("radius", self.theme_manager.scale_px(8))
        if selected:
            return f"border: {border_width}px solid {border_color};border-radius: {border_radius}px;background-color: rgba(0, 0, 0, 0);"
        else:
            return "border: none;background-color: rgba(0, 0, 0, 0);"

    def update_button_styles(self):
        if hasattr(self, "btn_profile"):
            self.btn_profile.setStyleSheet(
                "border: 4px solid orange; background: transparent;"
                if self._focus_area == "top"
                else "border: none; background: transparent;"
            )
        if hasattr(self, "btn_update"):
            self.btn_update.setStyleSheet(
                "border: 4px solid orange; background: transparent;"
                if self._focus_area == "bottom"
                else "border: none; background: transparent;"
            )

    def mouseMoveEvent(self, event):
        if self.is_grid_mode and hasattr(self, "_drag_start_y"):
            delta = self._drag_start_y - event.globalPosition().y()
            self.card_scroll.verticalScrollBar().setValue(
                self.card_scroll.verticalScrollBar().value() + delta
            )
            self._drag_start_y = event.globalPosition().y()
            self._click_candidate = None
        elif not self.is_grid_mode and hasattr(self, "_drag_start_x"):
            delta = self._drag_start_x - event.globalPosition().x()
            self.card_scroll.horizontalScrollBar().setValue(
                self.card_scroll.horizontalScrollBar().value() + delta
            )
            self._drag_start_x = event.globalPosition().x()
            self._click_candidate = None

    def mouseReleaseEvent(self, event):
        if self.is_grid_mode and hasattr(self, "_drag_start_y"):
            delta = abs(self._drag_start_y - event.globalPosition().y())
            del self._drag_start_y
        elif not self.is_grid_mode and hasattr(self, "_drag_start_x"):
            delta = abs(self._drag_start_x - event.globalPosition().x())
            del self._drag_start_x
        else:
            delta = 9999
        if delta < 10 and hasattr(self, "_clicked_card"):
            card = self._clicked_card
            self._clicked_card = None
            if card is not None:
                self.on_card_click(event, card)
        else:
            self._clicked_card = None

    def on_card_click(self, event, card):
        if card is None:
            return
        app_id = card.property("appid")
        platform = card.property("platform")
        is_same_card = (
            self.focused_app_id == app_id and self.focused_platform == platform
        )
        self.focused_app_id = app_id
        self.focused_platform = platform
        self.selected_game_index = next(
            (
                i
                for i in range(self.card_layout.count())
                if self.card_layout.itemAt(i).widget() == card
            ),
            0,
        )
        self._fast_hint = True
        self._pending_action = None
        self._pending_focus_app = None
        self.render_cards()
        if is_same_card:
            meta_path = os.path.join("l_libs", platform, str(app_id), "meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    from popup_loading_launcher import launch_popup_with_loading

                    if platform == "emul":
                        from rom_list_popup import RomListPopup

                        launch_popup_with_loading(
                            RomListPopup,
                            meta,
                            self.theme_manager,
                            app_id,
                            platform,
                            parent=self.main_widget,
                        )
                    else:
                        from game_detail_screen import GameDetailScreen

                        launch_popup_with_loading(
                            GameDetailScreen,
                            meta,
                            self.theme_manager,
                            app_id,
                            platform,
                            parent=self.main_widget,
                        )
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def ensure_card_visible(self):
        """선택된 카드가 스크롤 영역 안에 보이도록 보정"""
        try:
            target = self._get_selected_card_widget()
            if (
                not target
                or not hasattr(self, "card_scroll")
                or self.card_scroll is None
            ):
                return
            self.card_container.updateGeometry()
            self.card_container.repaint()
            self.card_scroll.ensureWidgetVisible(target, xmargin=20, ymargin=20)
            QTimer.singleShot(
                0, lambda: self.card_scroll.ensureWidgetVisible(target, 20, 20)
            )
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def ensure_tab_visible(self):
        tab_rect = self.tab_bar.tabRect(self.selected_category_index)
        self.tab_scroll.ensureVisible(tab_rect.x(), 0, tab_rect.width(), 0)

    def clear_card_focus(self):
        if self.card_scroll:
            self.card_scroll.clearFocus()
        self.clearFocus()

    def update_info_label(self, visible_games=None):
        """선택 게임의 메타데이터로 상단 정보를 갱신한다. 빈 목록도 처리해야 이전 게임 정보가 남지 않는다."""
        if visible_games is None:
            visible_games = self.games
        if not visible_games:
            self.info_icon_label.clear()
            self.info_text_label.setText("플랫폼 | 제목 | 최근 실행: -")
            return
        game = visible_games[self.selected_game_index]
        platform = game["platform"]
        title = game["title"]
        last_played = game["last_played"]
        platform_map = {
            "steam": "Steam",
            "epic": "Epic",
            "gog": "GOG",
            "stove": "STOVE",
            "user": "User",
            "emul": "emul",
        }
        mapped_key = platform_map.get(platform.lower(), "User")
        icon_abs_path = self.theme_manager.get(
            f"platform_icons.{mapped_key}", "theme/default/icons/unknown.png"
        )
        if os.path.exists(icon_abs_path):
            self.info_icon_label.setPixmap(QPixmap(icon_abs_path))
        else:
            self.info_icon_label.clear()
        self.info_text_label.setText(f"| {title} | 최근 실행: {last_played}")

    def _get_background_value(self, bg_config):
        if isinstance(bg_config, dict):
            if bg_config.get("type") == "color":
                return bg_config.get("value", "transparent")
            elif bg_config.get("type") == "image":
                image_path = self.theme_manager.get(
                    "bg." + bg_config.get("value", ""), ""
                )
                return f"url({image_path})"
        return "transparent"
