"""ROM별 실행기·코어 예외 설정을 편집한다.
빈 값은 기종 대표 설정을 상속하는 의미다. 모듈의 RomEditPopup은 전체 정보 편집 화면과 다른 클래스다.
"""

import logging
import os
import json
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QApplication,
    QListView,
)
from PySide6.QtCore import Qt
from popup_windows import BasePopup
from ra_map_full import RA_MAP, SA_MAP
from popup_alert import CustomAlertDialog
from popup_utils import ConfirmDialog, ProgressDialog
from core_installer import CoreInstaller, CoreDownloadWorker


class RomEditPopup(BasePopup):
    def __init__(self, theme_manager, app_id, rom_data, parent=None):
        self.theme_manager = theme_manager
        self.app_id = app_id
        self.rom_data = rom_data.copy()
        self.original_core = rom_data.get("core", "")
        self.original_path = rom_data.get("emulator_path", "")
        meta = {}
        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        rom_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        rom_latest = {}
        if os.path.exists(rom_path):
            try:
                with open(rom_path, "r", encoding="utf-8") as f:
                    rom_list = json.load(f)
                    rom_latest = next(
                        (
                            r
                            for r in rom_list
                            if r.get("filename") == self.rom_data.get("filename")
                        ),
                        {},
                    )
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        emul_config_path = os.path.join("configs", "emul_config.json")
        executables = {}
        if os.path.exists(emul_config_path):
            try:
                with open(emul_config_path, "r", encoding="utf-8") as f:
                    conf = json.load(f)
                    executables = conf.get("executables", {})
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        core_val = rom_latest.get("core") or meta.get("main_core", "")
        core_type_val = rom_latest.get("core_type") or meta.get("main_core_type", "")
        self.target_core = (
            f"{core_type_val}:{core_val}" if core_val and core_type_val else ""
        )
        emul_path_val = rom_latest.get("emulator_path", "")
        if not emul_path_val and core_val and core_type_val:
            if core_type_val == "RA":
                emul_path_val = executables.get("RetroArch", "")
            elif core_type_val == "SA":
                emul_path_val = executables.get(core_val, "")
        self.emul_path_val = emul_path_val or ""
        super().__init__(parent)
        self.setWindowTitle("롬 실행 설정")
        self.setFixedSize(
            self.theme_manager.scale_px(800), self.theme_manager.scale_px(300)
        )
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_ui(self):
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#FFFFFF"
        )
        bg = QWidget(self)
        bg.setStyleSheet(f"background-color: {bg_color};")
        bg.setGeometry(0, 0, self.width(), self.height())
        layout = QVBoxLayout(bg)
        layout.setSpacing(self.theme_manager.scale_px(10))
        layout.setContentsMargins(
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(30),
        )
        font_conf = self.theme_manager.get("fonts.팝업라벨", {})
        family = font_conf.get("family", "맑은 고딕")
        font_color = font_conf.get("color", "#000000")
        size = font_conf.get("size", 22)
        weight = "bold" if font_conf.get("bold", False) else "normal"
        popup_bg = self.theme_manager.get("background.popup", {}).get(
            "value", "#ffffff"
        )
        widget_style = f"font-family: '{family}'; font-size: {size}px; font-weight: {weight}; color: {font_color}; border: 1px solid {font_color}; border-radius: 4px; padding: 4px;"

        def make_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-family: '{family}'; font-size: {size}px; font-weight: {weight}; color: {font_color}; border: none;"
            )
            return lbl

        def apply_style(w):
            w.setStyleSheet(widget_style)
            return w

        layout.addWidget(make_label("코어"))
        self.core_combo = QComboBox()
        self.core_combo.setView(QListView())
        combo_style = f"\n            QComboBox {{\n                {widget_style}\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: {popup_bg};\n                color: {font_color};\n                border: 1px solid #888;\n                selection-background-color: #d0eaff;\n            }}\n            QListView {{\n                font-family: '{family}';\n                font-size: {size}px;\n                font-weight: {weight};\n                background-color: {popup_bg};\n                color: {font_color};\n                border: 1px solid #888;\n                outline: 0;\n            }}\n        "
        self.core_combo.setStyleSheet(combo_style)
        self.populate_core_list()
        found = False
        for i in range(self.core_combo.count()):
            if (
                self.core_combo.itemText(i).strip().lower()
                == self.target_core.strip().lower()
            ):
                self.core_combo.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.core_combo.setCurrentIndex(-1)
            self.core_combo.setCurrentText("")
        initial_text = self.core_combo.currentText().strip() or ""
        self.core_combo.setProperty("prev_text", initial_text)
        self._core_change_guard = False
        self.core_combo.currentTextChanged.connect(self.on_core_changed)
        layout.addWidget(self.core_combo)
        layout.addWidget(make_label("에뮬레이터 실행 파일 경로"))
        h_emul = QHBoxLayout()
        self.emul_edit = apply_style(QLineEdit(self.emul_path_val))
        self.browse_btn = apply_style(QPushButton("찾기"))
        self.browse_btn.clicked.connect(self.browse_exe)
        h_emul.addWidget(self.emul_edit)
        h_emul.addWidget(self.browse_btn)
        layout.addLayout(h_emul)
        h_bottom = QHBoxLayout()
        h_bottom.addStretch()
        btn_save = apply_style(QPushButton("저장"))
        btn_cancel = apply_style(QPushButton("취소"))
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.close)
        h_bottom.addWidget(btn_save)
        h_bottom.addWidget(btn_cancel)
        layout.addLayout(h_bottom)
        bg.setLayout(layout)
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)

    def browse_exe(self):
        (path, _) = QFileDialog.getOpenFileName(
            self, "에뮬레이터 실행파일 선택", "", "EXE (*.exe)"
        )
        if path:
            self.emul_edit.setText(path)

    def populate_core_list(self):
        all_cores = []
        emul_config_path = os.path.join("configs", "emul_config.json")
        if os.path.exists(emul_config_path):
            try:
                with open(emul_config_path, "r", encoding="utf-8") as f:
                    json.load(f)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        ra_core_list = RA_MAP.get(self.app_id, [])
        for core in ra_core_list:
            all_cores.append(f"RA:{core}")
        sa_core_list = SA_MAP.get(self.app_id, [])
        for core in sa_core_list:
            all_cores.append(f"SA:{core}")
        self.core_combo.clear()
        self.core_combo.addItems(sorted(list(set(all_cores)), key=str.lower))

    def on_core_changed(self, text):
        if getattr(self, "_core_change_guard", False):
            return
        prev_text = self.core_combo.property("prev_text") or ""
        new_text = (text or "").strip()
        if new_text == "":
            return

        def revert():
            self._core_change_guard = True
            try:
                self.core_combo.setCurrentText(prev_text)
            finally:
                self._core_change_guard = False

        ctype = (
            "RA"
            if new_text.startswith("RA:")
            else "SA"
            if new_text.startswith("SA:")
            else ""
        )
        cname = new_text.split(":", 1)[1].strip() if ":" in new_text else new_text
        emul_config_path = os.path.join("configs", "emul_config.json")
        try:
            with open(emul_config_path, "r", encoding="utf-8") as f:
                executables = (json.load(f) or {}).get("executables", {})
        except Exception:
            executables = {}
        if ctype == "RA":
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
            if not CoreInstaller.is_installed(ra_info.retroarch_dir, cname):
                dlg = ConfirmDialog(
                    "코어 설치",
                    f"선택한 코어('{cname}')가 설치되어 있지 않습니다.\n확인을 누르면 자동으로 설치합니다.",
                    self.theme_manager,
                    self,
                )
                if dlg.exec() != QDialog.Accepted:
                    revert()
                    return
                prog = ProgressDialog(
                    "코어 설치", f"'{cname}' 설치를 준비 중…", self.theme_manager, self
                )
                worker = CoreDownloadWorker(cname, ra_info.retroarch_dir, self)
                prog.connect_worker(worker)
                worker.start()
                prog.exec()
                if not CoreInstaller.is_installed(ra_info.retroarch_dir, cname):
                    CustomAlertDialog(
                        "오류", "코어 설치에 실패했습니다.", self.theme_manager, self
                    ).exec()
                    revert()
                    return
            self.core_combo.setProperty("prev_text", new_text)
            was_ra = prev_text.startswith("RA:") if prev_text else False
            if not was_ra:
                self.emul_edit.setText("")
            return
        elif ctype == "SA":
            exe_path = (executables.get(cname, "") or "").strip()
            if not exe_path:
                CustomAlertDialog(
                    "경고",
                    f"'{cname}' 경로가 설정되어 있지 않습니다.",
                    self.theme_manager,
                    self,
                ).exec()
                revert()
                return
            self.core_combo.setProperty("prev_text", new_text)
            self.emul_edit.setText(exe_path)
            return
        revert()

    def save(self):
        from rom_list_popup import RomListPopup

        rom_path = os.path.join("l_libs", "emul", self.app_id, "rom_list.json")
        if not os.path.exists(rom_path):
            return
        try:
            with open(rom_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            return
        target = next(
            (r for r in data if r.get("filename") == self.rom_data.get("filename")),
            None,
        )
        if not target:
            return

        def check_update(k, new_val):
            if target.get(k) != new_val:
                target[k] = new_val

        import json as _json

        def _safe_load_json(_p, _default):
            try:
                with open(_p, "r", encoding="utf-8") as _f:
                    return _json.load(_f)
            except Exception:
                return _default

        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        meta = _safe_load_json(meta_path, {})
        main_core_type = (meta.get("main_core_type") or "").strip()
        main_core_name = (meta.get("main_core") or "").strip()
        emul_conf_path = os.path.join("configs", "emul_config.json")
        emul_conf = _safe_load_json(emul_conf_path, {})
        executables = emul_conf.get("executables", {})
        if (main_core_type or "").upper() == "RA":
            main_exe = (executables.get("RetroArch") or "").strip()
        elif (main_core_type or "").upper() == "SA":
            main_exe = (executables.get(main_core_name) or "").strip()
        else:
            main_exe = ""
        selected_core = self.core_combo.currentText()
        if ":" in selected_core:
            (core_type_in, core_name_in) = selected_core.split(":", 1)
        else:
            (core_type_in, core_name_in) = ("", selected_core)
        core_type_in = (core_type_in or "").strip()
        core_name_in = (core_name_in or "").strip()
        emu_path_in = (self.emul_edit.text() or "").strip()

        def _norm_core_key(_ctype, _cname):
            return f"{(_ctype or '').strip().lower()}:{(_cname or '').strip().lower()}"

        def _norm_path(_p):
            if not _p:
                return ""
            try:
                return os.path.normcase(os.path.normpath(_p.strip()))
            except Exception:
                return (_p or "").strip().lower()

        main_core_key = _norm_core_key(main_core_type, main_core_name)
        sel_core_key = _norm_core_key(core_type_in, core_name_in)
        if sel_core_key and sel_core_key == main_core_key:
            (final_core_type, final_core_name) = ("", "")
        else:
            (final_core_type, final_core_name) = (core_type_in, core_name_in)
        check_update("core", final_core_name)
        check_update("core_type", final_core_type)
        if emu_path_in == "":
            final_emu_path = ""
        elif _norm_path(emu_path_in) == _norm_path(main_exe):
            final_emu_path = ""
        else:
            final_emu_path = emu_path_in
        check_update("emulator_path", final_emu_path)
        try:
            with open(rom_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except:
            return
        rom_list = self.parent()
        if isinstance(rom_list, RomListPopup):
            rom_list.reopen_self(keep_state=True)
        else:
            for w in QApplication.topLevelWidgets():
                if isinstance(w, RomListPopup):
                    w.reopen_self(keep_state=True)
                    break
        self.close()
