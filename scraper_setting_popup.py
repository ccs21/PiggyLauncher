"""ScreenScraper 옵션 화면과 ROM 일괄 수집 작업.
옵션/키 준비 → 기종·ROM 순회 → 진행 신호 → 저장/완료 흐름을 읽는다. 개인 계정 암호는 공개본에서 디스크에 저장하지 않는다.
"""

import logging
import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QDialog,
    QProgressBar,
    QGridLayout,
)
from PySide6.QtCore import Qt, QThread, Signal
from popup_windows import BasePopup
from popup_alert import CustomAlertDialog
from scraper_credentials import load_flags, save_flags


class ScraperThread(QThread):
    # finished는 QThread가 run 반환 후 발생시킨다. 동일 이름을 다시 정의하거나
    # 직접 emit하면 UI가 작업 종료 전에 결과를 처리하거나 두 번 처리하게 된다.
    failed = Signal(str)
    progress = Signal(int, int, int, int, str)

    def __init__(self, config, selected_platforms):
        super().__init__()
        self.config = config
        self.selected_platforms = selected_platforms
        self.dev_keys = load_flags(os.path.join("configs", "api_keys.local.json"))

    def run(self):
        """선택 기종의 ROM 정보를 순차 수집하고 Classic JSON에 반영한다.
        개발자 키와 개인 계정은 서로 다른 인증 정보다. 키가 없으면 네트워크 호출 전에
        실패를 알린다. 진행은 시그널로만 전달하고 작업 스레드에서 위젯을 만지지 않는다.
        """
        if not self.dev_keys.get("devid") or not self.dev_keys.get("devpassword"):
            self.failed.emit("API 키가 비어 있습니다. wiki/API_SETUP.md를 확인하세요.")
            return
        try:
            import re

            def sanitize_filename(name):
                return re.sub('[\\\\/:*?"<>|;]', "_", name)

            region_map = {
                "일본": ("jp", "ja"),
                "미국": ("us", "en"),
                "유럽": ("eu", "en"),
                "프랑스": ("fr", "fr"),
            }
            fallback_regions = ["jp", "us", "eu", "fr"]
            fallback_langs = ["ja", "en", "fr", "es"]
            user_region = self.config.get("region", "일본")
            (region_code, lang_code) = region_map.get(user_region, ("jp", "ja"))
            for platform in self.selected_platforms:
                rom_list_path = os.path.join(
                    "l_libs", "emul", platform, "rom_list.json"
                )
                if not os.path.exists(rom_list_path):
                    continue
                with open(rom_list_path, "r", encoding="utf-8") as f:
                    roms = json.load(f)
                if self.config.get("scrap_type") == "누락된 항목만 스크랩":
                    target_roms = [r for r in roms if not r.get("title_image")]
                else:
                    target_roms = roms
                total = len(target_roms)
                success_count = 0
                fail_count = 0
                updated_roms = []
                for index, rom in enumerate(target_roms, start=1):
                    filename = rom.get("filename", "")
                    system_ids = self.map_system_id(platform)
                    if not isinstance(system_ids, list):
                        system_ids = [system_ids]
                    jeu = None
                    if platform == "playstation3":
                        try:
                            if " " in filename:
                                filename = filename.rsplit(" ", 1)[0]
                            else:
                                nps_url = "https://nopaystation.com/tsv/PS3_GAMES.tsv"
                                response = requests.get(nps_url, timeout=10)
                                response.encoding = "utf-8"
                                for line in response.text.splitlines():
                                    parts = line.strip().split("\t")
                                    if len(parts) >= 3 and parts[0].strip() == filename:
                                        filename = parts[2].strip()
                                        break
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                    if platform == "playstation_vita":
                        try:
                            nps_url = "https://nopaystation.com/tsv/PSV_GAMES.tsv"
                            response = requests.get(nps_url, timeout=10)
                            response.encoding = "utf-8"
                            for line in response.text.splitlines():
                                parts = line.strip().split("\t")
                                if len(parts) >= 3 and parts[0].strip() == filename:
                                    filename = parts[2].strip()
                                    break
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                    search_name = os.path.basename(filename)
                    for sid in system_ids:
                        params = {
                            "devid": self.dev_keys.get("devid", ""),
                            "devpassword": self.dev_keys.get("devpassword", ""),
                            "softname": "PiggyLauncher",
                            "output": "xml",
                            "romnom": search_name,
                            "systemeid": sid,
                        }
                        if self.config.get("id") and self.config.get("pw"):
                            params["ssid"] = self.config["id"]
                            params["sspassword"] = self.config["pw"]
                        url = "https://api.screenscraper.fr/api2/jeuInfos.php"
                        try:
                            response = requests.get(url, params=params, timeout=20)
                            if response.status_code != 200:
                                continue
                            root = ET.fromstring(response.content)
                            jeu = root.find("jeu")
                            if jeu is not None:
                                break
                        except Exception:
                            continue
                    if not jeu:
                        fail_count += 1
                        self.progress.emit(
                            index, total, success_count, fail_count, filename
                        )
                        continue
                    try:
                        title = None
                        for code in [region_code] + fallback_regions:
                            node = jeu.find(f"noms/nom[@region='{code}']")
                            if node is not None and node.text:
                                title = node.text.strip()
                                break
                        if not title:
                            node = jeu.find("noms/nom")
                            if node is not None and node.text:
                                title = node.text.strip()
                        title = title or rom.get("title", "")
                        safe_title = sanitize_filename(title)
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
                                release_date = (
                                    raw.replace("-", "년 ", 1).replace("-", "월 ", 1)
                                    + "일"
                                )
                                break
                        dev = jeu.findtext("developpeur", "").strip()
                        pub = jeu.findtext("editeur", "").strip()
                        publisher = (
                            f"{pub}/{dev}".strip("/") if pub or dev else "정보 없음"
                        )
                        title_url = ""
                        shot_url = ""
                        media_list = jeu.findall("medias/media")
                        for media in media_list:
                            if media.attrib.get("type") == "wheel" and media.text:
                                title_url = media.text.strip()
                                break
                        if not title_url:
                            for media in media_list:
                                if (
                                    media.attrib.get("type") == "marqueetitlesmall"
                                    and media.text
                                ):
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
                        img_dir = os.path.join("l_libs", "emul", platform)
                        os.makedirs(os.path.join(img_dir, "title"), exist_ok=True)
                        os.makedirs(os.path.join(img_dir, "s_shot"), exist_ok=True)

                        def save_image(url, path):
                            """응답 미디어를 ROM 이미지 폴더에 저장한다. 다운로드 실패는 해당 이미지의 실패로 처리한다."""
                            if url:
                                try:
                                    r = requests.get(url, timeout=10)
                                    with open(path, "wb") as f:
                                        f.write(r.content)
                                except Exception as e:
                                    logging.getLogger(__name__).debug(
                                        "작업 실패: %s", type(e).__name__
                                    )

                        title_path = f"title/{safe_title}_title.png"
                        shot_path = f"s_shot/{safe_title}_screenshot.png"
                        save_image(title_url, os.path.join(img_dir, title_path))
                        save_image(shot_url, os.path.join(img_dir, shot_path))
                        rom["title"] = title
                        rom["title_image"] = title_path
                        rom["screenshots"] = [shot_path]
                        rom["publisher"] = publisher
                        rom["release_date"] = release_date
                        rom["description"] = desc
                        success_count += 1
                    except Exception:
                        fail_count += 1
                    updated_roms.append(rom)
                    self.progress.emit(
                        index, total, success_count, fail_count, filename
                    )
                    time.sleep(1.0)
                final_roms = []
                filenames_scrapped = {r["filename"] for r in target_roms}
                for r in roms:
                    if r["filename"] in filenames_scrapped:
                        match = [
                            u for u in updated_roms if u["filename"] == r["filename"]
                        ]
                        final_roms.append(match[0] if match else r)
                    else:
                        final_roms.append(r)
                with open(rom_list_path, "w", encoding="utf-8") as f:
                    json.dump(final_roms, f, indent=4, ensure_ascii=False)
        except Exception as e:
            import traceback

            traceback.print_exc()
            self.failed.emit(type(e).__name__)

    def map_system_id(self, platform):
        """런처 기종 식별자를 서비스의 시스템 번호로 바꾼다. 여러 번호를 지원하는 경우 순서대로 조회한다."""
        mapping = {
            "3do": "29",
            "atari_5200": "40",
            "arduboy": "263",
            "bbcmicro": "37",
            "super_nes": ["4", "202"],
            "wonderswan": ["45", "46"],
            "game_boy": ["9", "10"],
            "game_boy_advance": ["12", "119"],
            "atari_lynx": "28",
            "neo_geo_pocket": ["25", "82"],
            "pc_fx": "72",
            "pc_engine": ["31", "50", "105", "114"],
            "playstation": "57",
            "sega_saturn": ["22", "69", "75"],
            "virtual_boy": "11",
            "msx": ["113", "116", "117", "118"],
            "colecovision": "48",
            "nes": ["3", "106", "278"],
            "cpc": "65",
            "cdi": "113",
            "3ds": "17",
            "arcade": ["6", "7", "8", "75"],
            "nds": "15",
            "gamecube": "13",
            "wii": "16",
            "dos": "135",
            "zx81": "77",
            "master_system": "2",
            "pico8": "234",
            "neogeo": ["68", "70", "75", "142"],
            "dreamcast": ["23", "56", "75"],
            "intellivision": "115",
            "J2ME": "",
            "commodore_c64": "66",
            "commodore_amiga": ["64", "111"],
            "zx_spectrum": "76",
            "gg": "21",
            "mega_drive": ["1", "19", "203"],
            "handheldelectronic": "52",
            "p2000t": "287",
            "mac68k": ["86", "217"],
            "nintendo_64": "14",
            "pc_98": "208",
            "odyssey2": "104",
            "playstation2": "58",
            "playstation3": "59",
            "pokemon_mini": "211",
            "supervision": "207",
            "playstation_portable": "61",
            "playstation_vita": "62",
            "atari_7800": "41",
            "sharp_x68000": "79",
            "pc_88": "221",
            "mega_duck": "90",
            "atari_2600": "26",
            "uzebox": "216",
            "vectrex": "102",
            "commodore_c128": "66",
            "atari_jaguar": ["27", "171"],
            "sharp_x1": "220",
            "atari_st": "42",
            "nsw": "225",
            "xbox": "32",
            "x360": "33",
        }
        return mapping.get(platform.lower(), 0)


