"""게임별 연동 프로그램과 실행 간격을 편집하는 화면.
설정 저장과 실제 프로그램 실행은 분리되어 있다. 실행 순서는 game_detail_screen에서 읽는다.
"""

import os
import json
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QComboBox,
)
from PySide6.QtGui import QFont, QGuiApplication
from popup_alert import CustomAlertDialog


class BatchSettingPopup(QDialog):
    def __init__(self, platform, appid, theme_manager, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.appid = appid
        self.theme_manager = theme_manager
        self.theme = theme_manager.theme
        self.setWindowTitle("배치 실행 설정")
        if parent:
            parent_geom = parent.window().geometry()
            popup_w = int(parent_geom.width() * 0.8)
            popup_h = int(parent_geom.height() * 0.8)
            self.resize(popup_w, popup_h)
            center = parent_geom.center()
            geo = self.frameGeometry()
            geo.moveCenter(center)
            self.move(geo.topLeft())
        else:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            popup_w = int(screen.width() * 0.8)
            popup_h = int(screen.height() * 0.8)
            self.resize(popup_w, popup_h)
        self.config_path = f"configs/{platform}_{appid}_batch.json"
        self.program_paths = ["", "", ""]
        self.last_dir = os.path.expanduser("~")
        self.init_ui()
        self.load_config()

    def init_ui(self):
        bg_color = self.theme_manager.get("background.popup", {}).get(
            "value", "#555555"
        )
        self.setStyleSheet(f"background-color: {bg_color};")
        font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        font_big = QFont()
        font_big.setFamily(font_cfg.get("family", "맑은 고딕"))
        font_big.setPointSizeF(font_cfg.get("size", 20))
        font_big.setBold(font_cfg.get("bold", False))
        font_color = font_cfg.get("color", "#FFFFFF")
        layout = QVBoxLayout()
        desc = QLabel(
            "이 설정 창은 키보드, 게임패드 입력이 안됩니다.\n터치 또는 마우스로 설정 해 주세요.\n\n\n배치 설정은 프로그램과 함께 기동 시킬 프로그램을 설정합니다.\n(예: Lossless Scaling, JoyToKey, 각종 애드온 및 트레이너 등)\n여기에 프로그램을 설정 해 두면 게임 기동시 설정된 타이머 시간 간격으로 차례로 프로그램이 실행 됩니다.\n\n아래와 같은 순서로 동작 합니다.\n게임실행->타이머 대기->배치1 실행->타이머 대기->배치2 실행->타이머 대기..."
        )
        desc.setWordWrap(True)
        desc.setFont(font_big)
        desc.setStyleSheet(f"color: {font_color};")
        layout.addWidget(desc)
        timer_layout = QHBoxLayout()
        timer_label = QLabel("배치 타이머:")
        timer_label.setFont(font_big)
        timer_label.setStyleSheet(f"color: {font_color};")
        timer_layout.addWidget(timer_label)
        self.timer_dropdown = QComboBox()
        self.timer_dropdown.setFont(font_big)
        self.timer_dropdown.setStyleSheet(f"color: {font_color};")
        self.timer_dropdown.setFixedHeight(self.theme_manager.scale_px(60))
        self.timer_dropdown.addItems([f"{i}초" for i in range(1, 61)])
        timer_layout.addWidget(self.timer_dropdown)
        layout.addLayout(timer_layout)
        self.program_inputs = []
        for i in range(3):
            program_layout = QHBoxLayout()
            label = QLabel(f"배치 프로그램 {i + 1}:")
            label.setFont(font_big)
            label.setStyleSheet(f"color: {font_color};")
            program_layout.addWidget(label)
            line_edit = QLineEdit()
            line_edit.setFont(font_big)
            line_edit.setStyleSheet(f"color: {font_color};")
            line_edit.setFixedHeight(self.theme_manager.scale_px(60))
            program_layout.addWidget(line_edit)
            self.program_inputs.append(line_edit)
            browse_btn = QPushButton("찾아보기")
            browse_btn.setFont(font_big)
            browse_btn.setStyleSheet(f"color: {font_color};")
            browse_btn.setFixedSize(
                self.theme_manager.scale_px(200), self.theme_manager.scale_px(60)
            )
            delete_btn = QPushButton("삭제")
            delete_btn.setFont(font_big)
            delete_btn.setStyleSheet(f"color: {font_color};")
            delete_btn.setFixedSize(
                self.theme_manager.scale_px(150), self.theme_manager.scale_px(60)
            )
            index = i
            browse_btn.clicked.connect(lambda _, idx=index: self.browse_program(idx))
            delete_btn.clicked.connect(lambda _, idx=index: self.clear_program(idx))
            program_layout.addWidget(browse_btn)
            program_layout.addWidget(delete_btn)
            layout.addLayout(program_layout)
        save_btn = QPushButton("저장")
        save_btn.setFont(font_big)
        save_btn.setStyleSheet(f"color: {font_color};")
        save_btn.setFixedHeight(self.theme_manager.scale_px(70))
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        self.setLayout(layout)

    def browse_program(self, index):
        (file_path, _) = QFileDialog.getOpenFileName(
            self,
            "실행 파일 선택",
            self.last_dir,
            "Executable Files (*.exe *.bat *.cmd)",
        )
        if file_path:
            self.program_inputs[index].setText(file_path)
            self.last_dir = os.path.dirname(file_path)

    def clear_program(self, index):
        self.program_inputs[index].clear()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    delay = data.get("delay_seconds", 3)
                    apps = data.get("apps", [])
                    self.timer_dropdown.setCurrentIndex(min(max(delay - 1, 0), 59))
                    for i in range(min(3, len(apps))):
                        self.program_inputs[i].setText(apps[i])
            except Exception as e:
                self.show_big_message(
                    "불러오기 실패",
                    f"설정 파일을 불러오는 중 오류가 발생했습니다.\n{e}",
                )

    def save_config(self):
        delay = self.timer_dropdown.currentIndex() + 1
        apps = [
            inp.text().strip()
            for inp in self.program_inputs
            if inp.isEnabled() and inp.text().strip()
        ]
        data = {"delay_seconds": delay, "apps": apps}
        try:
            os.makedirs("configs", exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.show_big_message("저장 완료", "배치 실행 설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            self.show_big_message("저장 실패", f"설정 파일 저장 중 오류 발생:\n{e}")

    def show_big_message(self, title, message):
        dlg = CustomAlertDialog(title, message, self.theme_manager, self)
        dlg.exec()

    def closeEvent(self, event):
        super().closeEvent(event)
