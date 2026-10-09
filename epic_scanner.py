"""Epic 로컬 설치 매니페스트를 등록 후보로 바꾼다.
상품 slug는 사용자 설정 매핑을 보조로 사용하며, 미설정 상태에서는 운영 서버로 접속하지 않는다.
"""

import logging
import os
import json
import re
import requests


def normalize_title(raw_title: str) -> str:
    """제목 비교를 방해하는 가격·안내 문구를 제거한다. 상품 고유 ID 조회를 대신하는 완전한 식별 방법은 아니다."""
    clean = re.sub(
        "(기본 게임|무료|이용 가능.*|₩[0-9,]+|−.*|\\\\n)",
        "",
        raw_title,
        flags=re.IGNORECASE,
    )
    return clean.strip().lower()


def load_slug_map(json_url=""):
    """사용자가 설정한 매핑 JSON을 읽는다. 주소가 비어 있으면 빈 목록을 반환하고 통신하지 않는다."""
    from service_settings import endpoint

    json_url = json_url or endpoint("epic_slug_url")
    if not json_url:
        return []
    try:
        res = requests.get(json_url, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def find_slug(display_name, slug_data):
    """정규화된 제목의 정확 일치를 우선하고 부분 일치를 보조로 사용한다. 동명 상품은 잘못 매칭될 수 있다."""
    dn = normalize_title(display_name)
    for entry in slug_data:
        et = normalize_title(entry["title"])
        if et == dn:
            return entry["slug"]
    for entry in slug_data:
        et = normalize_title(entry["title"])
        if dn in et:
            return entry["slug"]
    return None


def scan_epic_games(manifest_dir, slug_json_path=""):
    """로컬 .item 설치 매니페스트와 선택적 slug 매핑을 결합한다. 구입 목록 전체가 아니라 설치 흔적을 읽는다."""
    slug_data = load_slug_map(slug_json_path)
    games = []
    for file in os.listdir(manifest_dir):
        if not file.endswith(".item"):
            continue
        try:
            with open(os.path.join(manifest_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("DisplayName")
            exe = data.get("LaunchExecutable")
            path = data.get("InstallLocation")
            if not all([title, exe, path]):
                continue
            slug = find_slug(title, slug_data)
            if not slug:
                continue
            full_path = os.path.join(path, exe)
            appid = f"epic_{slug}"
            game = {
                "appid": appid,
                "title": title,
                "exe": exe,
                "exe_full_path": full_path,
                "path": path,
            }
            games.append(game)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    return games


if __name__ == "__main__":
    manifest_path = os.path.expandvars(
        "%ProgramData%\\\\Epic\\\\EpicGamesLauncher\\\\Data\\\\Manifests"
    )
    games = scan_epic_games(manifest_path)
