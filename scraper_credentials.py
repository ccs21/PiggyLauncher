"""수집기 설정 경계. 개발자 키는 환경변수 또는 사용자가 만든 로컬 파일에서 읽는다.

고정 암호화 키는 포함하지 않는다. 로컬 JSON은 평문이므로 공유하면 안 된다.
사용자 암호는 디스크에 저장하지 않고 현재 입력 또는 환경변수로 제공한다.
"""

import json
import os
from pathlib import Path


def load_flags(filepath):
    """기존 수집기 호출 규약을 유지하되 운영 데이터 파일은 읽지 않는다."""
    path = Path(filepath)
    if path.suffix != ".json":
        raise ValueError("공개본 설정은 JSON 파일만 사용합니다.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("설정 최상위 값은 객체여야 합니다.")
    if path.name == "api_keys.local.json":
        for key, env in [
            ("devid", "SCREENSCRAPER_DEV_ID"),
            ("devpassword", "SCREENSCRAPER_DEV_PASSWORD"),
        ]:
            data[key] = os.environ.get(env, data.get(key, ""))
    elif path.name == "scraper.local.json":
        data["id"] = os.environ.get("SCREENSCRAPER_USER", "")
        data["pw"] = os.environ.get("SCREENSCRAPER_PASSWORD", "")
    return data


def save_flags(filepath, data):
    """지역 등 환경설정만 저장한다. 사용자 ID·암호는 저장 대상에서 제외한다."""
    path = Path(filepath)
    if path.name != "scraper.local.json":
        raise ValueError("자격 증명 파일은 자동 저장하지 않습니다.")
    safe = {k: data[k] for k in ("region", "scrap_type", "translate") if k in data}
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
