"""Qt 애플리케이션의 시작과 화면 수명 관리. 직접 실행 시에만 UI를 시작한다."""

import logging
import sys
import os
import json
import pygame
import traceback
import ctypes
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer, QEvent
from theme_manager import ThemeManager
from central_content import CentralContent
from top_bar import TopBar
from bottom_bar import BottomBar
from gamepad_handler import GamepadHandler
from button_mapping_popup import ButtonMappingPopup
from gamepad_manager import load_profiles
from notification_manager import notification_manager
from popup_alert import CustomAlertDialog
from rom_list_core_cleaner import start_cleaner_thread
import win32api
import win32con
import webbrowser
import winreg


def check_chrome_installed():
    """PATH와 Windows 등록 경로에서 Chrome 실행 파일을 찾는다. 설치나 다운로드는 하지 않는다."""
    chrome_path = shutil.which("chrome") or shutil.which("chrome.exe")
    if chrome_path:
        return chrome_path
    reg_paths = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe",
        ),
    ]
    for hive, key in reg_paths:
        try:
            with winreg.OpenKey(hive, key) as regkey:
                (chrome_path, _) = winreg.QueryValueEx(regkey, "")
                if os.path.exists(chrome_path):
                    return chrome_path
        except FileNotFoundError:
            continue
    return None


main_launcher = None


def get_current_monitor_id(hwnd):
    """Win32 모니터 핸들을 디스플레이 이름으로 바꾼다. ctypes 구조체 필드 순서는 Windows ABI와 같아야 한다."""

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", ctypes.c_long * 4),
            ("rcWork", ctypes.c_long * 4),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
    info = MONITORINFOEXW()
    info.cbSize = ctypes.sizeof(MONITORINFOEXW)
    if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return info.szDevice
    return None


