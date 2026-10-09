"""Steam 레지스트리·라이브러리·매니페스트에서 설치 게임을 찾는다.
실행 정보 해석에는 Classic의 외부 VDFparse 의존성이 남아 있다. 상점 이미지 수집은 별도 모듈이다.
"""

import os
import re
import subprocess
import sys
import winreg


def get_steam_root_from_registry():
    """현재 Windows 사용자의 Steam 설치 경로를 레지스트리에서 읽는다. 조회 실패 시 None을 반환한다."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\\\Valve\\\\Steam")
        (value, _) = winreg.QueryValueEx(key, "SteamPath")
        return os.path.normpath(value)
    except Exception:
        return None


def get_library_folders(steam_root):
    """libraryfolders.vdf에서 복수 라이브러리 경로를 추출한다. 단순 정규식 파싱이므로 VDF 전체 문법 구현은 아니다."""
    vdf_path = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        return []
    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
        paths = re.findall('"path"\\s*"([^"]+)"', content)
        cleaned = [os.path.normpath(p.replace("\\\\", "\\")) for p in paths]
        return list(set([steam_root] + cleaned))
    except Exception:
        return [steam_root]


def get_appinfo_path(steam_root):
    """Steam 설치 루트에서 appcache/appinfo.vdf 위치를 계산한다."""
    return os.path.join(steam_root, "appcache", "appinfo.vdf")


def get_exe_name_by_vdfparse(appid: str, steam_root: str):
    """외부 VDFparse를 통해 바이너리 appinfo에서 실행 파일 정보를 얻는다. 도구 또는 데이터가 없으면 빈 문자열이다."""
    exe_path = os.path.join("tools", "vdfparse.exe")
    appinfo = get_appinfo_path(steam_root)
    if not os.path.exists(appinfo) or not os.path.exists(exe_path):
        return ""
    try:
        CREATE_NO_WINDOW = 134217728
        result = subprocess.run(
            [exe_path, appinfo, str(appid)],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=CREATE_NO_WINDOW if sys.platform.startswith("win") else 0,
        )
        matches = re.findall('"([^\\"]+\\.exe)"', result.stdout, re.IGNORECASE)
        exe_names = [
            m for m in matches if m and (not m.lower().startswith("unitycrashhandler"))
        ]
        return exe_names[0] if exe_names else ""
    except Exception:
        return ""


def scan_installed_steam_games():
    """라이브러리별 appmanifest를 읽고 설치 경로·상품 ID·실행 파일 후보를 모은다. 상점 스크래핑과 설치 검색을 분리한다."""
    results = []
    steam_root = get_steam_root_from_registry()
    if not steam_root:
        return []
    library_paths = get_library_folders(steam_root)
    for library_root in library_paths:
        steamapps_path = os.path.join(library_root, "steamapps")
        common_path = os.path.join(steamapps_path, "common")
        if not os.path.exists(steamapps_path):
            continue
        for file in os.listdir(steamapps_path):
            if file.startswith("appmanifest_") and file.endswith(".acf"):
                appid = file.replace("appmanifest_", "").replace(".acf", "")
                manifest_path = os.path.join(steamapps_path, file)
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except:
                    continue
                installdir_match = re.search('"installdir"\\s*"([^"]+)"', content)
                name_match = re.search('"name"\\s*"([^"]+)"', content)
                if not installdir_match:
                    continue
                install_folder = installdir_match.group(1)
                game_name = name_match.group(1) if name_match else install_folder
                exclude_keywords = ["Steamworks", "SteamVR"]
                if any(
                    (
                        keyword.lower() in game_name.lower()
                        for keyword in exclude_keywords
                    )
                ):
                    continue
                full_path = os.path.join(common_path, install_folder)
                exe_name = get_exe_name_by_vdfparse(appid, steam_root)
                exe_full_path = ""
                if exe_name:
                    for root, _, files in os.walk(full_path):
                        if exe_name in files:
                            exe_full_path = os.path.join(root, exe_name)
                            break
                if not exe_full_path:
                    for root, _, files in os.walk(full_path):
                        exes = [
                            f
                            for f in files
                            if f.lower().endswith(".exe")
                            and "unitycrashhandler" not in f.lower()
                        ]
                        if exes:
                            exe_full_path = os.path.join(
                                root, sorted(exes, key=lambda x: len(x))[0]
                            )
                            break
                exe_name = os.path.basename(exe_full_path) if exe_full_path else ""
                results.append(
                    {
                        "platform": "steam",
                        "appid": appid,
                        "title": game_name,
                        "path": full_path,
                        "exe": exe_name,
                        "exe_full_path": exe_full_path,
                        "steam_root": steam_root,
                    }
                )
    return results
