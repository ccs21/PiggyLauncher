"""에뮬레이터 실행, 임시 배치파일과 종료 감시. 실행은 파일과 프로세스에 영향을 준다."""

import logging
import os
import subprocess
import sys
import time
import threading
import psutil


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


def launch_game(core_type, core, emulator_path, rom_path, bat_path):
    """RA 또는 SA 실행 명령과 작업 폴더를 구성해 실행한다.
    RA는 코어 DLL과 ROM 경로를 전달하고 SA는 실행기별 명령 규칙을 따른다.
    Classic의 임시 배치 방식은 상대 경로·작업 디렉터리 의존성을 맞추기 위한 선택이다.
    프로세스 실행 성공과 게임 부팅 성공은 다르므로 호출부의 시작 감시가 추가로 필요하다.
    """
    if core_type == "RA":
        core_name = f"{core}_libretro.dll"
        core_path = os.path.join(os.path.dirname(emulator_path), "cores", core_name)
        cmd = f'"{emulator_path}" -L "{core_path}" "{rom_path}"'
    elif core_type == "SA":
        core = core.lower()
        if "xemu" in core:
            emulator_dir = os.path.dirname(emulator_path)
            log_path = os.path.join(emulator_dir, "xemu.log")

            def _clean_path_candidate(p: str) -> str:
                """로그에서 뽑은 경로 후보를 exists 검사에 적합하게 정리"""
                if not p:
                    return p
                p = p.strip()
                p = p.strip('"').strip("'")
                p = p.rstrip(")],;")
                p = p.rstrip('"').rstrip("'").rstrip(")")
                return p.strip()

            def _extract_xemu_toml_path_from_log(log_file):
                """xemu.log에서 xemu.toml 절대경로를 최대한 안정적으로 추출합니다."""
                if not os.path.exists(log_file):
                    return None
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    return None
                key = "xemu_settings_get_path: config path:"
                for line in lines:
                    if key in line:
                        tail = line.split(key, 1)[1].strip()
                        tail = _clean_path_candidate(tail)
                        if (
                            tail
                            and tail.lower().endswith("xemu.toml")
                            and os.path.exists(tail)
                        ):
                            return tail
                import re

                win_re = re.compile(
                    "([A-Za-z]:\\\\[^\\r\\n\\\"']*xemu\\.toml)", re.IGNORECASE
                )
                unix_re = re.compile(
                    "([A-Za-z]:/[^\\r\\n\\\"']*xemu\\.toml)", re.IGNORECASE
                )
                candidates = []
                for line in lines:
                    low = line.lower()
                    if "xemu.toml" not in low:
                        continue
                    for m in win_re.finditer(line):
                        candidates.append(_clean_path_candidate(m.group(1)))
                    for m in unix_re.finditer(line):
                        cand = _clean_path_candidate(m.group(1)).replace("/", "\\")
                        candidates.append(cand)
                    idx = low.find("xemu.toml")
                    if idx != -1:
                        end = idx + len("xemu.toml")
                        prefix = line[:end]
                        m2 = re.search("([A-Za-z]:[\\\\/])", prefix)
                        if m2:
                            starts = [
                                m.start()
                                for m in re.finditer("[A-Za-z]:[\\\\/]", prefix)
                            ]
                            if starts:
                                start = starts[-1]
                                cand = _clean_path_candidate(prefix[start:end]).replace(
                                    "/", "\\"
                                )
                                candidates.append(cand)
                seen = set()
                for c in candidates:
                    if not c:
                        continue
                    cl = c.lower()
                    if cl in seen:
                        continue
                    seen.add(cl)
                    if os.path.exists(c):
                        return c
                return None

            def _update_xemu_dvd_path(toml_file, iso_path):
                """xemu.toml의 [sys.files] dvd_path를 iso_path로 갱신합니다."""
                if not os.path.exists(toml_file):
                    return False
                try:
                    with open(toml_file, "r", encoding="utf-8", errors="ignore") as f:
                        s = f.read()
                except Exception:
                    return False
                iso_path = iso_path.replace("/", "\\").strip()
                iso_path = iso_path.strip().strip('"')
                iso_path = iso_path.replace('"', "")
                safe_iso = iso_path.replace("'", "\\'")
                new_line = f"dvd_path = '{safe_iso}'"
                import re

                dvd_re = re.compile("(?m)^\\s*dvd_path\\s*=\\s*.*\\s*$")
                if dvd_re.search(s):
                    s2 = dvd_re.sub(lambda _m: new_line, s, count=1)
                else:
                    sec_re = re.compile("(?m)^\\[sys\\.files\\]\\s*$")
                    m = sec_re.search(s)
                    if not m:
                        return False
                    insert_pos = m.end()
                    s2 = s[:insert_pos] + "\n" + new_line + s[insert_pos:]
                try:
                    with open(toml_file, "w", encoding="utf-8") as f:
                        f.write(s2)
                    return True
                except Exception:
                    return False

            toml_path = _extract_xemu_toml_path_from_log(log_path)
            if not toml_path:
                return
            if not _update_xemu_dvd_path(toml_path, rom_path):
                return
            cmd = f'"{emulator_path}"'
        elif (
            "rpcs3" in core
            or "pcsx2" in core
            or "duckstation" in core
            or ("ryujinx" in core)
            or ("eden" in core)
        ):
            temp_dir = get_launcher_temp_dir()
            game_bat_path = os.path.join(temp_dir, "launch_emulator.bat")
            vbs_path = os.path.join(temp_dir, "launch_emulator.vbs")
            emulator_dir = os.path.dirname(emulator_path)
            rom_path = rom_path.replace("/", "\\")
            with open(game_bat_path, "w", encoding="utf-8") as f:
                f.write(
                    f'@echo off\nchcp 65001 > nul\necho 게임이 종료되면 이 창은 자동으로 닫힙니다.\ncd /d "{emulator_dir}"\n"{emulator_path}" "{rom_path}"\nexit\n'
                )
            time.sleep(0.2)
            if not os.path.exists(game_bat_path):
                return
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(
                    '\nSet fso = CreateObject("Scripting.FileSystemObject")\nSet WshShell = CreateObject("WScript.Shell")\ncurrentDir = fso.GetParentFolderName(WScript.ScriptFullName)\nWshShell.CurrentDirectory = currentDir\nWshShell.Run chr(34) & "launch_emulator.bat" & Chr(34), 0\nSet WshShell = Nothing\n'
                )
            try:
                subprocess.Popen(["explorer", vbs_path], shell=True)
            except Exception:
                return

            def monitor_emulator_and_bat(bat_path_to_run):
                exe_name = os.path.basename(emulator_path).lower()
                found = False
                while not found:
                    for proc in psutil.process_iter(["name", "exe"]):
                        try:
                            if (
                                proc.info["name"]
                                and proc.info["name"].lower() == exe_name
                            ):
                                found = True
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if not found:
                        time.sleep(1)
                while True:
                    emulator_running = False
                    for proc in psutil.process_iter(["name", "pid"]):
                        try:
                            pname = proc.info["name"]
                            if pname and pname.lower() == exe_name:
                                emulator_running = True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    if not emulator_running:
                        time.sleep(2)
                        try:
                            if os.path.exists(game_bat_path):
                                os.remove(game_bat_path)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                        try:
                            if os.path.exists(vbs_path):
                                os.remove(vbs_path)
                        except Exception as e:
                            logging.getLogger(__name__).debug(
                                "작업 실패: %s", type(e).__name__
                            )
                        break
                    time.sleep(2)

            threading.Thread(
                target=monitor_emulator_and_bat, args=(bat_path,), daemon=True
            ).start()
            bat_process = None
            if bat_path and bat_path.strip():
                bat_process = launch_bat_after_delay(bat_path)
            return bat_process
        elif "vita3k" in core:
            title_id = os.path.basename(os.path.normpath(rom_path))
            cmd = f'"{emulator_path}" -r "{title_id}"'
        elif "dolphin" in core:
            cmd = f'"{emulator_path}" -e "{rom_path}"'
        elif "cemu" in core:
            cmd = f'"{emulator_path}" -g "{rom_path}"'
        else:
            cmd = f'"{emulator_path}" "{rom_path}"'
    else:
        return
    cmd = cmd.replace("/", "\\")
    subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(emulator_path))
    bat_process = None
    if bat_path and bat_path.strip():
        bat_process = launch_bat_after_delay(bat_path)
    return bat_process


def launch_bat_after_delay(bat_path):
    if not os.path.isfile(bat_path):
        return
    time.sleep(10)
    try:
        proc = subprocess.Popen(bat_path, shell=True, cwd=os.path.dirname(bat_path))
        return proc
    except Exception:
        return None


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit(1)
    launch_game(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
