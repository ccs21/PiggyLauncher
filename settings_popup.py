"""설정 메뉴 탐색과 각 탭 생성·수명 관리를 담당한다.
탭 내용은 별도 모듈에 위임한다. 키보드/패드 포커스와 화면 교체 시 상태를 함께 읽는다.
"""

import logging
from popup_windows import BasePopup
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLineEdit,
    QMessageBox,
    QDialog,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
)
from PySide6.QtGui import QIcon, QFont
import os, json
import socket
from popup_utils import ConfirmDialog
from tab_profile import build_profile_tab
from tab_launcher import build_launcher_tab
from tab_info import build_info_tab
from popup_alert import CustomAlertDialog

CATEGORY_PATH = os.path.join("configs", "user_categories.json")


def get_launcher_temp_dir():
    """
    런쳐 실행 폴더 기준으로 전용 임시폴더(launcher_temp)를 만들어 경로를 반환합니다.
    """
    base_dir = os.getcwd()
    temp_dir = os.path.join(base_dir, "launcher_temp")
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception:
        return base_dir
    return temp_dir


def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False


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


class SettingsPopup(BasePopup):
    def init_ui(self):
        super().init_ui()
        self.current_tab_index = 0
        self.category_limit = 30
        top_layout = QHBoxLayout()
        tabs_theme = self.theme_manager.get("tabs", {})
        sel = tabs_theme.get("selected", {})
        unsel = tabs_theme.get("unselected", {})
        self.sel_bg = sel.get("background", {}).get("value", "#000000")
        self.sel_text = sel.get("text_color", "#FFFFFF")
        self.sel_border = sel.get("border_color", "#FFFFFF")
        self.sel_border_w = sel.get("border_width", 2)
        self.unsel_bg = unsel.get("background", {}).get("value", "#636363")
        self.unsel_text = unsel.get("text_color", "#FFFFFF")
        self.unsel_border = unsel.get("border_color", "#FFFFFF")
        self.unsel_border_w = unsel.get("border_width", 2)
        self.menu_buttons = []
        tab_names = [
            "프로필",
            "게임 관리",
            "카테고리 관리",
            "런쳐 설정",
            "프로그램 정보",
        ]
        for i, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setFont(self._get_font("팝업버튼", self.theme_manager.scale_px(22)))
            btn.setFixedSize(
                self.theme_manager.scale_px(200), self.theme_manager.scale_px(60)
            )
            btn.setStyleSheet(
                f"\n                background-color: {self.unsel_bg};\n                color: {self.unsel_text};\n                border: {self.unsel_border_w}px solid {self.unsel_border};\n                "
            )
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self.switch_tab(idx))
            self.menu_buttons.append(btn)
            top_layout.addWidget(btn)
        top_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.close_button = QPushButton(self)
        self.close_button.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        self.close_button.setStyleSheet("background: transparent; border: none;")
        icon_path = self.theme_manager.get("icons.close", "icons/close.png")
        self.close_button.setIcon(QIcon(icon_path))
        self.close_button.setIconSize(self.close_button.size())
        self.close_button.clicked.connect(self.close)
        top_layout.addWidget(self.close_button)
        top_layout.addSpacing(self.theme_manager.scale_px(20))
        self.tab_stack = QStackedWidget()
        for name in tab_names:
            if name == "프로필":
                tab = build_profile_tab(self.theme_manager)
                self.category_limit = 30
                self.tab_profile = tab
            elif name == "카테고리 관리":
                tab = self.build_category_tab()
            elif name == "게임 관리":
                tab = QWidget()
                layout = QVBoxLayout(tab)
                layout.setAlignment(Qt.AlignCenter)
                layout.setSpacing(self.theme_manager.scale_px(40))
                for key in [
                    "game_auto_register",
                    "game_self_register",
                    "edit_metadata",
                ]:
                    b = QPushButton()
                    b.setIcon(QIcon(self.theme_manager.get(f"icons.{key}", "")))
                    b.setIconSize(
                        QSize(
                            self.theme_manager.scale_px(900),
                            self.theme_manager.scale_px(200),
                        )
                    )
                    b.setFixedSize(
                        self.theme_manager.scale_px(920),
                        self.theme_manager.scale_px(220),
                    )
                    b.setStyleSheet("border: none;")
                    b.clicked.connect(lambda _, k=key: self.open_game_popup(k))
                    layout.addWidget(b)
            elif name == "런쳐 설정":
                tab = build_launcher_tab(self.theme_manager)
                self.tab_launcher = tab
            elif name == "프로그램 정보":
                tab = build_info_tab(self.theme_manager)
                self.tab_info = tab
            else:
                tab = QWidget()
                layout = QVBoxLayout(tab)
                (font, color) = self.get_font_and_color("팝업라벨", 22)
                label = QLabel(f"[{name}] 준비 중입니다.")
                label.setFont(font)
                label.setStyleSheet(f"color: {color};")
                layout.addWidget(label)
            self.tab_stack.addWidget(tab)
        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        bg_color = self.theme_manager.get("background.popup.value", "#FFFFFF")
        if "theme" in bg_color and "\\" in bg_color:
            bg_color = bg_color.split("\\")[-1]
        top_widget.setStyleSheet(f"background-color: {bg_color};")
        self.tab_stack.setStyleSheet(f"background-color: {bg_color};")
        self.layout().addWidget(top_widget)
        self.layout().addWidget(self.tab_stack)
        self.switch_tab(0)

    def delete_category_confirmed(self, name, widget):
        if name in self.categories:
            self.categories.remove(name)
            self.save_categories()
        widget.setParent(None)
        if hasattr(self.parent(), "central_content"):
            self.parent().central_content.refresh_tab_bar()

    def _get_font(self, key, default_size=22):
        f = self.theme_manager.get(f"fonts.{key}", {})
        font = QFont(f.get("family", "맑은 고딕"), f.get("size", default_size))
        font.setBold(f.get("bold", False))
        font.setItalic(f.get("italic", False))
        return font

    def get_font_and_color(self, key, default_size=22):
        f = self.theme_manager.get(f"fonts.{key}", {})
        font = QFont(f.get("family", "맑은 고딕"), f.get("size", default_size))
        font.setBold(f.get("bold", False))
        font.setItalic(f.get("italic", False))
        color = f.get("color", "#FFFFFF")
        return (font, color)

    def build_category_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_layout = QHBoxLayout()
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("새 카테고리 이름 입력")
        (font, color) = self.get_font_and_color("카테고리입력", 22)
        self.category_input.setFont(font)
        self.category_input.setStyleSheet(f"color: {color};")
        self.category_input.setMinimumHeight(self.theme_manager.scale_px(60))
        top_layout.addWidget(self.category_input)
        self.category_input.returnPressed.connect(self.add_category)
        add_btn = QPushButton("  ➕ 추가  ")
        (font, color) = self.get_font_and_color("팝업버튼", 20)
        add_btn.setFont(font)
        add_btn.setStyleSheet(f"background: transparent; color: {color};")
        add_btn.setFixedHeight(self.theme_manager.scale_px(60))
        add_btn.clicked.connect(self.add_category)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)
        self.category_area = DraggableScrollArea()
        self.category_area.setWidgetResizable(True)
        self.category_list_widget = QWidget()
        self.category_list_layout = QVBoxLayout(self.category_list_widget)
        self.category_area.setWidget(self.category_list_widget)
        layout.addWidget(self.category_area)
        self.load_categories()
        return tab

    def load_categories(self):
        self.category_list_layout.setSpacing(self.theme_manager.scale_px(10))
        for i in reversed(range(self.category_list_layout.count())):
            widget = self.category_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if os.path.exists(CATEGORY_PATH):
            with open(CATEGORY_PATH, "r", encoding="utf-8") as f:
                self.categories = json.load(f)
        else:
            self.categories = []
        for name in self.categories:
            self.add_category_item(name)

    def move_category(self, name, direction):
        if name not in self.categories:
            return
        index = self.categories.index(name)
        new_index = index + direction
        if 0 <= new_index < len(self.categories):
            (self.categories[index], self.categories[new_index]) = (
                self.categories[new_index],
                self.categories[index],
            )
            self.save_categories()
            self.load_categories()
            if hasattr(self.parent(), "central_content"):
                self.parent().central_content.refresh_tab_bar()

    def save_categories(self):
        with open(CATEGORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)

    def add_category(self):
        if not hasattr(self, "categories"):
            self.load_categories()
        name = self.category_input.text().strip()
        if not name:
            return
        if name in self.categories:
            QMessageBox.warning(self, "중복", "이미 존재하는 카테고리입니다.")
            return
        if len(self.categories) >= self.category_limit:
            msg = "카테고리는 최대 30개 까지 만들 수 있습니다."
            dlg = CustomAlertDialog("제한 초과", msg, self.theme_manager, self)
            dlg.exec()
            return
        self.categories.append(name)
        self.save_categories()
        self.add_category_item(name)
        self.category_input.clear()
        if hasattr(self.parent(), "central_content"):
            self.parent().central_content.refresh_tab_bar()
        QTimer.singleShot(50, lambda: self.switch_tab(self.current_tab_index))

    def add_category_item(self, name):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(5),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(5),
        )
        (font, color) = self.get_font_and_color("카테고리라벨", 26)
        label = QLabel(name)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        row_layout.addWidget(label)
        up_btn = QPushButton("⬆️")
        up_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        up_btn.setFont(self._get_font("팝업버튼", 20))
        up_btn.setStyleSheet("background: transparent;")
        up_btn.clicked.connect(lambda: self.move_category(name, direction=-1))
        row_layout.addWidget(up_btn)
        down_btn = QPushButton("⬇️")
        down_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        down_btn.setFont(self._get_font("팝업버튼", 20))
        down_btn.setStyleSheet("background: transparent;")
        down_btn.clicked.connect(lambda: self.move_category(name, direction=1))
        row_layout.addWidget(down_btn)
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        edit_btn.setFont(self._get_font("팝업버튼", 20))
        edit_btn.setStyleSheet("background: transparent;")
        edit_btn.clicked.connect(
            lambda: self.edit_category(name, row, label, edit_btn, delete_btn)
        )
        row_layout.addWidget(edit_btn)
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        delete_btn.setFont(self._get_font("팝업버튼", 20))
        delete_btn.setStyleSheet("background: transparent;")
        delete_btn.clicked.connect(lambda: self.delete_category(name, row))
        row_layout.addWidget(delete_btn)
        self.category_list_layout.addWidget(row)

    def edit_category(self, old_name, row_widget, label_widget, edit_btn, delete_btn):
        new_input = QLineEdit()
        new_input.setText(old_name)
        new_input.setFixedHeight(self.theme_manager.scale_px(30))
        (font, color) = self.get_font_and_color("카테고리입력", 22)
        new_input.setFont(font)
        new_input.setStyleSheet(f"color: {color};")
        confirm_btn = QPushButton("수정 완료")
        confirm_btn.setFixedSize(
            self.theme_manager.scale_px(160), self.theme_manager.scale_px(40)
        )
        (font, color) = self.get_font_and_color("팝업버튼", 18)
        confirm_btn.setFont(font)
        confirm_btn.setStyleSheet(f"color: {color}; background: transparent;")
        confirm_btn.clicked.connect(
            lambda: self.finish_edit_category(old_name, new_input.text(), row_widget)
        )
        row_layout = row_widget.layout()
        row_layout.removeWidget(label_widget)
        label_widget.hide()
        row_layout.insertWidget(0, new_input)
        row_layout.insertWidget(1, confirm_btn)
        edit_btn.setEnabled(False)
        delete_btn.setEnabled(False)
        new_input.returnPressed.connect(
            lambda: self.finish_edit_category(old_name, new_input.text(), row_widget)
        )

    def finish_edit_category(self, old_name, new_name, row_widget):
        new_name = new_name.strip()
        if not new_name:
            return
        if new_name != old_name and new_name in self.categories:
            QMessageBox.warning(self, "중복", "이미 존재하는 카테고리입니다.")
            return
        if new_name != old_name:
            index = self.categories.index(old_name)
            self.categories[index] = new_name
            self.save_categories()
        self.load_categories()
        if hasattr(self.parent(), "central_content"):
            self.parent().central_content.refresh_tab_bar()
        self.load_categories()
        layout = row_widget.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        label = QLabel(new_name)
        (font, color) = self.get_font_and_color("카테고리라벨", 26)
        label.setFont(font)
        label.setStyleSheet(f"color: {color};")
        layout.addWidget(label)
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        edit_btn.setFont(self._get_font("팝업버튼", 20))
        edit_btn.setStyleSheet("background: transparent;")
        edit_btn.clicked.connect(
            lambda: self.edit_category(
                new_name, row_widget, label, edit_btn, delete_btn
            )
        )
        layout.addWidget(edit_btn)
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(
            self.theme_manager.scale_px(60), self.theme_manager.scale_px(60)
        )
        delete_btn.setFont(self._get_font("팝업버튼", 20))
        delete_btn.setStyleSheet("background: transparent;")
        delete_btn.clicked.connect(lambda: self.delete_category(new_name, row_widget))
        layout.addWidget(delete_btn)
        if hasattr(self.parent(), "central_content"):
            self.parent().central_content.refresh_tab_bar()

    def delete_category(self, name, widget):
        dialog = ConfirmDialog(
            "삭제 확인", f"{name} 카테고리를 삭제할까요?", self.theme_manager, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.delete_category_confirmed(name, widget)
            widget.setParent(None)
            self.save_categories()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, QLineEdit):
                event.accept()
                return
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def open_game_popup(self, key):
        self.close()
        if key == "game_auto_register":
            if not is_internet_available():
                dialog = CustomAlertDialog(
                    "인터넷 연결 필요",
                    "자동 등록은 인터넷 연결이 필요합니다.\n인터넷에 연결된 상태에서 시도해 주세요.",
                    self.theme_manager,
                    self,
                )
                dialog.exec()
                return
            from auto_register_popup import AutoRegisterPopup

            popup = AutoRegisterPopup(self.parent())
            popup.exec()
        elif key == "game_self_register":
            from user_register_popup import GameRegisterEditPopup

            popup = GameRegisterEditPopup(
                parent=self.parent(), theme_manager=self.theme_manager, edit_mode=False
            )
            popup.exec()
        elif key == "edit_metadata":
            from emulator_register_popup import EmulatorRegisterPopup

            popup = EmulatorRegisterPopup(
                theme_manager=self.theme_manager, parent=self.parent()
            )
            popup.exec()

    def switch_tab(self, index):
        self.current_tab_index = index
        self.tab_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.setStyleSheet(
                    f"\n                    background-color: {self.sel_bg};\n                    color: {self.sel_text};\n                    border: {self.sel_border_w}px solid {self.sel_border};\n                    "
                )
                btn.setChecked(True)
            else:
                btn.setStyleSheet(
                    f"\n                    background-color: {self.unsel_bg};\n                    color: {self.unsel_text};\n                    border: {self.unsel_border_w}px solid {self.unsel_border};\n                    "
                )
                btn.setChecked(False)

    def closeEvent(self, event):
        try:
            self.tab_stack.deleteLater()
            self.menu_buttons.clear()
            if hasattr(self, "tab_profile") and hasattr(self.tab_profile, "cleanup"):
                self.tab_profile.cleanup()
            if hasattr(self, "tab_info") and hasattr(self.tab_info, "cleanup"):
                self.tab_info.cleanup()
            if hasattr(self, "tab_launcher") and hasattr(self.tab_launcher, "cleanup"):
                self.tab_launcher.cleanup()
            if hasattr(self, "category_list_layout"):
                for i in reversed(range(self.category_list_layout.count())):
                    item = self.category_list_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        event.accept()