def get_monitor_scale(hwnd):
    """창이 속한 모니터의 DPI를 읽어 배율로 바꾼다. API 사용 불가 시 기본 배율을 사용한다."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass
    monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
    dpiX = ctypes.c_uint()
    dpiY = ctypes.c_uint()
    if (
        ctypes.windll.shcore.GetDpiForMonitor(
            monitor, 0, ctypes.byref(dpiX), ctypes.byref(dpiY)
        )
        == 0
    ):
        return dpiX.value / 96
    return 1.0


def get_monitor_resolution(hwnd):
    """작업 표시줄을 뺀 작업 영역이 아닌 모니터 전체 사각형에서 너비·높이를 얻는다."""
    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
    monitor_info = win32api.GetMonitorInfo(monitor)
    rect = monitor_info["Monitor"]
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    return (width, height)


class SplashWindow(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        label = QLabel(self)
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setGeometry(0, 0, self.width(), self.height())
        self.showFullScreen()

    def resizeEvent(self, event):
        self.findChild(QLabel).setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)


class PiggyLauncher(QMainWindow):
    def __init__(self, theme_manager):
        super().__init__()
        self.setWindowTitle("Piggy Launcher")
        self.setObjectName("PiggyLauncher")
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.theme_manager = theme_manager
        bg_color = self.theme_manager.get("background.main")
        if isinstance(bg_color, dict):
            color_value = bg_color.get("value", "#000000")
            self.setStyleSheet(f"background-color: {color_value};")
        self.main_widget = self
        self.is_game_running = False
        self.top_bar = TopBar(self.theme_manager, self.main_widget)
        self.bottom_bar = BottomBar(self.theme_manager)
        self.init_ui()
        QTimer.singleShot(100, self.start_gamepad_handling)

    def init_ui(self):
        """상단·중앙·하단 위젯을 조립하고 서로의 탐색 대상을 연결한다. 각 위젯의 소유자는 메인 창이다."""
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        self.central_content = CentralContent(
            self.theme_manager,
            btn_profile=self.top_bar.btn_profile,
            btn_update=self.bottom_bar.btn_update,
            bottom_bar=self.bottom_bar,
        )
        self.central_content.main_widget = self
        self.top_bar.central_content = self.central_content
        self.bottom_bar.central_content = self.central_content
        main_layout.addWidget(self.top_bar)
        main_layout.setStretch(0, 1)
        main_layout.addWidget(self.central_content)
        main_layout.setStretch(1, 7)
        main_layout.addWidget(self.bottom_bar)
        main_layout.setStretch(2, 1)
        self.setCentralWidget(central_widget)

    def start_gamepad_handling(self):
        """패드 입력 처리기와 신규 연결 확인 타이머를 준비한다. GUI 수명과 입력 처리기의 수명을 맞춘다."""
        self.gamepad_handler = GamepadHandler(
            self, self.central_content, self.theme_manager
        )
        self.seen_guids = set()
        self.gamepad_check_timer = QTimer(self)
        self.gamepad_check_timer.timeout.connect(self.check_new_gamepads)
        self.gamepad_check_timer.start(2000)
        self.start_mapping_for_new_pads()

    def on_guid_selected(self, joystick, guid, name):
        popup = ButtonMappingPopup(joystick, guid, name, parent=self, main_widget=self)
        popup.exec()
        self.seen_guids.add(guid)
        self.start_mapping_for_new_pads()

    def start_mapping_for_new_pads(self):
        """
        신규 연결 패드 처리:
          1) gamepad_manager에서 미등록 패드 수집
          2) SDL DB 기반 자동 맵핑 시도 (성공분은 바로 저장)
          3) 실패/미대상만 기존 GamepadConfigPopup으로 안내
        중복 팝업 방지를 위해 재진입 가드와 타이머 stop/start 처리 추가.
        """
        if not hasattr(self, "_mapping_popup_open"):
            self._mapping_popup_open = False
        if self._mapping_popup_open:
            return
        try:
            from gamepad_manager import get_unmapped_gamepads

            pads_to_map = get_unmapped_gamepads(full=True)
            len(pads_to_map) if pads_to_map else 0
            if not pads_to_map:
                return
            try:
                from sdl_automap import automap_for_devices

                mapped_guids = automap_for_devices(pads_to_map)
            except Exception:
                mapped_guids = set()
            try:
                if (
                    mapped_guids
                    and hasattr(self, "gamepad_handler")
                    and hasattr(self.gamepad_handler, "reload_profiles")
                ):
                    self.gamepad_handler.reload_profiles()
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            remaining = []
            for joystick, guid, name in pads_to_map:
                if guid not in mapped_guids:
                    remaining.append((joystick, guid, name))
            if not remaining:
                return
            self._mapping_popup_open = True
            try:
                if hasattr(self, "gamepad_check_timer"):
                    try:
                        self.gamepad_check_timer.stop()
                    except Exception:
                        pass
                if hasattr(self, "gamepad_handler") and hasattr(
                    self.gamepad_handler, "timer"
                ):
                    try:
                        self.gamepad_handler.timer.stop()
                    except Exception:
                        pass
                if hasattr(self, "notification_manager"):
                    try:
                        self.notification_manager.pause()
                    except Exception:
                        pass
                from gamepad_config_popup import GamepadConfigPopup

                popup = GamepadConfigPopup(
                    remaining, self.on_guid_selected, parent=self
                )
                popup.exec()
            finally:
                if hasattr(self, "notification_manager"):
                    try:
                        self.notification_manager.resume()
                    except Exception:
                        pass
                if hasattr(self, "gamepad_handler") and hasattr(
                    self.gamepad_handler, "timer"
                ):
                    try:
                        self.gamepad_handler.timer.start()
                    except Exception:
                        pass
                if hasattr(self, "gamepad_check_timer"):
                    try:
                        self.gamepad_check_timer.start(2000)
                    except Exception:
                        pass
                self._mapping_popup_open = False
        except Exception:
            self._mapping_popup_open = False

    def check_new_gamepads(self):
        """연결된 GUID를 저장된 매핑과 비교한다. 제품명만 같아도 GUID가 다를 수 있어 이름만으로 합치지 않는다."""
        profiles = load_profiles()
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            guid = joystick.get_guid()
            if guid not in profiles and guid not in self.seen_guids:
                self.start_mapping_for_new_pads()
                break

    def changeEvent(self, event):
        """창 상태 변경을 받는 Qt 콜백이다. 직접 호출 참조가 없어도 Qt가 호출하므로 삭제 대상이 아니다."""
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if not self.isMinimized() and self.isVisible() and self.isFullScreen():
                if hasattr(self, "central_content"):
                    try:
                        self.central_content.force_reload_all()
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )

                def _resume_notifications():
                    try:
                        notification_manager.resume()
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )

                QTimer.singleShot(2000, _resume_notifications)


if __name__ == "__main__":
    from bootstrap import prepare_workspace

    prepare_workspace(os.path.dirname(__file__))
    config = {}
    logging.basicConfig(level=logging.WARNING)
    from PySide6.QtCore import Qt

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    os.chdir(
        os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
    )
    config_path = os.path.join("configs", "l_config.json")
    theme_dir = "theme/default"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                selected_theme = config.get("theme")
                if selected_theme:
                    theme_dir = os.path.join("theme", selected_theme)
            except:
                pass
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(theme_dir, "default_profile.png")))
    try:
        start_cleaner_thread()
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    splash = SplashWindow(os.path.join(theme_dir, "default_profile.png"))
    app.processEvents()
    dummy_window = QMainWindow()
    dummy_window.showFullScreen()
    app.processEvents()
    hwnd = int(dummy_window.winId())
    scale = get_monitor_scale(hwnd)
    resolution = get_monitor_resolution(hwnd)
    monitor_id = get_current_monitor_id(hwnd)
    dpi = int(scale * 96)
    from theme_manager import ThemeManager

    try:
        theme_manager = ThemeManager(theme_dir, scale=scale, resolution=resolution)
    except Exception:
        dlg = CustomAlertDialog(
            "테마 로드 실패",
            "선택하신 테마를 로드하는데 실패 했습니다.\n임의의 테마를 로드 합니다.",
            ThemeManager("theme/default", scale=scale),
        )
        dlg.exec()
        fallback_theme = None
        theme_root = os.path.join(os.getcwd(), "theme")
        for folder_name in sorted(os.listdir(theme_root)):
            candidate_path = os.path.join(theme_root, folder_name, "theme.json")
            if os.path.exists(candidate_path):
                fallback_theme = folder_name
                break
        if fallback_theme:
            config["theme"] = fallback_theme
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            theme_dir = os.path.join("theme", fallback_theme)
            theme_manager = ThemeManager(theme_dir, scale=scale)
    dummy_window.close()

    def show_launcher():
        """시작 안내 이후 메인 창을 만들고 전역 참조로 유지한다. 지역 변수만 남기면 창 수명이 끝날 수 있다."""
        global main_launcher
        main_launcher = PiggyLauncher(theme_manager=theme_manager)
        main_launcher.show()
        splash.close()
        check_chrome_installed()
        if not check_chrome_installed():
            dlg = CustomAlertDialog(
                "Chrome 브라우저 필요",
                "이 프로그램은 일부 기능을 위해 Chrome 브라우저가 필요합니다.\n\nChrome을 설치 해 주세요.\n\n확인을 누르면 Chrome 다운로드 페이지로 연결 됩니다.",
                theme_manager,
                parent=main_launcher,
            )
            result = dlg.exec()
            if result == 1:
                webbrowser.open("https://www.google.com/chrome/")

    QTimer.singleShot(3000, show_launcher)
    try:
        app.exec()
    except Exception as e:
        tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write("[🧨] Qt 실행 루프 예외:\n")
            f.write("".join(tb_lines))
