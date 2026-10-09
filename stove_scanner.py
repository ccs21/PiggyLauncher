"""STOVE 클라이언트 설정과 매니페스트에서 설치 게임을 찾는다.
상품 번호 매핑은 사용자 설정에 의존하며 공개본에는 제작자 운영 서버 주소가 없다.
"""

import os
import json
import requests


def load_slug_map(json_url=""):
    """자체 설정한 매핑 주소만 조회한다. 공개본에는 제작자의 운영 서버 주소나 기본 매핑 데이터가 없다."""
    from service_settings import endpoint

    json_url = json_url or endpoint("stove_slug_url")
    if not json_url:
        return []
    try:
        res = requests.get(json_url, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def find_slug(display_name, slug_data):
    """로컬 게임 제목을 매핑 데이터의 상품 번호와 연결한다. 제목 규칙이 달라지면 매핑을 갱신해야 한다."""
    for entry in slug_data:
        et = entry.get("title", "")
        game_id = entry.get("game_id")
        if et == display_name:
            return str(game_id)
    for entry in slug_data:
        et = entry.get("title", "")
        game_id = entry.get("game_id")
        if display_name in et:
            return str(game_id)
    return None


def scan_stove_games(config_path, manifest_dir, slug_json_path=""):
    """클라이언트 설정과 매니페스트에서 설치 게임을 읽는다. 실제 상품 수집은 등록 작업 단계에서 수행한다."""
    slug_data = load_slug_map(slug_json_path)
    games = []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        path_list = config.get("defaultPathList")
        if not path_list:
            return []
    except Exception:
        return []
    for file in os.listdir(manifest_dir):
        if not file.endswith(".json"):
            continue
        try:
            with open(os.path.join(manifest_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
            exe = data.get("execution")
            root = data.get("root_folder")
            srvcode = data.get("service_code")
            if not exe or not root:
                continue
            install_path = None
            for root_path in path_list:
                candidate = os.path.join(root_path, root)
                exe_path = os.path.join(candidate, exe)
                if os.path.exists(candidate) and os.path.exists(exe_path):
                    install_path = candidate
                    break
            if not install_path:
                continue
            upf_path = os.path.join(install_path, "combinedata_manifest")
            title = None
            if os.path.isdir(upf_path):
                for upf in os.listdir(upf_path):
                    if upf.endswith(".upf"):
                        try:
                            with open(
                                os.path.join(upf_path, upf), "r", encoding="utf-8"
                            ) as uf:
                                upf_data = json.load(uf)
                                title = upf_data.get("game_title")
                                if title:
                                    break
                        except:
                            continue
            if not title:
                continue
            slug = find_slug(title, slug_data)
            if not slug:
                continue
            exe_full_path = os.path.join(install_path, exe)
            appid = f"stove_{slug}"
            games.append(
                {
                    "appid": appid,
                    "title": title,
                    "exe": exe,
                    "exe_full_path": exe_full_path,
                    "path": install_path,
                    "service_code": srvcode,
                }
            )
        except Exception:
            continue
    return games


if __name__ == "__main__":
    config_path = os.path.expandvars(
        "%LocalAppData%\\\\STOVE\\\\Config\\\\ClientConfig.json"
    )
    manifest_dir = os.path.expandvars("%LocalAppData%\\\\STOVE\\\\GameManifest")
    games = scan_stove_games(config_path, manifest_dir)
