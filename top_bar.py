"""프로필 진입점과 시계·배터리·연결 상태를 표시하는 상단 바.
주기적 표시 갱신과 사용자 입력을 처리한다. 네트워크 아이콘은 인터넷 접근 성공을 보증하지 않는다.
"""

import os
import subprocess
import re
import psutil
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QBrush, QPen, QColor
from PySide6.QtCore import QSize, Qt, QTime, QTimer, QEvent
from settings_popup import SettingsPopup
from popup_loading_launcher import launch_popup_with_loading


class TopBar(QWidget):
    def __init__(self, theme_manager, main_widget):
        super().__init__()
        self.layout = QHBoxLayout()
        self.theme_manager = theme_manager
        self.main_widget = main_widget
        self.central_content = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setup_ui()

    def update_button_styles(self):
        if self.central_content:
            border_color = self.theme_manager.get("focus.top.border_color", "orange")
            border_width = self.theme_manager.get("focus.top.border_width", 4)
            self.btn_profile.setStyleSheet(
                f"border: {border_width}px solid {border_color}; background: transparent;"
                if self.central_content._focus_area == "top"
                else "border: none; background: transparent;"
            )

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_Return
            and self.central_content
            and (self.central_content._focus_area == "top")
        ):
            launch_popup_with_loading(SettingsPopup, parent=self.main_widget)
            return
        if event.key() == Qt.Key_S and self.central_content:
            self.central_content._focus_area = "card"
            self.clearFocus()
            self.setFocusPolicy(Qt.NoFocus)
            self.central_content.setFocus(Qt.OtherFocusReason)
            self.central_content.render_cards()
            self.update_button_styles()

    def eventFilter(self, watched, event):
        if watched == self.btn_profile and event.type() == QEvent.KeyPress:
            if (
                event.key() == Qt.Key_Return
                and self.central_content
                and (self.central_content._focus_area == "top")
            ):
                launch_popup_with_loading(SettingsPopup, parent=self.main_widget)
                return True
            if event.key() == Qt.Key_S and self.central_content:
                self.central_content._focus_area = "card"
                self.central_content.setFocus(Qt.OtherFocusReason)
                self.central_content.render_cards()
                self.update_button_styles()
                return True
        return super().eventFilter(watched, event)

    def setup_ui(self):
        background_color = self.theme_manager.get(
            "background.top_bar.value", "transparent"
        )
        self.setStyleSheet(f"background-color: {background_color};")
        self.layout.addSpacing(self.theme_manager.scale_px(40))
        self.btn_profile = QPushButton()
        self.btn_profile.setStyleSheet("background: transparent; border: none;")
        self.btn_profile.setFixedSize(
            self.theme_manager.scale_px(80), self.theme_manager.scale_px(80)
        )
        self.btn_profile.setIconSize(
            QSize(self.theme_manager.scale_px(80), self.theme_manager.scale_px(80))
        )
        self.btn_profile.clicked.connect(self.open_settings)
        self.set_profile_icon(None)
        self.layout.addWidget(self.btn_profile)
        time_color = self.theme_manager.get("fonts.시간.color", "#FFFFFF")
        wifi_color = self.theme_manager.get("fonts.와이파이.color", "#FFFFFF")
        battery_color = self.theme_manager.get("fonts.배터리.color", "#FFFFFF")
        main_bg_color = self.theme_manager.get("background.main.value", "#555555")
        time_font = self._get_font_from_theme("시간", "맑은 고딕", 40)
        self.label_time = QLabel()
        palette = self.label_time.palette()
        palette.setColor(self.label_time.foregroundRole(), QColor(time_color))
        self.label_time.setPalette(palette)
        self.label_time.setFont(time_font)
        self.label_time.setStyleSheet(f"background-color: {main_bg_color};")
        wifi_font = self._get_font_from_theme("와이파이", "맑은 고딕", 40)
        self.label_wifi = QLabel("📡")
        palette = self.label_wifi.palette()
        palette.setColor(self.label_wifi.foregroundRole(), QColor(wifi_color))
        self.label_wifi.setPalette(palette)
        self.label_wifi.setFont(wifi_font)
        self.label_wifi.setStyleSheet(f"background-color: {main_bg_color};")
        battery_font = self._get_font_from_theme("배터리", "맑은 고딕", 30)
        self.battery_icon = QLabel("🔋")
        palette = self.battery_icon.palette()
        palette.setColor(self.battery_icon.foregroundRole(), QColor(battery_color))
        self.battery_icon.setPalette(palette)
        self.battery_icon.setFont(battery_font)
        self.battery_icon.setStyleSheet(f"background-color: {main_bg_color};")
        battery_font = self._get_font_from_theme("배터리", "맑은 고딕", 30)
        self.battery_text = QLabel("100%")
        palette = self.battery_text.palette()
        palette.setColor(self.battery_text.foregroundRole(), QColor(battery_color))
        self.battery_text.setPalette(palette)
        self.battery_text.setFont(battery_font)
        self.battery_text.setStyleSheet(f"background-color: {main_bg_color};")
        right_layout = QHBoxLayout()
        right_layout.addWidget(self.label_time)
        right_layout.addSpacing(self.theme_manager.scale_px(20))
        right_layout.addWidget(self.label_wifi)
        right_layout.addSpacing(self.theme_manager.scale_px(20))
        battery_layout = QHBoxLayout()
        battery_layout.addWidget(self.battery_icon)
        battery_layout.addWidget(self.battery_text)
        right_layout.addLayout(battery_layout)
        right_layout.setAlignment(Qt.AlignRight)
        self.layout.addLayout(right_layout)
        self.layout.addSpacing(self.theme_manager.scale_px(50))
        self.setLayout(self.layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self.update_network_status)
        self.network_timer.start(30000)
        self.update_network_status()
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(10000)
        self.update_battery_status()
        self.btn_profile.setFocusPolicy(Qt.StrongFocus)
        self.btn_profile.installEventFilter(self)

    def _get_font_from_theme(self, key, default_family, default_size):
        f = self.theme_manager.get("fonts." + key, {})
        font = QFont(f.get("family", default_family), f.get("size", default_size))
        font.setBold(f.get("bold", True))
        font.setItalic(f.get("italic", False))
        return font

    def set_profile_icon(self, image_path: str | None):
        """로컬 프로필 이미지가 있으면 사용하고 없으면 테마 기본 이미지를 사용한다. 공개본에서는 계정 서버에 요청하지 않는다."""
        default_path = self.theme_manager.get(
            "icons.default_profile", "icons/default_profile.png"
        )
        profile_path = os.path.join("user", "profile_image", "user_profile.jpg")
        if not image_path:
            image_path = profile_path if os.path.exists(profile_path) else default_path
        if not os.path.exists(image_path):
            image_path = default_path
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            pixmap = QPixmap(
                self.theme_manager.scale_px(80), self.theme_manager.scale_px(80)
            )
            pixmap.fill(Qt.transparent)
        size = 80
        pixmap = pixmap.scaled(
            size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        rounded = QPixmap(size, size)
        rounded.fill(Qt.transparent)
        border_color = self.theme_manager.get("fonts.시간.color", "#000000")
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(pixmap))
        painter.setPen(QPen(QColor(border_color), 2))
        painter.drawEllipse(1, 1, size - 2, size - 2)
        painter.end()
        self.btn_profile.setIcon(QIcon(rounded))

    def open_settings(self):
        launch_popup_with_loading(SettingsPopup, parent=self.main_widget)

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm")
        self.label_time.setText(current_time)

    def update_battery_status(self):
        """배터리 정보를 아이콘·백분율로 표시한다. 배터리 없는 데스크톱도 처리한다."""
        battery = psutil.sensors_battery()
        if battery is None:
            percent = 100
            charging = True
        else:
            percent = int(battery.percent)
            charging = battery.power_plugged
        self.battery_text.setText(f"{percent}%")
        if charging:
            if percent <= 30:
                key = "icons.batt_c30"
            elif percent <= 70:
                key = "icons.batt_c70"
            else:
                key = "icons.batt_c100"
        elif percent <= 3:
            key = "icons.batt0"
        elif percent <= 10:
            key = "icons.batt10"
        elif percent <= 30:
            key = "icons.batt30"
        elif percent <= 59:
            key = "icons.batt60"
        elif percent <= 89:
            key = "icons.batt90"
        else:
            key = "icons.batt100"
        icon_path = self.theme_manager.get(key, "icons/battery.png")
        scaled = self.theme_manager.scale_px(80)
        self.battery_icon.setPixmap(
            QPixmap(icon_path).scaled(scaled, scaled, Qt.KeepAspectRatio)
        )

    def get_wifi_signal_strength(self):
        """netsh의 지역화된 출력에서 신호 세기를 읽는다. 운영체제 언어·출력 형식 의존성을 가진 부분이다."""
        command = "netsh wlan show interfaces"
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            try:
                output = result.stdout.decode("utf-8")
            except UnicodeDecodeError:
                output = result.stdout.decode("cp949", errors="replace")
            for line in output.splitlines():
                if "Signal" in line or "신호" in line:
                    match = re.search("(Signal|신호)\\s*[:：]?\\s*(\\d+)", line)
                    if match:
                        strength = int(match.group(2))
                        return strength
            return None
        except Exception:
            return None

    def get_wifi_icon_from_signal(self, strength):
        if strength >= 90:
            return self.theme_manager.get("icons.wifi90", "icons/wifi90.png")
        elif strength >= 65:
            return self.theme_manager.get("icons.wifi65", "icons/wifi65.png")
        elif strength >= 40:
            return self.theme_manager.get("icons.wifi40", "icons/wifi40.png")
        elif strength >= 15:
            return self.theme_manager.get("icons.wifi15", "icons/wifi15.png")
        else:
            return self.theme_manager.get("icons.wifi0", "icons/wifi0.png")

    def update_network_status(self):
        """인터페이스 이름과 활성 상태로 유선·무선 아이콘을 고른다. 링크 활성은 인터넷이나 로그인 서버 접속 성공을 의미하지 않는다."""
        active_ifaces = [
            iface for (iface, stats) in psutil.net_if_stats().items() if stats.isup
        ]
        ethernet_keywords = ["ethernet", "이더넷", "lan"]
        wifi_keywords = ["wi-fi", "wlan", "무선"]
        ethernet_connected = any(
            (
                any((k in iface.lower() for k in ethernet_keywords))
                for iface in active_ifaces
            )
        )
        wifi_connected = any(
            (
                any((k in iface.lower() for k in wifi_keywords))
                for iface in active_ifaces
            )
        )
        scaled = self.theme_manager.scale_px(80)
        if ethernet_connected:
            icon_path = self.theme_manager.get("icons.ethernet", "icons/ethernet.png")
            self.label_wifi.setPixmap(
                QPixmap(icon_path).scaled(scaled, scaled, Qt.KeepAspectRatio)
            )
        elif wifi_connected:
            strength = self.get_wifi_signal_strength()
            if strength is not None:
                icon = QIcon(self.get_wifi_icon_from_signal(strength))
                self.label_wifi.setPixmap(icon.pixmap(scaled, scaled))
            else:
                fallback = QPixmap(
                    self.theme_manager.get("icons.wifi0", "icons/wifi0.png")
                ).scaled(scaled, scaled, Qt.KeepAspectRatio)
                self.label_wifi.setPixmap(fallback)
        else:
            fallback = QPixmap(
                self.theme_manager.get("icons.wifi0", "icons/wifi0.png")
            ).scaled(scaled, scaled, Qt.KeepAspectRatio)
            self.label_wifi.setPixmap(fallback)
