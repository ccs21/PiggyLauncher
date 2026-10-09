"""프로젝트의 로컬 패드 매핑 형식을 읽고 저장하는 어댑터.
SDL 매핑에서 변환한 값과 사용자가 학습한 값을 같은 저장 경계로 다룬다.
"""

import os
import json
from typing import Any, Dict, Optional

OUR_DB_PATH_DEFAULT = os.path.join("tools", "our_gamepad_db.json")
_cache: Dict[str, Any] = {}
_cached_path: str = ""
_cached_mtime: float = -1.0


def _load_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data
    return {}


def load(path: str = OUR_DB_PATH_DEFAULT) -> Dict[str, Any]:
    global _cache, _cached_path, _cached_mtime
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = -1.0
    if path != _cached_path or mtime != _cached_mtime:
        _cache = _load_file(path)
        _cached_path = path
        _cached_mtime = mtime
    return _cache


def lookup(guid: str, path: str = OUR_DB_PATH_DEFAULT) -> Optional[Dict[str, Any]]:
    db = load(path)
    entry = db.get(guid)
    if isinstance(entry, dict):
        return entry
    return None
