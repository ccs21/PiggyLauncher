"""실행기 경로와 기종별 대표 코어·ROM 폴더를 연결하는 설정 화면.
사용 가능한 실행기가 바뀌면 코어 목록도 다시 계산해야 한다. ROM별 예외 설정은 별도 편집 화면에서 다룬다.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QWidget,
    QLineEdit,
    QSizePolicy,
    QComboBox,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItem
import os
import json
from popup_alert import CustomAlertDialog
from popup_utils import ConfirmDialog, ProgressDialog
from core_installer import CoreInstaller, CoreDownloadWorker


class DraggableScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.pos() - self.start_pos
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.start_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.start_pos = None
        super().mouseReleaseEvent(event)


class EmulatorRegisterPopup(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("에뮬레이터 등록")
        self.setStyleSheet(
            f"background-color: {self.theme_manager.get('background.popup.value', '#555555')};"
        )
        self.setFixedSize(
            self.theme_manager.scale_px(1600), self.theme_manager.scale_px(900)
        )
        self.sa_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.sa_paths = {}
        self.systems_config = {}
        self.retroarch_path = ""
        emul_config_path = os.path.join("configs", "emul_config.json")
        if os.path.exists(emul_config_path):
            try:
                with open(emul_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sa_paths = data.get("executables", {})
                    self.systems_config = data.get("systems", {})
                    self.retroarch_path = self.sa_paths.get("RetroArch", "")
            except:
                pass
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(20),
        )
        layout.setSpacing(self.theme_manager.scale_px(20))
        top_layout = QHBoxLayout()
        top_layout.setSpacing(self.theme_manager.scale_px(20))
        self.left_scroll = DraggableScrollArea()
        self.left_content = QWidget()
        self.left_scroll.setWidget(self.left_content)
        self.left_layout = QVBoxLayout(self.left_content)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(self.theme_manager.scale_px(10))
        self.build_left_section()
        self.right_scroll = DraggableScrollArea()
        self.right_content = QWidget()
        self.right_scroll.setWidget(self.right_content)
        self.right_layout = QVBoxLayout(self.right_content)
        top_layout.addWidget(self.left_scroll, 5)
        top_layout.addWidget(self.right_scroll, 5)
        self.build_right_section()
        color = self.theme_manager.get("fonts.팝업라벨.color", "#FFFFFF")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        save_btn = QPushButton(" 저장 ")
        save_btn.setFont(self._get_font("팝업버튼"))
        save_btn.setFixedHeight(self.theme_manager.scale_px(60))
        save_btn.setStyleSheet(
            f"color: {color}; border: 2px solid {color}; border-radius: 8px;"
        )
        save_btn.clicked.connect(self.save_right_config_to_meta)
        cancel_btn = QPushButton(" 취소 ")
        cancel_btn.setFont(self._get_font("팝업버튼"))
        cancel_btn.setFixedHeight(self.theme_manager.scale_px(60))
        cancel_btn.setStyleSheet(
            f"color: {color}; border: 2px solid {color}; border-radius: 8px;"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addSpacing(self.theme_manager.scale_px(20))
        button_layout.addWidget(cancel_btn)
        layout.addLayout(top_layout)
        layout.addLayout(button_layout)

    def build_right_section(self):
        color = self.theme_manager.get("fonts.팝업라벨.color", "#FFFFFF")
        title = QLabel("코어 설정")
        title.setFont(self._get_font("팝업라벨"))
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(f"color: {color}; padding-bottom: 10px;")
        self.right_layout.addWidget(title)
        from ra_map_full import RA_MAP, SA_MAP, DISPLAY_NAME_MAP, SORTED_RA_KEYS

        font = self._get_font("팝업라벨")
        bg_color = self.theme_manager.get("background.popup.value", "#555555")
        border_color = self.theme_manager.get("fonts.팝업라벨.color", "#FFFFFF")
        for sys in SORTED_RA_KEYS:
            saved_core = ""
            saved_rom = ""
            meta_path = os.path.join("l_libs", "emul", sys, "meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        saved_core = meta.get("main_core", "")
                        saved_rom = meta.get("rom_folder", "")
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            if saved_core:
                if self.retroarch_path == "" and saved_core in (
                    RA_MAP.get(sys, []) or []
                ):
                    saved_core = ""
                if saved_core in (SA_MAP.get(sys, []) or []) and (
                    not (self.sa_paths.get(saved_core, "") or "").strip()
                ):
                    saved_core = ""
            group = QWidget()
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(self.theme_manager.scale_px(6))
            display_name = DISPLAY_NAME_MAP.get(sys, sys.upper())
            label = QLabel(display_name)
            label.setFont(font)
            label.setFixedWidth(self.theme_manager.scale_px(600))
            label.setStyleSheet(f"color: {color};")
            group_layout.addWidget(label)
            core_row = QWidget()
            core_layout = QHBoxLayout(core_row)
            core_layout.setContentsMargins(0, 0, 0, 0)
            core_layout.setSpacing(self.theme_manager.scale_px(10))
            core_box = QComboBox()
            core_box.setMinimumHeight(self.theme_manager.scale_px(50))
            core_box.setFont(font)
            core_box.setStyleSheet(
                f"\n                background-color: {bg_color};\n                color: {border_color};\n                border: 2px solid {border_color};\n                border-radius: 8px;\n                "
            )
            core_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            core_box.addItem("사용안함")
            model = core_box.model()
            for core in RA_MAP.get(sys, []):
                item = QStandardItem(f"RA: {core}")
                item.setEnabled(True)
                model.appendRow(item)
            for sa in SA_MAP.get(sys, []):
                item = QStandardItem(f"SA: {sa}")
                item.setEnabled(True)
                model.appendRow(item)
            if saved_core:
                for i in range(core_box.count()):
                    if core_box.itemText(i).endswith(saved_core):
                        core_box.setCurrentIndex(i)
                        break
            core_label = QLabel("코어 선택")
            core_label.setFont(font)
            core_label.setStyleSheet(f"color: {color};")
            initial_text = core_box.currentText().strip() or "사용안함"
            core_box.setProperty("prev_text", initial_text)
            core_box.currentTextChanged.connect(
                lambda new_text, s=sys, cb=core_box: self._on_system_core_selected(
                    s, cb, new_text
                )
            )
            core_layout.addWidget(core_label)
            core_layout.addWidget(core_box)
            group_layout.addWidget(core_row)
            rom_row = QWidget()
            rom_layout = QHBoxLayout(rom_row)
            rom_layout.setContentsMargins(0, 0, 0, 0)
            rom_layout.setSpacing(self.theme_manager.scale_px(10))
            rom_path = QLineEdit()
            rom_path.setReadOnly(True)
            rom_path.setFont(font)
            rom_path.setMinimumHeight(self.theme_manager.scale_px(50))
            rom_path.setStyleSheet(
                f"\n                background-color: {bg_color};\n                color: {border_color};\n                border: 2px solid {border_color};\n                border-radius: 8px;\n                "
            )
            rom_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if saved_rom:
                rom_path.setText(saved_rom)
            browse_btn = QPushButton("찾기")
            browse_btn.setFont(self._get_font("팝업버튼"))
            browse_btn.setStyleSheet(
                f"color: {border_color}; border: 2px solid {border_color}; border-radius: 8px;"
            )
            browse_btn.setFixedWidth(self.theme_manager.scale_px(100))
            browse_btn.setMinimumHeight(self.theme_manager.scale_px(50))
            browse_btn.clicked.connect(
                lambda _, s=sys, r=rom_path: self.select_rom_folder(s, r)
            )
            rom_label = QLabel("롬 폴더")
            rom_label.setFont(font)
            rom_label.setStyleSheet(f"color: {color};")
            rom_layout.addWidget(rom_label)
            rom_layout.addWidget(rom_path, 1)
            rom_layout.addWidget(browse_btn)
            group_layout.addWidget(rom_row)
            group_layout.addSpacing(self.theme_manager.scale_px(30))
            self.right_layout.addWidget(group)
        self.right_layout.addStretch()

    def select_rom_folder(self, system_key, target_lineedit):
        dir_path = QFileDialog.getExistingDirectory(self, "롬 폴더 선택", "")
        if dir_path:
            target_lineedit.setText(dir_path)

    def build_left_section(self):
        color = self.theme_manager.get("fonts.팝업라벨.color", "#FFFFFF")
        title = QLabel("에뮬레이터 설정")
        title.setFont(self._get_font("팝업라벨"))
        title.setStyleSheet(f"color: {color};")
        title.setAlignment(Qt.AlignLeft)
        self.left_layout.addWidget(title)
        SUPPORTED_SA_ORDERED = [
            ("RetroArch", "RetroArch"),
            ("PPSSPP", "PSP"),
            ("Duckstation", "PSX"),
            ("PCSX2", "PS2"),
            ("RPCS3", "PS3"),
            ("Dolphin", "GameCube/Wii"),
            ("Cemu", "GameCube/Wii"),
            ("MelonDS", "NDS"),
            ("Citra", "3DS"),
            ("Lime3DS", "3DS"),
            ("Azahar", "3DS"),
            ("Ryujinx", "NSW"),
            ("Citron", "NSW"),
            ("Yuzu", "NSW"),
            ("Eden", "NSW"),
            ("Xemu", "Xbox"),
            ("Xenia_canary", "X360"),
            ("Mednafen", "Saturn"),
            ("Redream", "Dreamcast"),
            ("Demul", "Dreamcast"),
            ("Flycast", "Dreamcast"),
            ("Vita3K", "PS Vita"),
        ]
        font = self._get_font("팝업라벨")
        for emul_name, _ in SUPPORTED_SA_ORDERED:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(self.theme_manager.scale_px(10))
            label = QLabel(emul_name)
            label.setFont(font)
            label.setFixedWidth(self.theme_manager.scale_px(160))
            label.setStyleSheet(f"color: {color};")
            lineedit = QLineEdit()
            lineedit.setReadOnly(True)
            bg_color = self.theme_manager.get("background.popup.value", "#555555")
            border_color = self.theme_manager.get("fonts.팝업라벨.color", "#FFFFFF")
            lineedit.setStyleSheet(
                f"\n                background-color: {bg_color};\n                color: {border_color};\n                border: 2px solid {border_color};\n                border-radius: 8px;\n                "
            )
            lineedit.setMinimumHeight(self.theme_manager.scale_px(50))
            lineedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if emul_name in self.sa_paths:
                lineedit.setText(self.sa_paths[emul_name])
            browse_btn = QPushButton("찾기")
            browse_btn.setFixedWidth(self.theme_manager.scale_px(100))
            browse_btn.setMinimumHeight(self.theme_manager.scale_px(50))
            browse_btn.setFont(self._get_font("팝업버튼"))
            browse_btn.setStyleSheet(
                f"color: {color}; border: 2px solid {color}; border-radius: 8px;"
            )
            browse_btn.clicked.connect(
                lambda _, e=emul_name: self.select_emulator_path(e)
            )
            delete_btn = QPushButton("삭제")
            delete_btn.setFixedWidth(self.theme_manager.scale_px(100))
            delete_btn.setMinimumHeight(self.theme_manager.scale_px(50))
            delete_btn.setFont(self._get_font("팝업버튼"))
            delete_btn.setStyleSheet(
                f"color: {color}; border: 2px solid {color}; border-radius: 8px;"
            )
            delete_btn.clicked.connect(
                lambda _, e=emul_name: self.clear_emulator_path(e)
            )
            row_layout.addWidget(label)
            row_layout.addWidget(lineedit, 1)
            row_layout.addWidget(browse_btn)
            row_layout.addWidget(delete_btn)
            self.left_layout.addWidget(row)
            self.sa_widgets[emul_name] = {
                "lineedit": lineedit,
                "browse_btn": browse_btn,
                "delete_btn": delete_btn,
            }
        self.left_layout.addStretch()

    def select_emulator_path(self, emul_name):
        (file_path, _) = QFileDialog.getOpenFileName(
            self, "실행 파일 선택", "", "실행 파일 (*.exe)"
        )
        if file_path:
            self.sa_widgets[emul_name]["lineedit"].setText(file_path)
            self.save_left_config_and_refresh_right()

    def clear_emulator_path(self, emul_name):
        self.sa_widgets[emul_name]["lineedit"].clear()
        self.save_left_config_and_refresh_right()

    def _get_font(self, key, default_size=22):
        f = self.theme_manager.get(f"fonts.{key}", {})
        font = QFont(f.get("family", "맑은 고딕"), f.get("size", default_size))
        font.setBold(f.get("bold", False))
        font.setItalic(f.get("italic", False))
        return font

    def save_left_config_and_refresh_right(self):
        """실행기 경로를 저장한 뒤 사용 가능한 코어 선택지를 다시 만든다. 실행기 설정과 기종 설정의 의존 관계를 보여준다."""
        data = {"executables": {}}
        for name, widget in self.sa_widgets.items():
            path = widget["lineedit"].text().strip()
            if path:
                data["executables"][name] = path
        try:
            os.makedirs("configs", exist_ok=True)
            with open("configs/emul_config.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        try:
            with open("configs/emul_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.sa_paths = config.get("executables", {})
                self.retroarch_path = self.sa_paths.get("RetroArch", "")
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.clear_right_layout()
        self.build_right_section()

    def clear_right_layout(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def save_right_config_to_meta(self):
        """기종별 대표 코어·ROM 폴더를 카드 메타데이터로 저장한다. 기종별 디렉터리형 ROM 처리는 일반 확장자 처리와 분기된다."""
        from ra_map_full import DISPLAY_NAME_MAP
        import re

        success_count = 0
        sa_exec_path = {}
        try:
            with open("configs/emul_config.json", "r", encoding="utf-8") as f:
                emul_config = json.load(f)
                sa_exec_path = emul_config.get("executables", {})
        except:
            pass
        for i in range(self.right_layout.count()):
            item = self.right_layout.itemAt(i)
            widget = item.widget()
            if not isinstance(widget, QWidget):
                continue
            children = widget.findChildren(QWidget)
            sys_key = None
            core_box = None
            rom_lineedit = None
            for child in children:
                if isinstance(child, QLabel) and (not sys_key):
                    text = child.text()
                    for k, v in DISPLAY_NAME_MAP.items():
                        if v == text:
                            sys_key = k
                            break
                elif isinstance(child, QComboBox) and (not core_box):
                    core_box = child
                elif isinstance(child, QLineEdit) and (not rom_lineedit):
                    rom_lineedit = child
            if not sys_key or not core_box or (not rom_lineedit):
                continue
            selected_core = core_box.currentText().strip()
            rom_path = rom_lineedit.text().strip()
            meta_path = os.path.join("l_libs", "emul", sys_key, "meta.json")
            romlist_path = os.path.join("l_libs", "emul", sys_key, "rom_list.json")
            if selected_core == "사용안함" or not rom_path:
                for path in [meta_path, romlist_path]:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                continue
            core_match = re.match("^(?:RA|SA):\\s*(.+)$", selected_core)
            main_core = core_match.group(1) if core_match else selected_core
            thumb_path = self.theme_manager.get(f"emul.{sys_key}", "").replace(
                "\\", "/"
            )
            meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            meta.setdefault("appid", sys_key)
            meta.setdefault("platform", "emul")
            meta.setdefault("title", DISPLAY_NAME_MAP.get(sys_key, sys_key.upper()))
            meta.setdefault("thumbnail", thumb_path)
            meta.setdefault(
                "main_core_type", "RA" if selected_core.startswith("RA:") else "SA"
            )
            meta.setdefault("main_core", main_core)
            meta.setdefault("rom_folder", rom_path)
            meta.setdefault("last_played", "없음")
            meta.setdefault("categories", [])
            meta["title"] = DISPLAY_NAME_MAP.get(sys_key, sys_key.upper())
            meta["thumbnail"] = thumb_path
            meta["main_core_type"] = "RA" if selected_core.startswith("RA:") else "SA"
            meta["main_core"] = main_core
            meta["rom_folder"] = rom_path
            try:
                folder = os.path.join("l_libs", "emul", sys_key)
                os.makedirs(folder, exist_ok=True)
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=4, ensure_ascii=False)
            except Exception:
                continue
            existing = {}
            if os.path.exists(romlist_path):
                try:
                    with open(romlist_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                        for r in loaded:
                            if "filename" in r:
                                existing[r["filename"]] = r
                except:
                    pass
            new_list = []
            try:
                from ra_map_full import ROM_EXTENSIONS_MAP

                valid_exts = ROM_EXTENSIONS_MAP.get(sys_key, [])
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            loaded_meta = json.load(f)
                            custom_exts = loaded_meta.get("ext_name", [])
                            if isinstance(custom_exts, list):
                                filtered_exts = [
                                    e.lower()
                                    for e in custom_exts
                                    if isinstance(e, str) and e.startswith(".")
                                ]
                                if filtered_exts:
                                    valid_exts = list(set(valid_exts + filtered_exts))
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
                current_files = set()
                if sys_key == "playstation_vita":
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
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
                    rom_folder_path = os.path.abspath(rom_path)
                    for folder_name in os.listdir(rom_folder_path):
                        folder_path = os.path.join(rom_folder_path, folder_name)
                        if os.path.isdir(folder_path):
                            current_files.add(folder_name)
                elif sys_key == "playstation3":
                    rom_folder_path = os.path.abspath(rom_path)
                    rpcs3_path = sa_exec_path.get("RPCS3", "")
                    hdd_folder_path = ""
                    if rpcs3_path:
                        rpcs3_dir = os.path.dirname(os.path.abspath(rpcs3_path))
                        hdd_folder_path = os.path.join(rpcs3_dir, "dev_hdd0", "game")

                    def scan_for_eboot(base_path, nested=True):
                        results = []
                        for folder_name in os.listdir(base_path):
                            full_path = os.path.join(base_path, folder_name)
                            if not os.path.isdir(full_path):
                                continue
                            if nested:
                                eboot_path = os.path.join(
                                    full_path, "PS3_GAME", "USRDIR", "EBOOT.BIN"
                                )
                            else:
                                eboot_path = os.path.join(
                                    full_path, "USRDIR", "EBOOT.BIN"
                                )
                            if os.path.isfile(eboot_path):
                                results.append(folder_name)
                        return results

                    current_files.update(scan_for_eboot(rom_folder_path, nested=True))
                    if hdd_folder_path and os.path.isdir(hdd_folder_path):
                        current_files.update(
                            scan_for_eboot(hdd_folder_path, nested=False)
                        )
                else:
                    for root, _, files in os.walk(rom_path):
                        for fname in files:
                            if valid_exts and (
                                not any(
                                    (fname.lower().endswith(ext) for ext in valid_exts)
                                )
                            ):
                                continue
                            rel_path = os.path.relpath(
                                os.path.join(root, fname), rom_path
                            )
                            current_files.add(rel_path)
                existing = {}
                if os.path.exists(romlist_path):
                    try:
                        with open(romlist_path, "r", encoding="utf-8") as f:
                            loaded = json.load(f)
                            for r in loaded:
                                if "filename" in r:
                                    existing[r["filename"]] = r
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
                for filename in current_files:
                    if filename in existing:
                        new_list.append(existing[filename])
                    elif sys_key == "playstation_vita":
                        title_image = ""
                        screenshot = ""
                        title_id = filename
                        folder_path = os.path.join(rom_folder_path, title_id)
                        title_image_path = os.path.join(
                            folder_path, "sce_sys", "icon0.png"
                        )
                        screenshot_path = os.path.join(
                            folder_path, "sce_sys", "pic0.png"
                        )
                        if os.path.exists(title_image_path):
                            title_dir = os.path.join("l_libs", "emul", sys_key, "title")
                            os.makedirs(title_dir, exist_ok=True)
                            target = os.path.join(title_dir, f"{title_id}_title.png")
                            shutil.copyfile(title_image_path, target)
                            title_image = f"title/{title_id}_title.png"
                        if os.path.exists(screenshot_path):
                            screenshot_dir = os.path.join(
                                "l_libs", "emul", sys_key, "s_shot"
                            )
                            os.makedirs(screenshot_dir, exist_ok=True)
                            target = os.path.join(
                                screenshot_dir, f"{title_id}_screenshot.png"
                            )
                            shutil.copyfile(screenshot_path, target)
                            screenshot = f"s_shot/{title_id}_screenshot.png"
                        new_list.append(
                            {
                                "title": title_map.get(title_id, ""),
                                "filename": title_id,
                                "title_image": title_image,
                                "screenshots": [screenshot] if screenshot else [],
                                "publisher": "",
                                "release_date": "",
                                "description": "",
                                "last_played": "없음",
                                "favorites": "False",
                                "core": "",
                                "core_type": "",
                                "emulator_path": "",
                            }
                        )
                    elif sys_key == "playstation3":
                        rom_dir = ""
                        if rpcs3_path:
                            rom_dir = os.path.join(rom_folder_path, filename)
                        new_list.append(
                            {
                                "title": "",
                                "filename": filename,
                                "rom_dir": rom_dir.replace("/", "\\"),
                                "title_image": "",
                                "screenshots": [],
                                "publisher": "",
                                "release_date": "",
                                "description": "",
                                "last_played": "없음",
                                "favorites": "False",
                                "core": "",
                                "core_type": "",
                                "emulator_path": "",
                            }
                        )
                    else:
                        new_list.append(
                            {
                                "title": "",
                                "filename": filename,
                                "title_image": "",
                                "screenshots": [],
                                "publisher": "",
                                "release_date": "",
                                "description": "",
                                "last_played": "없음",
                                "favorites": "False",
                                "core": "",
                                "core_type": "",
                                "emulator_path": "",
                            }
                        )
                with open(romlist_path, "w", encoding="utf-8") as f:
                    json.dump(new_list, f, indent=4, ensure_ascii=False)
                success_count += 1
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        for w in QApplication.topLevelWidgets():
            if w.isVisible() and hasattr(w, "central_content"):

                def delayed_refresh(target_window):
                    target_window.central_content.load_registered_games()
                    target_window.central_content.on_category_changed(0)
                    target_window.central_content.render_cards()

                QTimer.singleShot(500, lambda w=w: delayed_refresh(w))
        self.accept()

    def cleanup(self):
        if hasattr(self, "left_layout"):
            while self.left_layout.count():
                item = self.left_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.hide()
        if hasattr(self, "right_layout"):
            while self.right_layout.count():
                item = self.right_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.hide()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def reject(self):
        self.cleanup()
        self.done(QDialog.Rejected)

    def _on_system_core_selected(self, system_key, combo, new_text):
        """코어 선택을 검증하고 필요한 다운로드를 요청한다. 되돌리기 중에는 가드를 세워 선택 변경 신호의 재진입을 막는다."""
        if getattr(self, "_core_select_guard", False):
            return
        prev_text = combo.property("prev_text") or "사용안함"
        text = (new_text or "").strip()
        if text == "":
            return

        def revert():
            self._core_select_guard = True
            try:
                combo.setCurrentText(prev_text)
            finally:
                self._core_select_guard = False

        if text == "사용안함":
            combo.setProperty("prev_text", "사용안함")
            return
        core_type = (
            "RA" if text.startswith("RA:") else "SA" if text.startswith("SA:") else ""
        )
        core_name = text.split(":", 1)[1].strip() if ":" in text else text
        try:
            with open(
                os.path.join("configs", "emul_config.json"), "r", encoding="utf-8"
            ) as f:
                executables = (json.load(f) or {}).get("executables", {})
        except Exception:
            executables = {}
        if core_type == "RA":
            ra_info = CoreInstaller.ensure_retroarch_path()
            if not ra_info or not (executables.get("RetroArch", "") or "").strip():
                CustomAlertDialog(
                    "경고",
                    "RetroArch 경로가 설정되지 않았습니다.",
                    self.theme_manager,
                    self,
                ).exec()
                revert()
                return
            if not CoreInstaller.is_installed(ra_info.retroarch_dir, core_name):
                dlg = ConfirmDialog(
                    "코어 설치",
                    f"선택한 코어('{core_name}')가 설치되어 있지 않습니다.\n확인을 누르면 자동으로 설치합니다.",
                    self.theme_manager,
                    self,
                )
                if dlg.exec() != QDialog.Accepted:
                    revert()
                    return
                prog = ProgressDialog(
                    "코어 설치",
                    f"'{core_name}' 설치를 준비 중…",
                    self.theme_manager,
                    self,
                )
                worker = CoreDownloadWorker(core_name, ra_info.retroarch_dir, self)
                prog.connect_worker(worker)
                worker.start()
                prog.exec()
                if not CoreInstaller.is_installed(ra_info.retroarch_dir, core_name):
                    CustomAlertDialog(
                        "오류", "코어 설치에 실패했습니다.", self.theme_manager, self
                    ).exec()
                    revert()
                    return
            combo.setProperty("prev_text", text)
            return
        elif core_type == "SA":
            if not (executables.get(core_name, "") or "").strip():
                CustomAlertDialog(
                    "경고",
                    f"'{core_name}' 경로가 설정되어 있지 않습니다.",
                    self.theme_manager,
                    self,
                ).exec()
                revert()
                return
            combo.setProperty("prev_text", text)
            return
        revert()