class ScraperSettingPopup(BasePopup):
    def __init__(self, theme_manager, app_id, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.app_id = app_id
        self.resize_popup()
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#FFFFFF"
        )
        bg = QWidget(self)
        bg.setStyleSheet(f"background-color: {bg_color};")
        bg.setGeometry(0, 0, self.width(), self.height())
        self.top_section = QWidget(bg)
        self.bottom_section = QWidget(bg)
        self.top_section.setStyleSheet("background-color: transparent; border: none;")
        self.bottom_section.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        layout = QVBoxLayout(bg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.top_section, 9)
        layout.addWidget(self.bottom_section, 1)
        bg.setLayout(layout)
        self.setup_top_section()
        self.setup_bottom_section()
        self.load_scrap_config()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        if self.parent():
            geo = self.parent().window().frameGeometry()
            center = geo.center()
            self.move(center - self.rect().center())
        self.show()
        self.raise_()
        self.activateWindow()

    def resize_popup(self):
        self.setFixedSize(
            self.theme_manager.scale_px(800), self.theme_manager.scale_px(900)
        )

    def setup_top_section(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(
            *[self.theme_manager.scale_px(x) for x in (30, 30, 30, 30)]
        )
        layout.setSpacing(self.theme_manager.scale_px(10))
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = "bold" if font_cfg.get("bold", False) else "normal"
        font_color = font_cfg.get("color", "#000000")
        base_style = f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_bold};\n            background-color: transparent;\n            border: none;\n        "
        input_style = f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_bold};\n            border: 1px solid #888888;\n            border-radius: 4px;\n            padding: {self.theme_manager.scale_px(6)}px;\n        "
        font_color = font_cfg.get("color", "#000000")
        label1 = QLabel(
            f'<a href="https://screenscraper.fr/" style="color: {font_color}; text-decoration: none;">https://screenscraper.fr/</a> 를 통해서 스크랩 데이터를 받아옵니다.'
        )
        label1.setTextFormat(Qt.RichText)
        label1.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label1.setOpenExternalLinks(True)
        label1.setStyleSheet(base_style)
        label2 = QLabel("아래 설정을 마친 뒤 스크랩 시작을 눌러주세요.")
        label2.setStyleSheet(base_style)
        layout.addWidget(label1)
        layout.addWidget(label2)
        layout.addSpacing(self.theme_manager.scale_px(30))
        login_label = QLabel("스크린 스크래퍼 로그인")
        login_label.setStyleSheet(base_style)
        layout.addWidget(login_label)
        id_row = QHBoxLayout()
        id_label = QLabel("ID")
        id_label.setStyleSheet(base_style)
        id_label.setFixedWidth(self.theme_manager.scale_px(40))
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID")
        self.id_input.setStyleSheet(input_style)
        id_row.addWidget(id_label)
        id_row.addWidget(self.id_input)
        layout.addLayout(id_row)
        pw_row = QHBoxLayout()
        pw_label = QLabel("PW")
        pw_label.setStyleSheet(base_style)
        pw_label.setFixedWidth(self.theme_manager.scale_px(40))
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("PW")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet(input_style)
        pw_row.addWidget(pw_label)
        pw_row.addWidget(self.pw_input)
        layout.addLayout(pw_row)
        layout.addSpacing(self.theme_manager.scale_px(20))
        platform_label = QLabel("기종 선택")
        platform_label.setStyleSheet(base_style)
        layout.addWidget(platform_label)
        self.platform_checkboxes = {}
        meta_root = os.path.join("l_libs", "emul")
        app_ids = []
        if self.app_id:
            app_ids.append(self.app_id)
        for folder in sorted(os.listdir(meta_root)):
            path = os.path.join(meta_root, folder, "meta.json")
            if folder != self.app_id and os.path.isfile(path):
                app_ids.append(folder)
        excluded_platforms = {"j2me", "segavisualmemoryunit"}
        platform_grid = QGridLayout()
        platform_grid.setHorizontalSpacing(self.theme_manager.scale_px(10))
        platform_grid.setVerticalSpacing(self.theme_manager.scale_px(10))
        (row, col) = (0, 0)
        max_columns = 4
        for idx, app_id in enumerate(app_ids):
            if app_id in excluded_platforms:
                continue
            checkbox = QCheckBox(app_id)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(base_style)
            platform_grid.addWidget(checkbox, row, col)
            self.platform_checkboxes[app_id] = checkbox
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
        layout.addLayout(platform_grid)
        layout.addSpacing(self.theme_manager.scale_px(20))
        region_label = QLabel("선호 국가")
        region_label.setStyleSheet(base_style)
        layout.addWidget(region_label)
        region_row = QHBoxLayout()
        self.region_group = QButtonGroup(self)
        regions = ["일본", "미국", "유럽", "프랑스"]
        for region in regions:
            btn = QRadioButton(region)
            btn.setStyleSheet(base_style)
            region_row.addWidget(btn)
            self.region_group.addButton(btn)
            if region == "일본":
                btn.setChecked(True)
        layout.addLayout(region_row)
        layout.addSpacing(self.theme_manager.scale_px(20))
        scrap_type_label = QLabel("스크랩 방식")
        scrap_type_label.setStyleSheet(base_style)
        layout.addWidget(scrap_type_label)
        scrap_type_row = QHBoxLayout()
        self.scrap_type_group = QButtonGroup(self)
        scrap_types = ["전체 다시 스크랩", "누락된 항목만 스크랩"]
        for label in scrap_types:
            btn = QRadioButton(label)
            btn.setStyleSheet(base_style)
            scrap_type_row.addWidget(btn)
            self.scrap_type_group.addButton(btn)
            if label == "누락된 항목만 스크랩":
                btn.setChecked(True)
        layout.addLayout(scrap_type_row)
        layout.addSpacing(self.theme_manager.scale_px(20))
        translate_label = QLabel("게임설명 자동 번역 (번역기 번역)")
        translate_label.setStyleSheet(base_style)
        layout.addWidget(translate_label)
        translate_row = QHBoxLayout()
        self.translate_group = QButtonGroup(self)
        options = ["번역하기", "원문 유지"]
        for opt in options:
            btn = QRadioButton(opt)
            btn.setStyleSheet(base_style)
            translate_row.addWidget(btn)
            self.translate_group.addButton(btn)
            if opt == "원문 유지":
                btn.setChecked(True)
            elif opt == "번역하기":
                btn.toggled.connect(
                    lambda checked, b=btn: (
                        checked
                        and b.text() == "번역하기"
                        and CustomAlertDialog(
                            "안내", "추후 구현 예정입니다.", self.theme_manager, self
                        ).exec()
                    )
                )
        layout.addLayout(translate_row)
        layout.addSpacing(self.theme_manager.scale_px(20))
        self.top_section.setLayout(layout)

    def load_scrap_config(self):
        """지역·작업 옵션을 복원하고 개인 인증 값은 환경변수에서 읽는다. 공개본은 계정 암호를 설정 JSON에 저장하지 않는다."""
        config_path = os.path.join("configs", "scraper.local.json")
        if not os.path.exists(config_path):
            return
        try:
            data = load_flags(config_path)
            self.id_input.setText(data.get("id", ""))
            self.pw_input.setText(data.get("pw", ""))
            region = data.get("region", "")
            for btn in self.region_group.buttons():
                btn.setChecked(btn.text() == region)
            scrap_type = data.get("scrap_type", "")
            for btn in self.scrap_type_group.buttons():
                btn.setChecked(btn.text() == scrap_type)
            translate = data.get("translate", "")
            for btn in self.translate_group.buttons():
                btn.setChecked(btn.text() == translate)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def save_scrap_config(self):
        """비밀정보를 제외한 수집 옵션만 저장한다. 실제 저장 경계는 scraper_credentials 모듈에서 다시 제한한다."""
        config_path = os.path.join("configs", "scraper.local.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            data = {
                "id": self.id_input.text().strip(),
                "pw": self.pw_input.text().strip(),
                "region": self.region_group.checkedButton().text()
                if self.region_group.checkedButton()
                else "",
                "scrap_type": self.scrap_type_group.checkedButton().text()
                if self.scrap_type_group.checkedButton()
                else "",
                "translate": self.translate_group.checkedButton().text()
                if self.translate_group.checkedButton()
                else "",
            }
            save_flags(config_path, data)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    def setup_bottom_section(self):
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_color = font_cfg.get("color", "#000000")
        font_bold = "bold" if font_cfg.get("bold", False) else "normal"
        button_style = f"\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {font_bold};\n            color: {font_color};\n            padding: {self.theme_manager.scale_px(10)}px {self.theme_manager.scale_px(20)}px;\n            border: 1px solid {font_color};\n            border-radius: 4px;\n            background-color: transparent;\n        "
        layout = QHBoxLayout()
        layout.setContentsMargins(
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(10),
            self.theme_manager.scale_px(30),
            self.theme_manager.scale_px(20),
        )
        layout.setSpacing(self.theme_manager.scale_px(20))
        layout.addStretch()
        self.scrap_button = QPushButton("스크랩 시작")
        self.scrap_button.setStyleSheet(button_style)
        layout.addWidget(self.scrap_button)
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setStyleSheet(button_style)
        layout.addWidget(self.cancel_button)
        self.bottom_section.setLayout(layout)
        self.cancel_button.clicked.connect(self.close)
        self.scrap_button.clicked.connect(self.on_scrap_clicked)

    def on_scrap_clicked(self):
        """선택 기종과 옵션을 수집해 새 작업 스레드를 시작한다. 시그널 연결과 상태 초기화를 start보다 먼저 끝낸다."""
        self.save_scrap_config()
        self.scrap_button.setEnabled(False)
        selected_platforms = [
            k for (k, v) in self.platform_checkboxes.items() if v.isChecked()
        ]
        if not selected_platforms:
            CustomAlertDialog(
                "안내", "선택된 기종이 없습니다.", self.theme_manager, self
            ).exec()
            self.scrap_button.setEnabled(True)
            return
        config = {
            "id": self.id_input.text().strip(),
            "pw": self.pw_input.text().strip(),
            "region": self.region_group.checkedButton().text(),
            "scrap_type": self.scrap_type_group.checkedButton().text(),
            "translate": self.translate_group.checkedButton().text(),
        }
        self.progress_popup = ScrapProgressPopup(self.theme_manager, self)
        self.progress_popup.show()
        self.scraper_thread = ScraperThread(config, selected_platforms)
        # 매번 새 스레드를 생성하므로 이전 연결을 disconnect할 필요가 없다.
        self.scrap_done_called = False
        self.scraper_thread.finished.connect(self._on_scrap_done_once)
        self.scraper_thread.failed.connect(self.on_scrap_failed)
        self.scraper_thread.progress.connect(self.on_scrap_progress)
        self.scraper_thread.start()

    def on_scrap_progress(self, index, total, success, fail, filename):
        if hasattr(self, "progress_popup"):
            self.progress_popup.update_progress(index, total, success, fail, filename)

    def _on_scrap_done_once(self):
        """완료 UI가 두 번 열리지 않도록 가드한다. 실패 알림과 스레드 종료 알림은 별개로 도착할 수 있다."""
        if self.scrap_done_called:
            return
        self.scrap_done_called = True
        self.on_scrap_done()

    def on_scrap_done(self):
        self.progress_popup.close()

        def after_confirm():
            try:
                from rom_list_popup import RomListPopup
                from PySide6.QtWidgets import QApplication

                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, RomListPopup):
                        widget.reload()
                        break
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            self.close()

        alert = CustomAlertDialog(
            "완료", "스크랩이 완료되었습니다.", self.theme_manager, self
        )
        alert.accepted.connect(after_confirm)
        alert.exec()

    def on_scrap_failed(self, msg):
        self.progress_popup.close()
        CustomAlertDialog(
            "스크랩 실패", f"오류 발생: {msg}", self.theme_manager, self
        ).exec()


