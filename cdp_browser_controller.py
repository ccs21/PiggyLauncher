"""Classic 수집에 사용하는 별도 Chrome 프로필과 프로세스를 관리한다.
브라우저 시작·최소화·종료는 DOM 읽기와 별도 책임이다. 디버깅 포트와 프로필은 로컬 개발 자원이다.
"""

import logging
import os
import subprocess
import time
import winreg
import psutil
import threading
import win32gui
import win32con
import win32process

CDP_PORT = 9222
PROFILE_BASE = "chrome_profile"


def get_chrome_path():
    possible_keys = [
        (
            winreg.HKEY_CURRENT_USER,
            "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\Google Chrome",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\Google Chrome",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            "Software\\\\WOW6432Node\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\Google Chrome",
        ),
    ]
    for hive, path in possible_keys:
        try:
            with winreg.OpenKey(hive, path) as key:
                (install_path, _) = winreg.QueryValueEx(key, "InstallLocation")
                chrome_path = os.path.join(install_path, "chrome.exe")
                if os.path.exists(chrome_path):
                    return chrome_path
        except FileNotFoundError:
            continue
    return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"


def launch_browser(
    url, profile_name="Default", headless=False, minimized=False, use_app_mode=True
):
    chrome_path = get_chrome_path()
    user_data_dir = os.path.abspath(os.path.join(PROFILE_BASE, profile_name))
    os.makedirs(user_data_dir, exist_ok=True)
    args = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=TouchUI",
        "--lang=ko-KR",
        f"--app={url}" if use_app_mode else url,
        "--window-size=1280,800",
        "--window-position=200,100",
    ]
    if headless:
        args.append("--headless=new")
    elif minimized:
        args.append("--window-position=0,10000")
        args.append("--start-minimized")
    proc = subprocess.Popen(args)
    if minimized:

        def wait_and_minimize_chrome_by_pid(target_pid, max_wait=15.0, interval=0.1):
            start_time = time.time()
            while time.time() - start_time < max_wait:

                def enum_handler(hwnd, result_list):
                    try:
                        (_, pid) = win32process.GetWindowThreadProcessId(hwnd)
                        if pid == target_pid and win32gui.IsWindowVisible(hwnd):
                            result_list.append(hwnd)
                    except Exception:
                        pass

                found = []
                win32gui.EnumWindows(enum_handler, found)
                if found:
                    for hwnd in found:
                        try:

                            def force_minimize(hwnd, retries=3):
                                for i in range(retries):
                                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                                    time.sleep(0.2)
                                    if win32gui.IsIconic(hwnd):
                                        return True
                                return False

                            force_minimize(hwnd)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                    return
                time.sleep(interval)

        threading.Thread(
            target=wait_and_minimize_chrome_by_pid, args=(proc.pid,), daemon=True
        ).start()


def kill_all_cdp_chrome():
    try:
        count = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if "chrome.exe" in proc.info["name"].lower():
                    cmdline = (
                        " ".join(proc.info.get("cmdline", []))
                        if proc.info.get("cmdline")
                        else ""
                    )
                    if (
                        "--remote-debugging-port" in cmdline
                        or "chrome_profile" in cmdline
                    ):
                        proc.kill()
                        count += 1
            except Exception:
                continue
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)


def kill_all_chrome():
    count = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if "chrome.exe" in proc.info["name"].lower():
                proc.kill()
                count += 1
        except Exception:
            continue
