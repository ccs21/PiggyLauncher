"""게임 실행 전에 적용할 해상도·볼륨·로케일 옵션을 편집한다.
이 화면은 프리셋을 저장하며, 실제 장치 변경과 복구는 system_config_handler에서 처리한다.
"""

import ctypes
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QSizePolicy,
    QLineEdit,
    QWidget,
    QSlider,
)
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtCore import Qt, QTimer
from system_info_util import (
    get_system_log_string,
    get_monitor_info,
    get_available_display_modes,
)
from popup_alert import CustomAlertDialog


class GraphicSettingPopup(QDialog):
    def __init__(self, platform, appid, theme_manager, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.app_id = appid
        self.theme_manager = theme_manager
        self.theme = theme_manager.theme
        self.preset_data = self.load_preset()
        self.setWindowTitle("실행 프리셋 설정")
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
            screen_width = screen.width()
            screen_height = screen.height()
            popup_w = int(screen_width * 0.8)
            popup_h = int(screen_height * 0.8)
            self.resize(popup_w, popup_h)
            self.setMaximumSize(screen_width, screen_height)
        bg_color = (
            self.theme.get("background", {}).get("popup", {}).get("value", "#FFFFFF")
        )
        self.setStyleSheet(f"background-color: {bg_color};")
        self.init_ui()

    def init_ui(self):
        label_theme = self.theme_manager.get("fonts.팝업라벨", {})
        font_big = QFont()
        font_big.setFamily(label_theme.get("family", "맑은 고딕"))
        font_big.setPointSizeF(label_theme.get("size", 22))
        font_big.setBold(label_theme.get("bold", False))
        font_color = label_theme.get("color", "#FFFFFF")
        main_layout = QVBoxLayout()

        def apply_fontcolor(widget):
            widget.setStyleSheet(f"color: {font_color};")

        title_widget = QWidget()
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(
            0, self.theme_manager.scale_px(10), 0, self.theme_manager.scale_px(10)
        )
        title_layout.setAlignment(Qt.AlignHCenter)
        title_label = QLabel(
            "고급 설정에서는 게임 실행 시 해상도 및 볼륨 변경 옵션을 제공 합니다."
        )
        title_label.setStyleSheet("border: none; padding: 10px 20px;")
        title_label.setFont(font_big)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(title_label)
        title_layout.addWidget(title_label)
        title_widget.setStyleSheet("background: transparent; border: none;")
        title_widget.setLayout(title_layout)
        main_layout.addWidget(title_widget)
        apply_fontcolor(title_widget)
        graphics_section = QVBoxLayout()
        graphics_toggle_row = QHBoxLayout()
        self.graphics_toggle = QComboBox()
        self.graphics_toggle.addItems(["적용 안 함", "적용 함"])
        self.graphics_toggle.setFont(font_big)
        self.graphics_toggle.setFixedSize(
            self.theme_manager.scale_px(200), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.graphics_toggle)
        display_label = QLabel("설정을 적용 할 디스플레이 선택")
        display_label.setFont(font_big)
        display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(display_label)
        self.display_combo = QComboBox()
        self.display_combo.setFont(font_big)
        self.display_combo.setFixedSize(
            self.theme_manager.scale_px(600), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.display_combo)
        self.monitors = get_monitor_info()
        for m in self.monitors:
            label = f"{m['id']}  [{m['model']}]"
            self.display_combo.addItem(label)
        self.display_combo.currentIndexChanged.connect(self.update_resolution_combo)
        graphics_toggle_row.addWidget(self.graphics_toggle)
        graphics_toggle_row.addWidget(display_label)
        graphics_toggle_row.addWidget(self.display_combo)
        graphics_section.addLayout(graphics_toggle_row)
        resolution_row = QHBoxLayout()
        resolution_label = QLabel("해상도")
        resolution_label.setFont(font_big)
        resolution_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(resolution_label)
        self.resolution_combo = QComboBox()
        self.resolution_combo.setFont(font_big)
        self.resolution_combo.setFixedSize(
            self.theme_manager.scale_px(600), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.resolution_combo)
        self.resolution_combo.currentIndexChanged.connect(self.update_rate_combo)
        resolution_row.addSpacing(self.theme_manager.scale_px(200))
        resolution_row.addWidget(resolution_label)
        resolution_row.addWidget(self.resolution_combo)
        graphics_section.addLayout(resolution_row)
        rate_row = QHBoxLayout()
        rate_label = QLabel("주사율")
        rate_label.setFont(font_big)
        rate_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(rate_label)
        self.rate_combo = QComboBox()
        self.rate_combo.setFont(font_big)
        self.rate_combo.setFixedSize(
            self.theme_manager.scale_px(600), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.rate_combo)
        rate_row.addSpacing(self.theme_manager.scale_px(200))
        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.rate_combo)
        graphics_section.addLayout(rate_row)
        main_layout.addLayout(graphics_section)
        main_layout.addSpacing(self.theme_manager.scale_px(20))
        volume_row = QHBoxLayout()
        self.volume_toggle = QComboBox()
        self.volume_toggle.addItems(["적용 안 함", "적용 함"])
        self.volume_toggle.setFont(font_big)
        self.volume_toggle.setFixedSize(
            self.theme_manager.scale_px(200), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.volume_toggle)
        volume_label = QLabel("게임을 실행 할 때 변경할 볼륨")
        volume_label.setFont(font_big)
        volume_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(volume_label)
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setMinimum(0)
        volume_slider.setMaximum(100)
        volume_slider.setValue(80)
        volume_slider.setTickInterval(10)
        volume_slider.setSingleStep(1)
        volume_slider.setFixedHeight(self.theme_manager.scale_px(60))
        volume_slider.setFixedWidth(self.theme_manager.scale_px(483))
        self.volume_value = QLabel("80%")
        self.volume_value.setFont(font_big)
        self.volume_value.setFixedWidth(self.theme_manager.scale_px(110))
        apply_fontcolor(self.volume_value)
        self.volume_slider = volume_slider
        volume_slider.valueChanged.connect(
            lambda val: self.volume_value.setText(f"{val}%")
        )
        volume_row.addWidget(self.volume_toggle)
        volume_row.addWidget(volume_label)
        volume_row.addWidget(volume_slider)
        volume_row.addWidget(self.volume_value)
        main_layout.addLayout(volume_row)
        main_layout.addSpacing(self.theme_manager.scale_px(20))
        locale_row = QHBoxLayout()
        self.locale_toggle = QComboBox()
        self.locale_toggle.addItems(["적용 안 함", "적용 함"])
        self.locale_toggle.setFont(font_big)
        self.locale_toggle.setFixedSize(
            self.theme_manager.scale_px(200), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.locale_toggle)
        locale_label = QLabel("로케일 에뮬레이터 사용")
        locale_label.setFont(font_big)
        locale_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        apply_fontcolor(locale_label)
        self.locale_path_edit = QLineEdit()
        self.locale_path_edit.setFont(font_big)
        self.locale_path_edit.setFixedSize(
            self.theme_manager.scale_px(483), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(self.locale_path_edit)
        locale_browse_btn = QPushButton(" 찾기 ")
        locale_browse_btn.setFont(font_big)
        locale_browse_btn.setFixedSize(
            self.theme_manager.scale_px(110), self.theme_manager.scale_px(60)
        )
        apply_fontcolor(locale_browse_btn)

        def browse_locale_path():
            from PySide6.QtWidgets import QFileDialog

            (path, _) = QFileDialog.getOpenFileName(
                self, "LEProc.exe 경로 선택", "", "실행 파일 (*.exe)"
            )
            if path:
                self.locale_path_edit.setText(path)

        locale_browse_btn.clicked.connect(browse_locale_path)
        locale_row.addWidget(self.locale_toggle)
        locale_row.addWidget(locale_label)
        locale_row.addWidget(self.locale_path_edit)
        locale_row.addWidget(locale_browse_btn)
        main_layout.addLayout(locale_row)
        main_layout.addSpacing(self.theme_manager.scale_px(20))
        log_box = QTextEdit()
        log_box.setFont(font_big)
        log_box.setReadOnly(True)
        log_box.setMinimumHeight(self.theme_manager.scale_px(200))
        apply_fontcolor(log_box)
        self.log_box = log_box
        main_layout.addWidget(log_box)
        main_layout.addSpacing(self.theme_manager.scale_px(20))
        QTimer.singleShot(0, self.defer_monitor_log)
        button_row = QHBoxLayout()
        save_btn = QPushButton("설정 저장")
        save_btn.setFont(font_big)
        save_btn.setFixedSize(
            self.theme_manager.scale_px(200), self.theme_manager.scale_px(80)
        )
        apply_fontcolor(save_btn)
        save_btn.clicked.connect(self.save_preset)
        cancel_btn = QPushButton("취소")
        cancel_btn.setFont(font_big)
        cancel_btn.setFixedSize(
            self.theme_manager.scale_px(200), self.theme_manager.scale_px(80)
        )
        apply_fontcolor(cancel_btn)
        cancel_btn.clicked.connect(self.close)
        button_row.addStretch()
        button_row.addWidget(save_btn)
        button_row.addWidget(cancel_btn)
        main_layout.addLayout(button_row)
        self.setLayout(main_layout)
        self.update_resolution_combo()
        if self.preset_data:
            self.apply_preset(self.preset_data)

    def defer_monitor_log(self):
        import traceback

        try:
            current_monitor_id = get_current_monitor_id(int(self.winId()))
            log_text = get_system_log_string()
            if current_monitor_id:
                for m in self.monitors:
                    if m["id"] == current_monitor_id:
                        insert_text = f"현재 런쳐가 실행중인 모니터 : {m['id']} [{m['model']}]\n\n"
                        log_text = log_text.replace(
                            "감지된 모니터의 갯수 :",
                            insert_text + "감지된 모니터의 갯수 :",
                        )
                        break
            self.log_box.setPlainText(log_text)
        except Exception:
            traceback.print_exc()

    def load_preset(self):
        import os, json

        filename = f"{self.platform}_{self.app_id}_preset.json"
        filepath = os.path.join("configs", filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return None
        return None

    def apply_preset(self, data):
        if data.get("resolution_enabled"):
            self.graphics_toggle.setCurrentText("적용 함")
        else:
            self.graphics_toggle.setCurrentText("적용 안 함")
        for i in range(self.display_combo.count()):
            if data.get("resolution_display") in self.display_combo.itemText(i):
                self.display_combo.setCurrentIndex(i)
                break
        res = data.get("resolution")
        rate = str(int(data.get("refresh_rate", 0)))
        for i in range(self.resolution_combo.count()):
            if self.resolution_combo.itemText(i) == res:
                self.resolution_combo.setCurrentIndex(i)
                break
        for i in range(self.rate_combo.count()):
            if self.rate_combo.itemText(i) == rate:
                self.rate_combo.setCurrentIndex(i)
                break
        if data.get("volume_enabled"):
            self.volume_toggle.setCurrentText("적용 함")
        else:
            self.volume_toggle.setCurrentText("적용 안 함")
        vol_value = int(data.get("volume", "80%")[:-1])
        self.volume_slider.setValue(vol_value)
        if data.get("locale_emulate"):
            self.locale_toggle.setCurrentText("적용 함")
        else:
            self.locale_toggle.setCurrentText("적용 안 함")
        self.locale_path_edit.setText(data.get("locale_path", ""))

    def save_preset(self):
        import os, json

        resolution_enabled = self.graphics_toggle.currentText() == "적용 함"
        resolution_display = self.display_combo.currentText().split()[0]
        resolution = self.resolution_combo.currentText()
        try:
            refresh_rate = float(self.rate_combo.currentText())
        except:
            refresh_rate = 0.0
        volume_enabled = self.volume_toggle.currentText() == "적용 함"
        volume = self.volume_value.text()
        locale_enabled = self.locale_toggle.currentText() == "적용 함"
        locale_path = self.locale_path_edit.text()
        filename = f"{self.platform}_{self.app_id}_preset.json"
        filepath = os.path.join("configs", filename)
        os.makedirs("configs", exist_ok=True)
        data = {
            "resolution_enabled": resolution_enabled,
            "resolution": resolution,
            "resolution_display": resolution_display,
            "refresh_rate": refresh_rate,
            "volume_enabled": volume_enabled,
            "volume": volume,
            "locale_emulate": locale_enabled,
            "locale_path": locale_path,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        CustomAlertDialog(
            "설정 완료", "고급 설정이 저장되었습니다.", self.theme_manager, self
        ).exec()
        self.close()

    def update_resolution_combo(self):
        current_text = self.display_combo.currentText()
        if not current_text:
            return
        display_id = current_text.split()[0]
        self.mode_map = get_available_display_modes(display_id)
        self.resolution_combo.clear()
        sorted_res = sorted(
            self.mode_map.keys(), key=lambda x: x[0] * x[1], reverse=True
        )
        for res in sorted_res:
            res_str = f"{res[0]}x{res[1]}"
            self.resolution_combo.addItem(res_str)
        self.update_rate_combo()

    def update_rate_combo(self):
        self.rate_combo.clear()
        res_text = self.resolution_combo.currentText()
        if not res_text:
            return
        (width, height) = map(int, res_text.split("x"))
        rates = self.mode_map.get((width, height), [])
        for hz in sorted(rates):
            self.rate_combo.addItem(str(hz))


def get_current_monitor_id(hwnd):

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", ctypes.c_long * 4),
            ("rcWork", ctypes.c_long * 4),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
    monitor_info = MONITORINFOEXW()
    monitor_info.cbSize = ctypes.sizeof(MONITORINFOEXW)
    if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
        return monitor_info.szDevice
    return None