class ScrapProgressPopup(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.theme_manager = theme_manager
        self.setFixedSize(
            self.theme_manager.scale_px(500), self.theme_manager.scale_px(200)
        )
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#FFFFFF"
        )
        self.setStyleSheet(f"background-color: {bg_color};")
        font_cfg = theme_manager.get("fonts.팝업라벨", {})
        font_family = font_cfg.get("family", "맑은 고딕")
        font_size = font_cfg.get("size", 22)
        font_bold = font_cfg.get("bold", False)
        font_color = font_cfg.get("color", "#000000")
        label_style = f"\n            color: {font_color};\n            font-family: '{font_family}';\n            font-size: {font_size}px;\n            font-weight: {('bold' if font_bold else 'normal')};\n            background-color: transparent;\n            border: none;\n        "
        self.label_title = QLabel("스크랩 진행률")
        self.label_title.setStyleSheet(label_style)
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_filename = QLabel("현재 파일: -")
        self.label_filename.setStyleSheet(label_style)
        self.label_filename.setAlignment(Qt.AlignCenter)
        self.label_count = QLabel("전체 0개 | 성공 0개 | 실패 0개")
        self.label_count.setStyleSheet(label_style)
        self.label_count.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(self.theme_manager.scale_px(18))
        layout = QVBoxLayout()
        layout.setContentsMargins(
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
            self.theme_manager.scale_px(20),
        )
        layout.setSpacing(self.theme_manager.scale_px(10))
        layout.addWidget(self.label_title)
        layout.addWidget(self.label_filename)
        layout.addWidget(self.label_count)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def update_progress(self, index, total, success, fail, filename):
        self.label_filename.setText(f"현재 파일: {filename}")
        self.label_count.setText(f"전체 {total}개 | 성공 {success}개 | 실패 {fail}개")
        percent = int((success + fail) / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
