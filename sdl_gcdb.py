"""SDL 매핑 DB의 행을 해석하고 장치에 맞는 항목을 고른다.
GUID 일치와 이름 유사도는 서로 다른 근거다. 후보 선택 이유를 함께 반환해 진단 가능하게 한다.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

DB_PATH_DEFAULT = os.path.join("tools", "gamecontrollerdb.txt")


@dataclass
class GcdbEntry:
    guid: str
    name: str
    tokens: Dict[str, str]
    platform: str


def parse_gcdb_line(line: str) -> Optional[GcdbEntry]:
    s = line.strip()
    if not s or s.startswith("#") or "," not in s:
        return None
    parts = s.split(",")
    if len(parts) < 3:
        return None
    guid = parts[0].strip()
    name = parts[1].strip()
    tokens: Dict[str, str] = {}
    platform = ""
    for kv in parts[2:]:
        kv = kv.strip()
        if not kv or ":" not in kv:
            continue
        (k, v) = kv.split(":", 1)
        k = k.strip()
        v = v.strip()
        if k == "platform":
            platform = v
        else:
            tokens[k] = v
    return GcdbEntry(guid=guid, name=name, tokens=tokens, platform=platform)


def load_gcdb(db_path: str = DB_PATH_DEFAULT) -> List[GcdbEntry]:
    entries: List[GcdbEntry] = []
    if not os.path.exists(db_path):
        return entries
    with open(db_path, "r", encoding="utf-8") as f:
        for raw in f:
            e = parse_gcdb_line(raw)
            if e:
                entries.append(e)
    return entries


def _norm(s: str) -> str:
    return (s or "").lower().strip()


def pick_best_with_reason(
    entries: List[GcdbEntry],
    guid: str,
    name: str,
    platform: str = "Windows",
    debug: bool = False,
) -> Tuple[Optional[GcdbEntry], str]:
    """
    허용 우선순위:
      1) GUID 정확 일치
      2) XInput 힌트(기기명이 xbox/xinput이거나 DB guid=='xinput') → Windows 우선
    그 외 이름 기반 매칭은 전부 금지합니다.
    """
    g = _norm(guid)
    n_raw = _norm(name)
    if g:
        for e in entries:
            if _norm(e.guid) == g:
                return (e, "GUID_MATCH")
    if "xbox" in n_raw or "xinput" in n_raw:
        xinputs = [e for e in entries if _norm(e.guid) == "xinput"]
        if xinputs:
            for xe in xinputs:
                if _norm(xe.platform) == _norm(platform):
                    return (xe, "XINPUT_HINT_WIN")
            return (xinputs[0], "XINPUT_HINT_ANY")
    return (None, "NO_MATCH")
