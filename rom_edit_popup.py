"""개별 ROM의 제목·이미지·설명·실행 예외를 편집하는 화면.
입력 데이터는 복사해서 편집하고, 저장 시 Classic JSON 목록의 해당 항목을 갱신한다.
"""

import logging
import os
import json
import shutil
import requests
import xml.etree.ElementTree as ET
import re
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QMessageBox,
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
        meta_path = os.path.join("l_libs", "emul", self.app_id, "meta.json")
        meta = {}
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
        core_val = rom_latest.get("core")
        core_type_val = rom_latest.get("core_type")
        emul_path_val = rom_latest.get("emulator_path")
        if not core_val:
            core_val = meta.get("main_core", "")
        if not core_type_val:
            core_type_val = meta.get("main_core_type", "")
        if not core_val or not core_type_val:
            self.target_core = ""
        else:
            self.target_core = f"{core_type_val}:{core_val}"
        if not emul_path_val and core_val and core_type_val:
            if core_type_val == "RA":
                emul_path_val = executables.get("RetroArch", "")
            elif core_type_val == "SA":
                emul_path_val = executables.get(core_val, "")
        self.emul_path_val = emul_path_val or ""
        super().__init__(parent)
        self.setWindowTitle("롬 정보 수정")
        self.setFixedSize(
            self.theme_manager.scale_px(800), self.theme_manager.scale_px(1000)
        )
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_ui(self):
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#FFFFFF"
        )
        bg = QWidget(self)
        bg.setStyleSheet(f"background-color: {bg_color};")
        bg.setGeometry(0, 0, self.width(), self.height())
        self.top_section = QWidget(bg)
        self.top_section.setStyleSheet("background-color: transparent; border: none;")
        layout = QVBoxLayout(self.top_section)
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
                f"font-family: '{family}'; font-size: {size}px; font-weight: {weight}; color: {font_color};"
            )
            return lbl

        def apply_style(w):
            w.setStyleSheet(widget_style)
            return w

        layout.addWidget(make_label("타이틀"))
        self.title_edit = apply_style(QLineEdit(self.rom_data.get("title", "")))
        layout.addWidget(self.title_edit)
        layout.addWidget(make_label("코어"))
        font_conf = self.theme_manager.get("fonts.팝업라벨", {})
        family = font_conf.get("family", "맑은 고딕")
        font_color = font_conf.get("color", "#000000")
        size = font_conf.get("size", 22)
        weight = "bold" if font_conf.get("bold", False) else "normal"
        popup_bg = self.theme_manager.get("background.popup", {}).get(
            "value", "#ffffff"
        )
        self.core_combo = QComboBox()
        self.core_combo.setView(QListView())
        combo_style = f"\n            QComboBox {{\n                {widget_style}\n            }}\n            QComboBox QAbstractItemView {{\n                background-color: {popup_bg};\n                color: {font_color};\n                border: 1px solid #888;\n                selection-background-color: #d0eaff;\n            }}\n            QListView {{\n                font-family: '{family}';\n                font-size: {size}px;\n                font-weight: {weight};\n                background-color: {popup_bg};\n                color: {font_color};\n                border: 1px solid #888;\n                outline: 0;\n            }}\n        "
        self.core_combo.setStyleSheet(combo_style)
        self.populate_core_list()
        found = False
        if self.target_core:
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
        for i in range(self.core_combo.count()):
            if (
                self.core_combo.itemText(i).strip().lower()
                == self.target_core.strip().lower()
            ):
                self.core_combo.setCurrentIndex(i)
                break
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
        layout.addWidget(make_label("배치 실행"))
        h_bat = QHBoxLayout()
        self.bat_edit = apply_style(QLineEdit(self.rom_data.get("bat_path", "")))
        btn_bat = apply_style(QPushButton("찾아보기"))
        btn_bat_del = apply_style(QPushButton("삭제"))
        btn_bat.clicked.connect(self.browse_bat_file)
        btn_bat_del.clicked.connect(self.clear_bat_path)
        h_bat.addWidget(self.bat_edit)
        h_bat.addWidget(btn_bat)
        h_bat.addWidget(btn_bat_del)
        layout.addLayout(h_bat)
        layout.addWidget(make_label("타이틀 이미지"))
        h_title = QHBoxLayout()
        self.title_path_edit = apply_style(
            QLineEdit(self.rom_data.get("title_image", ""))
        )
        btn_title = apply_style(QPushButton("선택"))
        btn_title.clicked.connect(self.browse_title_image)
        h_title.addWidget(self.title_path_edit)
        h_title.addWidget(btn_title)
        layout.addLayout(h_title)
        layout.addWidget(make_label("스크린샷"))
        h_shot = QHBoxLayout()
        self.screenshot_edit = apply_style(
            QLineEdit(";".join(self.rom_data.get("screenshots", [])))
        )
        btn_shot = apply_style(QPushButton("선택"))
        btn_shot.clicked.connect(self.browse_screenshot)
        h_shot.addWidget(self.screenshot_edit)
        h_shot.addWidget(btn_shot)
        layout.addLayout(h_shot)
        layout.addWidget(make_label("개발/배급"))
        self.pub_edit = apply_style(QLineEdit(self.rom_data.get("publisher", "")))
        layout.addWidget(self.pub_edit)
        layout.addWidget(make_label("출시일"))
        self.date_edit = apply_style(QLineEdit(self.rom_data.get("release_date", "")))
        layout.addWidget(self.date_edit)
        layout.addWidget(make_label("설명"))
        self.desc_edit = apply_style(QTextEdit(self.rom_data.get("description", "")))
        layout.addWidget(self.desc_edit)
        h_bottom = QHBoxLayout()
        h_bottom.addStretch()
        self.scrap_btn = apply_style(QPushButton("타이틀 제목으로 스크랩"))
        self.scrap_btn.clicked.connect(self.scrap_single_game)
        h_bottom.addWidget(self.scrap_btn)
        btn_save = apply_style(QPushButton("저장"))
        btn_cancel = apply_style(QPushButton("취소"))
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.close)
        h_bottom.addWidget(btn_save)
        h_bottom.addWidget(btn_cancel)
        layout.addLayout(h_bottom)
        wrapper = QVBoxLayout(bg)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(self.top_section)
        bg.setLayout(wrapper)
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)

    def browse_bat_file(self):
        (path, _) = QFileDialog.getOpenFileName(
            self,
            "배치 및 실행 파일 선택",
            "",
            "실행 가능 파일 (*.bat *.cmd *.exe *.msi *.ps1);;모든 파일 (*.*)",
        )
        if path:
            self.bat_edit.setText(path)

    def clear_bat_path(self):
        self.bat_edit.clear()

    def scrap_single_game(self):
        from scraper_credentials import load_flags

        title = self.title_edit.text().strip()
        if not title:
            CustomAlertDialog(
                "경고", "타이틀명이 비어있습니다.", self.theme_manager, self
            ).exec()
            return
        flags = load_flags(os.path.join("configs", "api_keys.local.json"))
        devid = flags.get("devid", "")
        devpw = flags.get("devpassword", "")
        if not devid or not devpw:
            CustomAlertDialog(
                "경고", "dev_keys.dat가 올바르지 않습니다.", self.theme_manager, self
            ).exec()
            return
        from scraper_setting_popup import ScraperThread

        system_ids = ScraperThread.map_system_id(None, self.app_id)
        if not system_ids:
            CustomAlertDialog(
                "경고",
                f"{self.app_id}에 대한 시스템 ID를 찾을 수 없습니다.",
                self.theme_manager,
                self,
            ).exec()
            return
        if not isinstance(system_ids, list):
            system_ids = [system_ids]
        jeu = None
        for sid in system_ids:
            params = {
                "devid": devid,
                "devpassword": devpw,
                "softname": "PiggyLauncher",
                "output": "xml",
                "romnom": title,
                "systemeid": sid,
            }
            url = "https://api.screenscraper.fr/api2/jeuInfos.php"
            try:
                r = requests.get(url, params=params, timeout=10)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                jeu = root.find("jeu")
                if jeu is not None:
                    break
            except Exception:
                continue
        if not jeu:
            CustomAlertDialog(
                "경고", "스크랩 결과를 찾을 수 없습니다.", self.theme_manager, self
            ).exec()
            return

        def sanitize_filename(name):
            return re.sub('[\\\\/:*?"<>|;]', "_", name)

        region_code = "jp"
        lang_code = "ja"
        fallback_regions = ["jp", "us", "eu", "fr"]
        fallback_langs = ["ja", "en", "fr", "es"]
        title_text = None
        for code in [region_code] + fallback_regions:
            node = jeu.find(f"noms/nom[@region='{code}']")
            if node is not None and node.text:
                title_text = node.text.strip()
                break
        if not title_text:
            node = jeu.find("noms/nom")
            if node is not None and node.text:
                title_text = node.text.strip()
        safe_title = sanitize_filename(title_text or title)
        desc = ""
        for code in [lang_code] + fallback_langs:
            node = jeu.find(f"synopsis/synopsis[@langue='{code}']")
            if node is not None and node.text:
                desc = node.text.strip()
                break
        release_date = "정보 없음"
        for code in [region_code] + fallback_regions:
            node = jeu.find(f"dates/date[@region='{code}']")
            if node is not None and node.text:
                raw = node.text.strip()
                release_date = raw.replace("-", "년 ", 1).replace("-", "월 ", 1) + "일"
                break
        dev = jeu.findtext("developpeur", "").strip()
        pub = jeu.findtext("editeur", "").strip()
        publisher = f"{pub}/{dev}".strip("/") if pub or dev else "정보 없음"
        (title_url, shot_url) = ("", "")
        media_list = jeu.findall("medias/media")
        for media in media_list:
            if media.attrib.get("type") == "wheel" and media.text:
                title_url = media.text.strip()
                break
        if not title_url:
            for media in media_list:
                if media.attrib.get("type") == "marqueetitlesmall" and media.text:
                    title_url = media.text.strip()
                    break
        for code in [region_code] + fallback_regions:
            for media in media_list:
                if (
                    media.attrib.get("type") == "mixrbv2"
                    and media.attrib.get("region") == code
                    and media.text
                ):
                    shot_url = media.text.strip()
                    break
            if shot_url:
                break
        if not shot_url:
            for media in media_list:
                if media.attrib.get("type") == "ss" and media.text:
                    shot_url = media.text.strip()
                    break
        app_folder = os.path.join("l_libs", "emul", self.app_id)
        os.makedirs(os.path.join(app_folder, "title"), exist_ok=True)
        os.makedirs(os.path.join(app_folder, "s_shot"), exist_ok=True)

        def save_image(url, path):
            if url:
                try:
                    r = requests.get(url, timeout=10)
                    with open(path, "wb") as f:
                        f.write(r.content)
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

        title_path = f"title/{safe_title}_title.png"
        shot_path = f"s_shot/{safe_title}_screenshot.png"
        save_image(title_url, os.path.join(app_folder, title_path))
        save_image(shot_url, os.path.join(app_folder, shot_path))
        self.title_edit.setText(title_text)
        self.desc_edit.setPlainText(desc)
        self.pub_edit.setText(publisher)
        self.date_edit.setText(release_date)
        self.title_path_edit.setText(title_path)
        self.screenshot_edit.setText(shot_path)
        CustomAlertDialog(
            "완료", "스크랩 결과를 반영했습니다.", self.theme_manager, self
        ).exec()

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
        all_cores = sorted(list(set(all_cores)), key=str.lower)
        self.core_combo.clear()
        self.core_combo.addItems(all_cores)

    def browse_exe(self):
        (path, _) = QFileDialog.getOpenFileName(
            self, "에뮬레이터 실행파일 선택", "", "EXE (*.exe)"
        )
        if path:
            self.emul_edit.setText(path)

    def browse_title_image(self):
        (path, _) = QFileDialog.getOpenFileName(
            self, "타이틀 이미지 선택", "", "이미지 (*.png *.jpg *.jpeg)"
        )
        if path:
            self.title_path_edit.setText(path)

    def browse_screenshot(self):
        (paths, _) = QFileDialog.getOpenFileNames(
            self, "스크린샷 선택", "", "이미지 (*.png *.jpg *.jpeg)"
        )
        if paths:
            self.screenshot_edit.setText(";".join(paths))

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
            QMessageBox.warning(self, "경고", "rom_list.json을 찾을 수 없습니다.")
            return
        try:
            with open(rom_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            QMessageBox.warning(self, "경고", "rom_list.json 읽기 실패")
            return
        target = next(
            (r for r in data if r.get("filename") == self.rom_data.get("filename")),
            None,
        )
        if not target:
            QMessageBox.warning(self, "경고", "대상 롬을 찾을 수 없습니다.")
            return
        app_folder = os.path.join("l_libs", "emul", self.app_id)
        os.makedirs(os.path.join(app_folder, "title"), exist_ok=True)
        os.makedirs(os.path.join(app_folder, "s_shot"), exist_ok=True)

        def check_update(k, new_val):
            if target.get(k) != new_val:
                target[k] = new_val

        check_update("title", self.title_edit.text())
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
        check_update("bat_path", self.bat_edit.text())
        import re

        def sanitize_filename(name):
            return re.sub('[\\\\/:*?"<>|;]', "_", name)

        t_img = self.title_path_edit.text()
        if t_img:
            safe_title = sanitize_filename(self.title_edit.text().strip() or "untitled")
            if not t_img.startswith("title/"):
                ext = os.path.splitext(t_img)[1]
                filename = f"title/{safe_title}_title{ext}"
                shutil.copy(t_img, os.path.join(app_folder, filename))
            else:
                filename = t_img
            check_update("title_image", filename)
        screenshots = []
        safe_title = sanitize_filename(self.title_edit.text().strip() or "untitled")
        shot_index = 1
        for path in self.screenshot_edit.text().split(";"):
            if path and (not path.startswith("s_shot/")):
                ext = os.path.splitext(path)[1]
                dest = f"s_shot/{safe_title}_screenshot_{shot_index}{ext}"
                shutil.copy(path, os.path.join(app_folder, dest))
                screenshots.append(dest)
                shot_index += 1
            elif path:
                screenshots.append(path)
        check_update("screenshots", screenshots)
        check_update("publisher", self.pub_edit.text())
        check_update("release_date", self.date_edit.text())
        check_update("description", self.desc_edit.toPlainText())
        try:
            with open(rom_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except:
            QMessageBox.warning(self, "경고", "rom_list.json 저장 실패")
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
