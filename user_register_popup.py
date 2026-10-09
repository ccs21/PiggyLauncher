"""Classic의 user_register_popup 모듈. 역할과 읽는 순서는 docs/SOURCE_MAP.md를 참고한다."""

import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QTextEdit,
    QGridLayout,
    QSizePolicy,
    QListWidgetItem,
    QDialog,
)
from PySide6.QtGui import QPixmap, QFont, QImage
from PySide6.QtCore import Qt, QTimer, QThread, Signal
import os
import json
from pathlib import Path
from popup_alert import CustomAlertDialog
from popup_windows import BasePopup
from popup_utils import ConfirmDialog
from cdp_scraper import scrape_steam_search_results
from register_progress_popup import RegisterProgressPopup


class SteamScrapeWorker(QThread):
    result_ready = Signal(dict, dict)

    def __init__(self, appid):
        super().__init__()
        self.appid = appid

    def run(self):
        from cdp_scraper import scrape_steam_metadata

        (metadata, images) = scrape_steam_metadata(self.appid)
        self.result_ready.emit(metadata, images)


class SteamSearchWorker(QThread):
    results_ready = Signal(list)

    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword

    def run(self):
        results = scrape_steam_search_results(self.keyword)
        self.results_ready.emit(results)


class GameRegisterEditPopup(BasePopup):
    def __init__(
        self,
        parent=None,
        theme_manager=None,
        edit_mode=False,
        edit_data=None,
        appid=None,
    ):
        self.edit_mode = edit_mode
        self.edit_data = edit_data or {}
        self.edit_appid = appid
        self.theme = theme_manager
        self.screenshot_index = 0
        self.screenshot_labels = []
        self.header_label = None
        self.thumbnail_label = None
        self.thumbnail_path = None
        self.header_path = None
        self.screenshot_paths = []
        self.confirm_bg = self.theme.get("background.popup.value", "#555555")
        self.confirm_text = self.theme.get("fonts.팝업라벨.color", "#FFFFFF")
        self.cancel_bg = self.theme.get("background.popup.value", "#555555")
        self.cancel_text = self.theme.get("fonts.팝업라벨.color", "#FFFFFF")
        self.input_bg = self.theme.get("background.popup.value", "#FFFFFF")
        self.input_text_color = self.theme.get("fonts.팝업라벨.color", "#FFFFFF")
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowTitle("게임 수동 등록 / 메타데이터 수정")
        self.resize_popup()

    def init_ui(self):
        layout = QVBoxLayout(self)
        bg_item = self.theme.get("background.popup", {"value": "#555555"})
        bg = bg_item.get("value", "#FFFFFF")
        self.setStyleSheet(f"background-color: {bg};")
        self.top_frame = QFrame()
        self.top_frame.setFrameShape(QFrame.StyledPanel)
        self.top_frame.setStyleSheet(f"border: none; background-color: {bg};")
        top_layout = QHBoxLayout(self.top_frame)

        self.top_left = QFrame()
        self.top_left.setFrameShape(QFrame.StyledPanel)
        self.top_left.setStyleSheet(f"border: none; background-color: {bg};")
        self.init_thumbnail_section(self.top_left)
        thumb_button = QPushButton("썸네일 찾아보기")
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        font = QFont(font_conf["family"])
        font.setPointSizeF(font_conf["size"])
        font.setBold(font_conf.get("bold", False))
        thumb_button.setFont(font)
        thumb_button.setMinimumHeight(self.theme.scale_px(60))
        thumb_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        thumb_button.clicked.connect(self.select_thumbnail_image)
        thumb_wrapper = QFrame()
        thumb_layout = QVBoxLayout(thumb_wrapper)
        thumb_layout.setAlignment(Qt.AlignCenter)
        thumb_layout.addWidget(thumb_button)
        left_section = QFrame()
        left_layout = QVBoxLayout(left_section)
        left_layout.addWidget(self.top_left, 9)
        left_layout.addWidget(thumb_wrapper, 1)
        self.top_center = QFrame()
        self.top_center.setFrameShape(QFrame.StyledPanel)
        self.top_center.setStyleSheet(f"border: none; background-color: {bg};")
        self.init_header_section(self.top_center)
        header_button = QPushButton("헤더 이미지 찾아보기")
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        font = QFont(font_conf["family"])
        font.setPointSizeF(font_conf["size"])
        font.setBold(font_conf.get("bold", False))
        header_button.setFont(font)
        header_button.setMinimumHeight(self.theme.scale_px(60))
        header_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        header_button.clicked.connect(self.select_header_image)
        header_wrapper = QFrame()
        header_layout = QVBoxLayout(header_wrapper)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_button)
        center_section = QFrame()
        center_layout = QVBoxLayout(center_section)
        center_layout.addWidget(self.top_center, 9)
        center_layout.addWidget(header_wrapper, 1)
        self.top_right = QFrame()
        self.top_right.setFrameShape(QFrame.StyledPanel)
        self.top_right.setStyleSheet(f"border: none; background-color: {bg};")
        self.init_metadata_section(self.top_right)
        register_button = QPushButton(
            "수정 완료" if getattr(self, "edit_mode", False) else "등록"
        )
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        font = QFont(font_conf["family"])
        font.setPointSizeF(font_conf["size"])
        font.setBold(font_conf.get("bold", False))
        register_button.setFont(font)
        register_button.setMinimumHeight(self.theme.scale_px(60))
        register_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        register_button.clicked.connect(self.on_register_clicked)
        register_wrapper = QFrame()
        register_layout = QHBoxLayout(register_wrapper)
        register_layout.setAlignment(Qt.AlignCenter)
        register_layout.addWidget(register_button)
        register_layout.addSpacing(self.theme.scale_px(30))
        cancel_button = QPushButton("취소")
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        font = QFont(font_conf["family"])
        font.setPointSizeF(font_conf["size"])
        font.setBold(font_conf.get("bold", False))
        cancel_button.setFont(font)
        cancel_button.setMinimumHeight(self.theme.scale_px(60))
        cancel_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.cancel_bg}; color: {self.cancel_text}; padding: 5px;"
        )
        cancel_button.clicked.connect(self.reject)
        register_layout.addWidget(cancel_button)
        right_section = QFrame()
        right_layout = QVBoxLayout(right_section)
        right_layout.addWidget(self.top_right, 9)
        right_layout.addWidget(register_wrapper, 1)
        top_layout.addWidget(left_section, 2)
        top_layout.addWidget(center_section, 3)
        top_layout.addWidget(right_section, 5)
        self.middle_frame = QFrame()
        self.middle_frame.setFrameShape(QFrame.StyledPanel)
        self.middle_frame.setStyleSheet(f"border: none; background-color: {bg};")
        middle_layout = QHBoxLayout(self.middle_frame)
        middle_left = QFrame()
        middle_left.setFrameShape(QFrame.StyledPanel)
        middle_left.setStyleSheet(f"border: none; background-color: {bg};")
        middle_left_layout = QVBoxLayout(middle_left)
        desc_label = QLabel("게임 설명")
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        desc_label.setStyleSheet(f"color: {self.confirm_text};")
        desc_font = QFont(font_conf["family"])
        desc_font.setPointSizeF(font_conf["size"])
        desc_font.setBold(font_conf.get("bold", False))
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignCenter)
        middle_left_layout.addStretch()
        middle_left_layout.addWidget(desc_label)
        middle_left_layout.addStretch()
        middle_right = QFrame()
        middle_right.setFrameShape(QFrame.StyledPanel)
        middle_right.setStyleSheet(f"border: none; background-color: {bg};")
        middle_right_layout = QVBoxLayout(middle_right)
        self.description_edit = QTextEdit()
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        font = QFont(font_conf["family"])
        font.setPointSizeF(font_conf["size"])
        font.setBold(font_conf.get("bold", False))
        self.description_edit.setFont(font)
        desc_bg = self.theme.get("background.user_description.value", "#FFFFFF")
        if "theme\\default\\" in desc_bg:
            desc_bg = desc_bg.split("\\")[-1]
        self.description_edit.setStyleSheet(
            f"background-color: {self.input_bg}; color: {self.input_text_color}; border: 1px solid #ccc;"
        )
        middle_right_layout.addWidget(self.description_edit)
        middle_layout.addWidget(middle_left, 15)
        middle_layout.addWidget(middle_right, 85)
        self.bottom_frame = QFrame()
        self.bottom_frame.setFrameShape(QFrame.StyledPanel)
        self.bottom_frame.setStyleSheet(f"border: none; background-color: {bg};")
        bottom_layout = QHBoxLayout(self.bottom_frame)
        bottom_left = QFrame()
        bottom_left.setFrameShape(QFrame.StyledPanel)
        bottom_left.setStyleSheet(f"border: none; background-color: {bg};")
        bottom_left_layout = QVBoxLayout(bottom_left)
        self.screenshot_button = QPushButton("스크린샷\n찾아보기")
        self.screenshot_button.setMinimumHeight(self.theme.scale_px(60))
        self.screenshot_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        weight = QFont.Bold if font_conf.get("bold", False) else QFont.Normal
        self.screenshot_button.setFont(
            QFont(font_conf["family"], int(font_conf["size"]), weight)
        )
        self.screenshot_button.clicked.connect(self.select_screenshots)
        bottom_left_layout.addStretch()
        bottom_left_layout.addWidget(self.screenshot_button)
        bottom_left_layout.addStretch()
        bottom_right = QFrame()
        bottom_right.setFrameShape(QFrame.StyledPanel)
        bottom_right.setStyleSheet(f"border: none; background-color: {bg};")
        grid_layout = QGridLayout(bottom_right)
        grid_layout.setHorizontalSpacing(self.theme.scale_px(5))
        grid_layout.setVerticalSpacing(self.theme.scale_px(5))
        grid_layout.setContentsMargins(
            self.theme.scale_px(5),
            self.theme.scale_px(5),
            self.theme.scale_px(5),
            self.theme.scale_px(5),
        )
        for i in range(2):
            for j in range(10):
                index = i * 10 + j
                label = QLabel()
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                label.setMinimumSize(self.theme.scale_px(100), self.theme.scale_px(56))
                label.setStyleSheet("background-color: #ddd; border: 1px solid #aaa;")
                label.setAlignment(Qt.AlignCenter)
                self.bind_screenshot_click(label, index)
                grid_layout.addWidget(label, i, j)
                self.screenshot_labels.append(label)
        bottom_layout.addWidget(bottom_left, 15)
        bottom_layout.addWidget(bottom_right, 85)
        layout.addWidget(self.top_frame, 4)
        layout.addWidget(self.middle_frame, 3)
        layout.addWidget(self.bottom_frame, 3)
        if getattr(self, "edit_mode", False):
            QTimer.singleShot(0, self.fill_existing_data)

    def init_thumbnail_section(self, parent):
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignCenter)
        self.thumbnail_label = QLabel("썸네일 미리보기")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumbnail_label.setStyleSheet(f"color: {self.confirm_text};")
        layout.addWidget(self.thumbnail_label)

    def init_header_section(self, parent):
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignCenter)
        self.header_label = QLabel("헤더 이미지 미리보기")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.header_label.setStyleSheet(f"color: {self.confirm_text};")
        layout.addWidget(self.header_label)

    def init_metadata_section(self, parent):
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignTop)
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        input_font = QFont(font_conf["family"])
        input_font.setPointSizeF(font_conf["size"])
        input_font.setBold(font_conf.get("bold", False))

        # 위젯 순서 대신 항목 키로 보관한다. 입력칸을 추가해도 저장 대상이 밀리지 않는다.
        self.metadata_inputs = {}

        def row(label_text, field):
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(input_font)
            label.setStyleSheet(f"color: {self.confirm_text};")
            line_edit = QLineEdit()
            self.metadata_inputs[field] = line_edit
            line_edit.setFont(input_font)
            line_edit.setStyleSheet(
                f"background-color: {self.input_bg}; color: {self.input_text_color}; border: 1px solid #ccc;"
            )
            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)
            return row_layout

        exe_layout = QHBoxLayout()
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        exe_font = QFont(font_conf["family"])
        exe_font.setPointSizeF(font_conf["size"])
        exe_font.setBold(font_conf.get("bold", False))
        exe_label = QLabel("게임 실행파일 ")
        exe_label.setFont(exe_font)
        exe_label.setStyleSheet(f"color: {self.confirm_text};")
        self.exe_input = QLineEdit()
        self.exe_input.setStyleSheet(
            f"background-color: {self.input_bg}; color: {self.input_text_color}; border: 1px solid #ccc;"
        )
        self.exe_input.setFont(exe_font)
        exe_button = QPushButton("찾아보기")
        exe_button.setFont(exe_font)
        exe_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        exe_layout.addWidget(exe_label)
        exe_layout.addWidget(self.exe_input)
        exe_layout.addWidget(exe_button)
        exe_button.clicked.connect(self.select_exe_file)
        layout.addLayout(exe_layout)
        layout.addSpacing(self.theme.scale_px(10))
        search_layout = QHBoxLayout()
        font_conf = self.theme.get(
            "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
        )
        search_font = QFont(font_conf["family"])
        search_font.setPointSizeF(font_conf["size"])
        search_font.setBold(font_conf.get("bold", False))
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet(
            f"\n            background-color: {self.input_bg};\n            color: {self.input_text_color};\n            border: 1px solid #ccc;\n            padding-left: 10px;\n            selection-background-color: {self.confirm_bg};\n            selection-color: {self.confirm_text};\n            font-family: {font_conf['family']};\n            font-size: {int(font_conf['size'])}pt;\n            "
        )
        self.search_input.setFont(search_font)
        self.search_input.setPlaceholderText("검색어를 입력해 주세요.")
        self.search_input.setStyleSheet(
            self.search_input.styleSheet()
            + f"QLineEdit::placeholder {{ color: {self.input_text_color}; opacity: 0.7; }}"
        )
        search_button = QPushButton("메타 데이터 검색")
        search_button.setFont(search_font)
        search_button.setStyleSheet(
            f"border: 1px solid {self.confirm_text}; background-color: {self.confirm_bg}; color: {self.confirm_text}; padding: 5px;"
        )
        search_button.clicked.connect(self.open_search_popup)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        layout.addSpacing(self.theme.scale_px(10))
        layout.addLayout(row("제목 ", "title"))
        layout.addSpacing(self.theme.scale_px(10))
        layout.addLayout(row("개발사 ", "developer"))
        layout.addSpacing(self.theme.scale_px(10))
        layout.addLayout(row("배급사 ", "publisher"))
        layout.addSpacing(self.theme.scale_px(10))
        layout.addLayout(row("출시일 ", "release_date"))

    def on_register_clicked(self):
        """입력값과 선택 이미지를 로컬 라이브러리에 저장한다.
        수정 모드는 기존 ID/플랫폼을 유지하고 신규 모드는 경로 인덱스를 이용한다.
        검색 결과를 선택해 폼을 채우는 단계와 실제 파일을 쓰는 단계가 분리되어 있다.
        """
        import os, shutil, time
        from pathlib import Path

        exe_full_path = self.exe_input.text().strip()
        if not exe_full_path:
            return
        if self.edit_mode:
            appid = self.edit_appid
            platform = self.edit_data.get("platform", "user").lower()
            game_dir = Path(f"l_libs/{platform}/{appid}")
        else:
            index_path = Path("configs/user_register_index.json")
            index_path.parent.mkdir(parents=True, exist_ok=True)
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
            else:
                index = {}
            if exe_full_path in index:
                appid = index[exe_full_path]
            else:
                appid = int(time.time() * 1000) % 10000000
                index[exe_full_path] = appid
                with open(index_path, "w", encoding="utf-8") as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
            game_dir = Path(f"l_libs/user/{appid}")
        ss_dir = game_dir / "screenshots"
        game_dir.mkdir(parents=True, exist_ok=True)
        ss_dir.mkdir(exist_ok=True)
        if self.edit_mode:
            meta_path = game_dir / "meta.json"
            if not meta_path.exists():
                return
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            fields = self.metadata_inputs
            meta["title"] = fields["title"].text().strip()
            meta["developer"] = fields["developer"].text().strip()
            meta["publisher"] = fields["publisher"].text().strip()
            meta["release_date"] = fields["release_date"].text().strip()
            meta["description"] = self.description_edit.toPlainText().strip()
            meta["exe"] = os.path.basename(exe_full_path)
            meta["exe_full_path"] = exe_full_path
            meta["path"] = str(Path(exe_full_path).parent)
        else:
            meta = {
                "appid": appid,
                "title": self.metadata_inputs["title"].text().strip(),
                "release_date": self.metadata_inputs["release_date"].text().strip(),
                "platform": "User",
                "developer": self.metadata_inputs["developer"].text().strip(),
                "publisher": self.metadata_inputs["publisher"].text().strip(),
                "description": self.description_edit.toPlainText().strip(),
                "thumbnail": "library_600x900.jpg",
                "header": "library_header.jpg",
                "screenshots": [],
                "exe": os.path.basename(exe_full_path),
                "exe_full_path": exe_full_path,
                "path": str(Path(exe_full_path).parent),
            }
        thumb_path = game_dir / "library_600x900.jpg"
        header_path = game_dir / "library_header.jpg"
        from PIL import Image

        if getattr(self, "thumbnail_path", None) and os.path.exists(
            self.thumbnail_path
        ):
            try:
                img = Image.open(self.thumbnail_path)
                thumb_h = 450
                scale = thumb_h / img.height
                resized = img.resize((int(img.width * scale), thumb_h), Image.LANCZOS)
                crop_x = max((resized.width - 300) // 2, 0)
                cropped = resized.crop((crop_x, 0, crop_x + 300, thumb_h))
                cropped.save(thumb_path)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if getattr(self, "header_path", None) and os.path.exists(self.header_path):
            try:
                img = Image.open(self.header_path)
                header_w = 460
                scale = header_w / img.width
                resized = img.resize((header_w, int(img.height * scale)), Image.LANCZOS)
                crop_y = max((resized.height - 215) // 2, 0)
                cropped = resized.crop((0, crop_y, header_w, crop_y + 215))
                cropped.save(header_path)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        if isinstance(getattr(self, "screenshot_paths", None), list):
            for i, src_path in enumerate(self.screenshot_paths):
                if not src_path or not os.path.exists(src_path):
                    continue
                dst = ss_dir / f"screenshot_{i + 1}.jpg"
                try:
                    shutil.copyfile(src_path, dst)
                    meta["screenshots"].append(f"screenshots/screenshot_{i + 1}.jpg")
                except Exception as e:
                    logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        with open(game_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        tmp_dir = Path("tmp_scrape")
        if tmp_dir.exists() and tmp_dir.is_dir():
            import shutil

            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        for w in QApplication.topLevelWidgets():
            if w.isVisible() and hasattr(w, "central_content"):
                central = w.central_content
                if self.edit_mode:
                    focus_platform = (
                        self.edit_data.get("platform", "user")
                        if isinstance(self.edit_data, dict)
                        else "user"
                    )
                    central._pending_action = "edit"
                    central._pending_focus_app = str(appid)
                    central._pending_focus_platform = str(focus_platform)
                else:
                    central._pending_action = "register_new"
                    central._pending_focus_app = None
                    central._pending_focus_platform = None
                QTimer.singleShot(0, central.render_cards)
        self.accept()

    def fill_existing_data(self):
        """편집할 게임의 기존 텍스트·이미지 경로를 폼에 복원한다. 메타데이터 사전의 누락 필드는 기본값으로 처리한다."""
        fields = self.metadata_inputs
        self.exe_input.setText(self.edit_data.get("exe_full_path", ""))
        fields["title"].setText(self.edit_data.get("title", ""))
        fields["developer"].setText(self.edit_data.get("developer", ""))
        fields["publisher"].setText(self.edit_data.get("publisher", ""))
        fields["release_date"].setText(self.edit_data.get("release_date", ""))
        self.description_edit.setPlainText(self.edit_data.get("description", ""))
        platform = self.edit_data.get("platform", "user")
        base_path = os.path.join("l_libs", platform.lower(), str(self.edit_appid))
        thumb_path = os.path.join(base_path, "library_600x900.jpg")
        if os.path.exists(thumb_path):
            self.thumbnail_path = thumb_path
            pixmap = QPixmap(thumb_path).scaled(
                self.thumbnail_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(pixmap)
            self.thumbnail_label.setStyleSheet(
                "background-color: transparent; border: none;"
            )
        header_path = os.path.join(base_path, "library_header.jpg")
        if os.path.exists(header_path):
            self.header_path = header_path
            pixmap = QPixmap(header_path).scaled(
                self.header_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.header_label.setPixmap(pixmap)
            self.header_label.setStyleSheet(
                "background-color: transparent; border: none;"
            )
        ss_dir = Path(os.path.join(base_path, "screenshots"))
        self.screenshot_paths = []
        if ss_dir.exists():
            for file in sorted(ss_dir.glob("screenshot_*.jpg")):
                self.screenshot_paths.append(str(file))
        self.render_screenshots()

    def select_thumbnail_image(self):
        (file_path, _) = QFileDialog.getOpenFileName(
            self, "썸네일 이미지 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.thumbnail_path = file_path
            pixmap = QPixmap(file_path).scaled(
                self.thumbnail_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(pixmap)

    def select_header_image(self):
        (file_path, _) = QFileDialog.getOpenFileName(
            self, "헤더 이미지 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.header_path = file_path
            pixmap = QPixmap(file_path).scaled(
                self.header_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.header_label.setPixmap(pixmap)

    def select_exe_file(self):
        (file_path, _) = QFileDialog.getOpenFileName(
            self, "실행 파일 선택", "", "Executable (*.exe)"
        )
        if file_path:
            self.exe_input.setText(file_path)

    def open_search_popup(self):
        """검색어로 후보를 조회하고 선택한 게임의 정보를 폼에 채운다. 입력 폼의 등록 버튼을 누르기 전에는 등록을 확정하지 않는다."""
        from PySide6.QtWidgets import (
            QDialog,
            QListWidget,
            QVBoxLayout,
            QLabel,
            QHBoxLayout,
            QWidget,
        )
        from PySide6.QtGui import QPixmap, QFont
        import urllib.request

        class SearchPopup(QDialog):
            def __init__(self, keyword, results, parent=None):
                super().__init__(parent)
                self.keyword = keyword
                self.results = results
                self.setWindowTitle(f"스팀 검색 결과: {keyword}")
                if parent:
                    (pw, ph) = (parent.width(), parent.height())
                    (popup_w, popup_h) = (int(pw * 0.8), int(ph * 0.8))
                    self.resize(popup_w, popup_h)
                    parent_pos = parent.pos()
                    x = parent_pos.x() + (parent.width() - popup_w) // 2
                    y = parent_pos.y() + (parent.height() - popup_h) // 2
                    self.move(x, y)
                else:
                    self.setMinimumSize(
                        parent.theme.scale_px(800), parent.theme.scale_px(600)
                    )
                    self.resize(parent.theme.scale_px(800), parent.theme.scale_px(600))
                layout = QVBoxLayout(self)
                self.list = QListWidget()
                self.list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                font_conf = parent.theme.get(
                    "fonts.팝업라벨", {"family": "맑은 고딕", "size": 22, "bold": False}
                )
                font = QFont(font_conf["family"])
                font.setPointSizeF(font_conf["size"])
                font.setBold(font_conf.get("bold", False))
                if not self.results:
                    if hasattr(parent, "progress_popup"):
                        parent.progress_popup.close()

                    def show_alert_and_close():
                        CustomAlertDialog(
                            "검색 실패",
                            "검색 결과가 없습니다.\nSteam 상점 페이지에서 검색이 가능한 검색어를 사용 하셔야 합니다.",
                            self.parent().theme,
                            parent=self,
                        ).exec()
                        self.close()

                    QTimer.singleShot(0, show_alert_and_close)
                    return
                if hasattr(parent, "progress_popup"):
                    parent.progress_popup.close()
                for result in self.results:
                    item = QListWidgetItem()
                    widget = QWidget()
                    hbox = QHBoxLayout(widget)
                    image_label = QLabel()
                    try:
                        data = urllib.request.urlopen(result["thumb"]).read()
                        image = QImage()
                        image.loadFromData(data)
                        pixmap = QPixmap.fromImage(image).scaledToHeight(
                            parent.theme.scale_px(64), Qt.SmoothTransformation
                        )
                        image_label.setPixmap(pixmap)
                    except Exception:
                        image_label.setText("[X]")
                    title_label = QLabel(result["title"])
                    title_label.setFont(font)
                    title_label.setStyleSheet(f"color: {parent.confirm_text};")
                    hbox.addWidget(image_label)
                    hbox.addWidget(title_label)
                    hbox.addStretch()
                    widget.setLayout(hbox)
                    item.setSizeHint(widget.sizeHint())
                    self.list.addItem(item)
                    self.list.setItemWidget(item, widget)
                self.list.itemClicked.connect(self.item_selected)
                layout.addWidget(self.list, stretch=1)

            def item_selected(self, item):
                parent = self.parent()
                self.accept()
                self.progress_popup = RegisterProgressPopup(parent.theme, parent)
                self.progress_popup.set_text("수집 중입니다...")
                self.progress_popup.show()
                QApplication.processEvents()
                row_index = self.list.row(item)
                selected = self.results[row_index]
                appid = selected["appid"]
                self.worker = SteamScrapeWorker(appid)
                self.worker.result_ready.connect(
                    lambda metadata, images: self.on_scrape_finished(
                        metadata, images, parent
                    )
                )
                self.worker.start()

            def on_scrape_finished(self, metadata, images, parent):
                self.progress_popup.close()
                if not metadata:
                    return
                fields = parent.metadata_inputs
                if fields:
                    fields["title"].setText(metadata.get("title", ""))
                    fields["developer"].setText(metadata.get("developer", ""))
                    fields["publisher"].setText(metadata.get("publisher", ""))
                    fields["release_date"].setText(metadata.get("release_date", ""))
                parent.description_edit.setPlainText(metadata.get("description", ""))
                from PySide6.QtGui import QPixmap
                from PySide6.QtCore import Qt
                import os

                if "thumbnail" in images and os.path.exists(images["thumbnail"]):
                    pixmap = QPixmap(images["thumbnail"]).scaled(
                        parent.thumbnail_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    parent.thumbnail_label.setPixmap(pixmap)
                    parent.thumbnail_path = images["thumbnail"]
                if "header" in images and os.path.exists(images["header"]):
                    pixmap = QPixmap(images["header"]).scaled(
                        parent.header_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    parent.header_label.setPixmap(pixmap)
                    parent.header_path = images["header"]
                parent.screenshot_paths = []
                for img_path in images.get("screenshots", []):
                    if os.path.exists(img_path):
                        parent.screenshot_paths.append(img_path)
                parent.render_screenshots()
                parent.screenshot_index = len(parent.screenshot_paths)

        import shutil
        from pathlib import Path

        tmp_dir = Path("tmp_scrape")
        if tmp_dir.exists() and tmp_dir.is_dir():
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        keyword = self.search_input.text().strip()
        if not keyword:
            CustomAlertDialog(
                "입력 필요", "검색어를 입력해 주세요.", self.theme, parent=self
            ).exec()
            return
        self.progress_popup = RegisterProgressPopup(self.theme, self)
        self.progress_popup.set_text("검색 중입니다...")
        self.progress_popup.show()
        QApplication.processEvents()

        def launch_popup(results):
            if hasattr(self, "progress_popup"):
                self.progress_popup.close()
            popup = SearchPopup(keyword, results, self)
            popup.exec()

        self.search_worker = SteamSearchWorker(keyword)
        self.search_worker.results_ready.connect(launch_popup)
        self.search_worker.start()

    def select_screenshots(self):
        (files, _) = QFileDialog.getOpenFileNames(
            self, "스크린샷 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not files:
            return
        max_count = len(self.screenshot_labels)
        remaining_slots = max_count - len(self.screenshot_paths)
        files = files[:remaining_slots]
        for path in files:
            self.screenshot_paths.append(path)
        for label in self.screenshot_labels:
            label.clear()
        for i, path in enumerate(self.screenshot_paths):
            if i >= len(self.screenshot_labels):
                break
            if os.path.exists(path):
                pixmap = QPixmap(path).scaled(
                    self.screenshot_labels[i].size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.screenshot_labels[i].setPixmap(pixmap)
                self.bind_screenshot_click(self.screenshot_labels[i], i)
        self.screenshot_index = len(self.screenshot_paths)

    def confirm_remove_screenshot(self, index):
        if index >= len(self.screenshot_paths):
            return
        if not self.screenshot_paths[index]:
            return
        dialog = ConfirmDialog(
            "스크린샷 삭제", "선택한 이미지를 삭제하시겠습니까?", self.theme, self
        )
        if dialog.exec() == QDialog.Accepted:
            self.screenshot_labels[index].clear()
            self.screenshot_paths[index] = None
            self.screenshot_paths = [p for p in self.screenshot_paths if p]
            for label in self.screenshot_labels:
                label.clear()
            for i, path in enumerate(self.screenshot_paths):
                if i >= len(self.screenshot_labels):
                    break
                if os.path.exists(path):
                    pixmap = QPixmap(path).scaled(
                        self.screenshot_labels[i].size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    self.screenshot_labels[i].setPixmap(pixmap)
                    self.bind_screenshot_click(self.screenshot_labels[i], i)
            self.screenshot_index = len(self.screenshot_paths)

    def bind_screenshot_click(self, label, index):
        """클로저에 현재 이미지 인덱스를 보관한다. 반복문의 마지막 인덱스가 모든 콜백에 공유되는 문제를 피한다."""

        def on_click(event):
            self.confirm_remove_screenshot(index)

        label.mousePressEvent = on_click

    def render_screenshots(self):
        """선택한 스크린샷 목록으로 미리보기를 다시 만든다. 클릭 콜백에는 각 이미지의 인덱스를 고정해 연결한다."""
        for label in self.screenshot_labels:
            label.clear()
        for i, path in enumerate(self.screenshot_paths):
            if i >= len(self.screenshot_labels):
                break
            if os.path.exists(path):
                pixmap = QPixmap(path).scaled(
                    self.screenshot_labels[i].size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.screenshot_labels[i].setPixmap(pixmap)
                self.bind_screenshot_click(self.screenshot_labels[i], i)
        self.screenshot_index = len(self.screenshot_paths)

    def closeEvent(self, event):
        super().closeEvent(event)

    def reject(self):
        if self.isModal():
            self.cleanup()
            self.done(QDialog.Rejected)
        else:
            self.close()

    def cleanup(self):
        """창의 자식 위젯을 이벤트 처리 후 해제한다. 파일 삭제나 게임 제거를 수행하는 함수가 아니다."""
        for widget in self.findChildren(QWidget):
            widget.deleteLater()
