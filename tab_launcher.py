"""실행 옵션·테마·패드·라이브러리 초기화 등 로컬 설정 탭.
설정 파일 저장과 재시작/시작프로그램 등록 같은 OS 동작을 구분해서 읽는다.
"""

import logging
import os
import sys
import pythoncom
import webbrowser
import json
import shutil
import subprocess
import time
from popup_alert import CustomAlertDialog
from win32com.client import Dispatch
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QScrollArea,
    QDialog,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt, QTimer
from notification_manager import notification_manager
from popup_utils import ConfirmDialog


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


def set_startup_enabled(enable: bool, shortcut_name: str, exe_path: str):
    """Windows 시작프로그램 폴더에 바로가기를 생성하거나 제거한다. 실행 파일 자체를 복사하는 동작은 아니다."""
    startup_dir = os.path.join(
        os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    )
    shortcut_path = os.path.join(startup_dir, f"{shortcut_name}.lnk")
    if enable:
        pythoncom.CoInitialize()
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.WindowStyle = 1
        shortcut.IconLocation = exe_path
        shortcut.Save()
    elif os.path.exists(shortcut_path):
        os.remove(shortcut_path)


def build_launcher_tab(theme_manager):
    scale_px = theme_manager.scale_px
    config_path = os.path.join("configs", "l_config.json")
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except:
                pass
    launch_on_startup_value = config.get("launch_on_startup", False)
    tab = QWidget()
    tab.theme_manager = theme_manager
    main_layout = QHBoxLayout(tab)
    main_layout.setContentsMargins(
        scale_px(40), scale_px(40), scale_px(40), scale_px(40)
    )
    main_layout.setSpacing(scale_px(40))
    left_section = QVBoxLayout()
    left_section.setSpacing(scale_px(20))

    def apply_border_theme(widget):
        f = theme_manager.get("fonts.팝업라벨", {})
        color = f.get("color", "#FFFFFF")
        size = f.get("size", 22)
        family = f.get("family", "맑은 고딕")
        bold = f.get("bold", False)
        weight = "bold" if bold else "normal"
        widget.setStyleSheet(
            f"font-size: {size}px; color: {color}; font-family: '{family}'; font-weight: {weight};border: 2px solid {color};"
        )

    def apply_popup_label_style(widget):
        f = theme_manager.get("fonts.팝업라벨", {})
        color = f.get("color", "#FFFFFF")
        size = f.get("size", 22)
        family = f.get("family", "맑은 고딕")
        bold = f.get("bold", False)
        weight = "bold" if bold else "normal"
        widget.setStyleSheet(
            f"font-size: {size}px; color: {color}; font-family: '{family}'; font-weight: {weight};border: none;"
        )

    def setting_row(label_text, widget):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(scale_px(350))
        apply_popup_label_style(label)
        widget.setFixedSize(scale_px(180), scale_px(60))
        row.addWidget(label)
        row.addWidget(widget)
        row.addStretch()
        return row

    def build_toggle_button(checked=True, enabled=True):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setText("")
        btn.setFixedSize(scale_px(180), scale_px(60))
        btn.setIconSize(QSize(scale_px(180), scale_px(60)))
        btn.setStyleSheet("border: none; padding: 0px; background: transparent;")
        btn.setEnabled(enabled)
        btn.setChecked(checked)
        icon_path = theme_manager.get(
            "icons.tgbutton_on" if checked else "icons.tgbutton_off"
        )
        btn.setIcon(QIcon(icon_path))
        btn.toggled.connect(
            lambda state: btn.setIcon(
                QIcon(
                    theme_manager.get(
                        "icons.tgbutton_on" if state else "icons.tgbutton_off"
                    )
                )
            )
        )
        return btn

    startup_btn = build_toggle_button(checked=launch_on_startup_value)
    startup_btn.toggled.connect(
        lambda checked: (
            set_startup_enabled(checked, "PiggyLauncher", sys.executable),
            save_config_value("launch_on_startup", checked),
        )
    )
    left_section.addLayout(setting_row("윈도우 시작 시 자동 실행", startup_btn))
    theme_combo = QComboBox()
    theme_combo.setFixedSize(scale_px(180), scale_px(60))
    f = theme_manager.get("fonts.팝업라벨", {})
    font_color = f.get("color", "#FFFFFF")
    font_size = f.get("size", 22)
    font_family = f.get("family", "맑은 고딕")
    font_weight = "bold" if f.get("bold", False) else "normal"
    popup_font_size = int(font_size * 1.5)
    bg_color = theme_manager.get("background.popup.value", "#222222")
    theme_combo.setStyleSheet(
        f"\n        QComboBox {{\n            background-color: {bg_color};\n            color: {font_color};\n            font-size: {font_size}px;\n            font-family: '{font_family}';\n            font-weight: {font_weight};\n            border: 2px solid white;\n        }}\n        QComboBox QAbstractItemView {{\n            background-color: {bg_color};\n        }}\n        QComboBox QListView::item {{\n            color: {font_color};\n            font-size: {popup_font_size}px;\n            font-family: '{font_family}';\n            font-weight: {font_weight};\n            height: {int(popup_font_size * 2)}px;\n        }}\n        QComboBox QListView::item:selected {{\n            background-color: #444444;\n        }}\n    "
    )
    theme_dir = os.path.join(os.getcwd(), "theme")
    if os.path.exists(theme_dir):
        selected_theme = config.get("theme")
        for name in os.listdir(theme_dir):
            folder_path = os.path.join(theme_dir, name)
            if os.path.isdir(folder_path) and os.path.exists(
                os.path.join(folder_path, "theme.json")
            ):
                theme_combo.addItem(name)
                if name == selected_theme:
                    theme_combo.setCurrentText(name)
    left_section.addLayout(setting_row("테마 설정", theme_combo))

    def save_config_value(key, value):
        config_path = os.path.join("configs", "l_config.json")
        os.makedirs("configs", exist_ok=True)
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                except:
                    pass
        config[key] = value
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def apply_theme_and_restart(name):
        config_path = os.path.join("configs", "l_config.json")
        os.makedirs("configs", exist_ok=True)
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                except:
                    pass
        config["theme"] = name
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        theme_dir = os.path.join(os.getcwd(), "theme", name)
        theme_json_path = os.path.join(theme_dir, "theme.json")
        if not os.path.exists(theme_json_path):
            dlg = CustomAlertDialog(
                "테마 로드 실패",
                "선택하신 테마를 로드하는데 실패 했습니다.\n임의의 테마를 로드 합니다.",
                theme_manager,
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
        exe = os.path.abspath(sys.argv[0])
        temp_dir = get_launcher_temp_dir()
        bat_path = os.path.join(temp_dir, "restart_launcher.bat")
        bat_lines = [
            "@echo off",
            "chcp 65001 >nul",
            f'cd /d "{os.path.dirname(exe)}"',
            "echo [INFO] 런처를 재시작 합니다...",
            "timeout /T 3 /NOBREAK >nul",
            f'start "" "{exe}"',
            "timeout /T 1 >nul",
            'del /F /Q "%~f0"',
        ]
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("\n".join(bat_lines))
            subprocess.Popen(["explorer", bat_path], shell=True)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        finally:
            sys.exit(0)

    theme_combo.currentTextChanged.connect(apply_theme_and_restart)
    group_roms_value = config.get("group_roms_by_folder", True)
    group_roms_btn = build_toggle_button(checked=group_roms_value)
    group_roms_btn.toggled.connect(
        lambda checked: save_config_value("group_roms_by_folder", checked)
    )
    left_section.addLayout(setting_row("롬 리스트 폴더형식으로 보기", group_roms_btn))
    hhc_mode_value = config.get("hhc_mode_enabled", False)
    hhc_btn = build_toggle_button(checked=hhc_mode_value)

    def on_hhc_toggled(checked: bool):
        save_config_value("hhc_mode_enabled", checked)

        def _find_main_widget(w):
            p = w
            while p is not None:
                if hasattr(p, "gamepad_handler"):
                    return p
                p = p.parent()
            return None

        main_widget = _find_main_widget(tab)
        handler = getattr(main_widget, "gamepad_handler", None) if main_widget else None
        if handler and hasattr(handler, "set_hhc_mode"):
            try:
                handler.set_hhc_mode(checked)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

    hhc_btn.toggled.connect(on_hhc_toggled)
    left_section.addLayout(setting_row("HHC 사용 중", hhc_btn))
    remap_btn = QPushButton("다시 맵핑")
    remap_btn.setFixedSize(scale_px(180), scale_px(60))
    apply_popup_label_style(remap_btn)
    apply_border_theme(remap_btn)

    def open_remap_flow():
        import json, os
        import pygame
        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QLabel,
            QComboBox,
            QPushButton,
            QHBoxLayout,
        )
        from button_mapping_popup import ButtonMappingPopup

        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        devices = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            try:
                name = joy.get_name()
                guid = joy.get_guid()
            except Exception:
                name = getattr(joy, "get_name", lambda: f"Joystick {i}")()
                guid = getattr(joy, "get_guid", lambda: None)()
            devices.append((i, guid, name))
        if not devices:
            dlg = CustomAlertDialog(
                "게임패드 감지 안됨",
                "연결된 게임패드가 없습니다.",
                theme_manager,
                parent=tab,
            )
            dlg.exec()
            return
        target = None
        sel_dlg = QDialog(tab)
        sel_dlg.setWindowTitle("게임패드 선택")
        v = QVBoxLayout(sel_dlg)
        sel_dlg.setMinimumSize(scale_px(700), scale_px(420))
        v.setContentsMargins(scale_px(30), scale_px(30), scale_px(30), scale_px(30))
        v.setSpacing(scale_px(20))
        label = QLabel("재맵핑할 게임패드를 선택하세요:")
        v.addWidget(label)
        apply_popup_label_style(label)
        label.setFixedHeight(scale_px(60))
        combo = QComboBox()
        combo.setFixedHeight(scale_px(60))
        f_combo = theme_manager.get("fonts.팝업라벨", {})
        _font_color = f_combo.get("color", "#FFFFFF")
        _font_size = f_combo.get("size", 22)
        _font_family = f_combo.get("family", "맑은 고딕")
        _font_weight = "bold" if f_combo.get("bold", False) else "normal"
        _popup_item = int(_font_size * 1.25)
        combo.setStyleSheet(
            f"\n        QComboBox {{\n            color: {_font_color};\n            font-size: {_font_size}px;\n            font-family: '{_font_family}';\n            font-weight: {_font_weight};\n            border: 2px solid {_font_color};\n            background-color: transparent; /* 배경은 부모 테마 상속 */\n        }}\n        QComboBox QAbstractItemView {{\n            background-color: transparent; /* 드롭다운 배경도 상속 */\n        }}\n        QComboBox QListView::item {{\n            color: {_font_color};\n            font-size: {_popup_item}px;\n            height: {int(_popup_item * 2)}px; /* 항목 높이 확대 */\n        }}\n        QComboBox QListView::item:selected {{\n            background-color: rgba(255,255,255,0.15);\n        }}\n        "
        )
        for idx, guid, name in devices:
            combo.addItem(f"{name}  [{guid or 'NO-GUID'}]", userData=(idx, guid, name))
        v.addWidget(combo)
        btn_row = QHBoxLayout()
        btn_confirm = QPushButton("재맵핑")
        btn_cancel = QPushButton("취소")
        apply_popup_label_style(btn_confirm)
        apply_border_theme(btn_confirm)
        apply_popup_label_style(btn_cancel)
        apply_border_theme(btn_cancel)
        btn_confirm.setFixedSize(scale_px(180), scale_px(60))
        btn_cancel.setFixedSize(scale_px(180), scale_px(60))
        btn_row.addWidget(btn_confirm)
        btn_row.setSpacing(scale_px(10))
        btn_row.addWidget(btn_cancel)
        v.addLayout(btn_row)

        def _ok():
            nonlocal target
            target = combo.currentData()
            sel_dlg.accept()

        def _cancel():
            sel_dlg.reject()

        btn_confirm.clicked.connect(_ok)
        btn_cancel.clicked.connect(_cancel)
        sel_dlg.exec()
        if not target:
            return
        (idx, guid, name) = target
        try:
            joy = pygame.joystick.Joystick(idx)
            if not joy.get_init():
                joy.init()
        except Exception:
            dlg = CustomAlertDialog(
                "오류",
                "선택한 게임패드를 초기화하는 중 오류가 발생했습니다.",
                theme_manager,
                parent=tab,
            )
            dlg.exec()
            return

        def _find_main_widget(w):
            p = w
            while p is not None:
                if hasattr(p, "gamepad_handler"):
                    return p
                p = p.parent()
            return None

        main_widget = _find_main_widget(tab)
        paused_timers = []
        candidate_timer_names = [
            "gamepad_check_timer",
            "check_new_gamepads_timer",
            "gamepad_timer",
        ]
        for nm in candidate_timer_names:
            tmr = getattr(main_widget, nm, None)
            if isinstance(tmr, QTimer):
                try:
                    paused_timers.append((tmr, tmr.interval()))
                    tmr.stop()
                except Exception:
                    pass
        handler = getattr(main_widget, "gamepad_handler", None)
        if handler:
            handler.pause_input(True)
        try:
            profile_path = os.path.join("configs", "gamepad_profiles.json")
            profiles = {}
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, "r", encoding="utf-8") as f:
                        profiles = json.load(f) or {}
                except Exception:
                    profiles = {}
            if "profiles" in profiles and isinstance(profiles["profiles"], dict):
                inner = profiles["profiles"]
            else:
                inner = profiles
            if guid and guid in inner:
                inner.pop(guid, None)
                try:
                    with open(profile_path, "w", encoding="utf-8") as f:
                        json.dump(profiles, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            if handler and hasattr(handler, "reload_profiles"):
                handler.reload_profiles()
            popup = ButtonMappingPopup(
                joy, guid, name, parent=tab, main_widget=main_widget
            )
            popup.exec()
        finally:
            for tmr, interval in paused_timers:
                try:
                    tmr.start(
                        interval if isinstance(interval, int) and interval > 0 else 2000
                    )
                except Exception:
                    try:
                        tmr.start(2000)
                    except Exception:
                        pass
            if handler:
                handler.pause_input(False)

    remap_btn.clicked.connect(open_remap_flow)
    left_section.addLayout(setting_row("게임패드 다시 맵핑", remap_btn))

    def reset_library():
        dlg = ConfirmDialog(
            "라이브러리 초기화",
            "라이브러리를 초기화하고 재시작하시겠습니까?",
            theme_manager,
        )
        if dlg.exec() == QDialog.Accepted:
            perform_library_reset()

    def perform_library_reset():
        """런처의 l_libs 등록 데이터를 삭제한다. 일반 게임 설치 경로가 아니라 이 상대 경로만 대상이며 확인은 호출부에서 받는다."""
        lib_path = os.path.join("l_libs")
        if os.path.exists(lib_path):
            try:
                shutil.rmtree(lib_path)
                time.sleep(3)
                restart_launcher()
            except Exception as e:
                notification_manager.push(f"초기화 실패: {e}")
        else:
            notification_manager.push("초기화할 라이브러리 정보가 없습니다.")

    def restart_launcher():
        """현재 프로세스가 종료된 뒤 재실행하도록 임시 배치를 만든다. 자신이 살아 있는 동안 같은 실행 파일을 교체하려는 용도가 아니다."""
        exe = os.path.abspath(sys.argv[0])
        temp_dir = get_launcher_temp_dir()
        bat_path = os.path.join(temp_dir, "restart_launcher.bat")
        bat_lines = [
            "@echo off",
            "chcp 65001 >nul",
            f'cd /d "{os.path.dirname(exe)}"',
            "echo [INFO] 런처를 재시작 합니다...",
            "timeout /T 3 /NOBREAK >nul",
            f'start "" "{exe}"',
            "timeout /T 1 >nul",
            'del /F /Q "%~f0"',
        ]
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("\n".join(bat_lines))
            subprocess.Popen(["explorer", bat_path], shell=True)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        finally:
            sys.exit(0)

    lib_reset_btn = QPushButton("초기화")
    lib_reset_btn.setFixedSize(scale_px(180), scale_px(60))
    apply_popup_label_style(lib_reset_btn)
    apply_border_theme(lib_reset_btn)
    left_section.addLayout(setting_row("라이브러리 초기화", lib_reset_btn))
    lib_reset_btn.clicked.connect(reset_library)
    wiki_btn = QPushButton("WIKI 접속")
    wiki_btn.setFixedSize(scale_px(180), scale_px(60))
    apply_popup_label_style(wiki_btn)
    apply_border_theme(wiki_btn)
    left_section.addLayout(setting_row("사용방법 확인", wiki_btn))
    wiki_btn.clicked.connect(
        lambda: webbrowser.open("https://github.com/ccs21/PiggyLauncher/wiki")
    )
    left_widget = QWidget()
    left_widget.setLayout(left_section)
    left_scroll = QScrollArea()
    left_scroll.setWidgetResizable(True)
    left_scroll.setWidget(left_widget)
    left_scroll.setStyleSheet("background-color: transparent; border: none;")
    main_layout.addWidget(left_scroll)
    right_section = QVBoxLayout()
    right_section.setSpacing(scale_px(20))
    noti_label = QLabel("알림 목록")
    f = theme_manager.get("fonts.팝업라벨", {})
    color = f.get("color", "#FFFFFF")
    size = f.get("size", 22) + 2
    family = f.get("family", "맑은 고딕")
    weight = "bold"
    noti_label.setStyleSheet(
        f"font-size: {size}px; color: {color}; font-family: '{family}'; font-weight: {weight};border: none;"
    )
    right_section.addWidget(noti_label)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet("background-color: transparent; border: none;")
    scroll_area.setFixedWidth(scale_px(700))
    scroll_area.setFixedHeight(scale_px(700))
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setSpacing(scale_px(10))
    scroll_layout.setAlignment(Qt.AlignTop)
    history_path = os.path.join("configs", "noti_history.json")
    noti_history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                noti_history = json.load(f)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    noti_history_sorted = sorted(
        noti_history, key=lambda x: x.get("received_at", ""), reverse=True
    )
    for item in noti_history_sorted:
        message = item.get("message", "메시지 없음")
        label = QLabel(message)
        label.setWordWrap(True)
        f = theme_manager.get("fonts.팝업라벨", {})
        size = f.get("size", 22)
        family = f.get("family", "맑은 고딕")
        bold = f.get("bold", False)
        weight = "bold" if bold else "normal"
        color = f.get("color", "#FFFFFF")
        label.setStyleSheet(
            f"font-size: {size}px; color: {color}; font-family: '{family}'; font-weight: {weight}; padding: {scale_px(10)}px;border: none;"
        )

        def on_label_clicked(event, item=item, label=label):
            if item.get("link"):
                webbrowser.open(item["link"])
            item["read"] = True
            label.setStyleSheet(
                f"font-size: {size}px; color: {color}; font-family: '{family}'; font-weight: {weight}; padding: {scale_px(10)}px;border: none;"
            )
            try:
                with open(history_path, "w", encoding="utf-8") as f:
                    json.dump(noti_history, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)

        label.mousePressEvent = on_label_clicked
        scroll_layout.addWidget(label)
    scroll_content.setLayout(scroll_layout)
    scroll_area.setWidget(scroll_content)
    right_section.addWidget(scroll_area)
    main_layout.addLayout(right_section)

    def cleanup():
        for child in tab.findChildren(QWidget):
            child.deleteLater()

    tab.cleanup = cleanup
    return tab
