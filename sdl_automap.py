"""SDL 컨트롤러 매핑을 Classic의 입력 프로필로 변환한다.
축·버튼·햇 입력은 번호뿐 아니라 방향·종류도 필요하므로 단순 이름 치환으로 처리할 수 없다.
"""

import os
import json
from typing import Any, Dict, Iterable, Optional, Set, Tuple
import pygame
from sdl_gcdb import load_gcdb, pick_best_with_reason, GcdbEntry
from our_gamepad_db import lookup as ourdb_lookup

PROFILES_PATH_DEFAULT = os.path.join("configs", "gamepad_profiles.json")
DB_PATH_DEFAULT = os.path.join("tools", "gamecontrollerdb.txt")
OUR_DB_PATH_DEFAULT = os.path.join("tools", "our_gamepad_db.json")


def _extract_device_info(
    dev: Any,
) -> Tuple[str, str, Optional[pygame.joystick.Joystick]]:
    joy: Optional[pygame.joystick.Joystick] = None
    name = ""
    guid = ""
    if hasattr(dev, "get_name") and hasattr(dev, "get_id"):
        joy = dev
        try:
            name = joy.get_name() or ""
        except Exception:
            name = ""
        try:
            guid = joy.get_guid() or ""
        except Exception:
            guid = ""
        return (name, guid, joy)
    if isinstance(dev, dict):
        name = str(dev.get("name", "") or "")
        guid = str(dev.get("guid", "") or "")
        j = dev.get("joystick")
        if j is not None and hasattr(j, "get_id"):
            joy = j
        return (name, guid, joy)
    if isinstance(dev, (tuple, list)):
        for it in dev:
            if hasattr(it, "get_id"):
                joy = it
                try:
                    name = joy.get_name() or name
                except Exception:
                    pass
                try:
                    guid = joy.get_guid() or guid
                except Exception:
                    pass
        for it in dev:
            if isinstance(it, str):
                s = it.lower()
                if len(it) >= 32 and all(
                    (c in "0123456789abcdef-" for c in s.replace("-", ""))
                ):
                    if not guid:
                        guid = it
                elif not name:
                    name = it
        return (name, guid, joy)
    return (name, guid, None)


def _translate_tokens_to_profile(
    e: GcdbEntry, joy: Optional[pygame.joystick.Joystick], debug: bool = False
) -> Optional[Dict[str, Any]]:
    t = e.tokens
    profile: Dict[str, Any] = {"buttons": {}, "axes": {}, "hat": {}}

    def _btn(key_sdl: str, key_out: str):
        v = t.get(key_sdl)
        if not v:
            return
        if v.startswith("b"):
            try:
                profile["buttons"][key_out] = int(v[1:])
            except Exception:
                pass

    def _axis(key_sdl: str, key_out: str):
        v = t.get(key_sdl)
        if not v:
            return
        if "a" in v:
            try:
                num = int(
                    v.replace("+", "")
                    .replace("-", "")
                    .replace("~", "")
                    .replace("a", "")
                )
                profile["axes"][key_out] = num
            except Exception:
                pass

    def _hat(key_sdl: str, dir_out: str):
        v = t.get(key_sdl)
        if v and v.startswith("h") and ("." in v):
            try:
                (left, right) = v.split(".", 1)
                hat_index = int(left.replace("h", ""))
                mask = int(right)
                profile["hat"]["index"] = hat_index
                profile["hat"][dir_out] = mask
            except Exception:
                pass

    _btn("a", "a")
    _btn("b", "b")
    _btn("x", "x")
    _btn("y", "y")
    _btn("leftshoulder", "lb")
    _btn("rightshoulder", "rb")
    _btn("back", "back")
    _btn("start", "start")
    _btn("guide", "guide")
    _axis("leftx", "leftx")
    _axis("lefty", "lefty")
    _axis("rightx", "rightx")
    _axis("righty", "righty")
    _axis("lefttrigger", "lt")
    _axis("righttrigger", "rt")
    _hat("dpup", "up")
    _hat("dpdown", "down")
    _hat("dpleft", "left")
    _hat("dpright", "right")
    nb = na = nh = None
    if joy is not None:
        try:
            nb = joy.get_numbuttons()
            na = joy.get_numaxes()
            nh = joy.get_numhats()
        except Exception:
            pass
    if isinstance(nb, int) and nb >= 0:
        for k, idx in list(profile["buttons"].items()):
            if not isinstance(idx, int) or idx < 0 or idx >= nb:
                profile["buttons"].pop(k, None)
    if isinstance(na, int) and na >= 0:
        for k, idx in list(profile["axes"].items()):
            if not isinstance(idx, int) or idx < 0 or idx >= na:
                profile["axes"].pop(k, None)
    if "index" in profile["hat"] and isinstance(nh, int) and (nh >= 0):
        if profile["hat"]["index"] >= nh:
            profile["hat"].clear()
    has_face = any((k in profile["buttons"] for k in ("a", "b", "x", "y")))
    has_hat = "index" in profile["hat"]
    if not (has_face or has_hat):
        return None
    return {
        "name": e.name,
        "type": "sdl_auto",
        "buttons": profile["buttons"],
        "axes": profile["axes"],
        "hat": profile["hat"],
    }


def _flatten_to_legacy(profile: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    btns = profile.get("buttons", {})
    for k in ("a", "b", "x", "y", "lb", "rb"):
        v = btns.get(k)
        if isinstance(v, int):
            out[k] = v
    hat = profile.get("hat", {})
    if hat:
        if "up" in hat:
            out["hat_up"] = [0, 1]
        if "down" in hat:
            out["hat_down"] = [0, -1]
        if "left" in hat:
            out["hat_left"] = [-1, 0]
        if "right" in hat:
            out["hat_right"] = [1, 0]
    return out


def _flatten_from_sdl_auto_entry(
    entry: Dict[str, Any], debug: bool = False
) -> Optional[Dict[str, Any]]:
    if not isinstance(entry, dict):
        return None
    if "buttons" not in entry and "hat" not in entry:
        return None
    return _flatten_to_legacy(entry, debug=debug)


def _load_profiles(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_profiles(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _merge_profile_legacy(
    doc: Dict[str, Any], guid: str, legacy_profile: Dict[str, Any]
) -> Dict[str, Any]:
    if "profiles" in doc and isinstance(doc["profiles"], dict):
        doc["profiles"][guid] = legacy_profile
    else:
        doc[guid] = legacy_profile
    return doc


def _migrate_existing_sdl_auto(
    doc: Dict[str, Any], debug: bool = False
) -> Dict[str, Any]:
    for k, v in list(doc.items()):
        if isinstance(v, dict) and ("buttons" in v or "hat" in v):
            if any((isinstance(v.get(x), (int, list)) for x in ("a", "lb", "hat_up"))):
                continue
            flat = _flatten_from_sdl_auto_entry(v, debug=debug)
            if flat:
                doc[k] = flat
    if "profiles" in doc and isinstance(doc["profiles"], dict):
        for k, v in list(doc["profiles"].items()):
            if isinstance(v, dict) and ("buttons" in v or "hat" in v):
                if any(
                    (isinstance(v.get(x), (int, list)) for x in ("a", "lb", "hat_up"))
                ):
                    continue
                flat = _flatten_from_sdl_auto_entry(v, debug=debug)
                if flat:
                    doc["profiles"][k] = flat
    return doc


def automap_for_devices(
    devices: Iterable[Any],
    profiles_path: str = PROFILES_PATH_DEFAULT,
    db_path: str = DB_PATH_DEFAULT,
    our_db_path: str = OUR_DB_PATH_DEFAULT,
    platform: str = "Windows",
    debug: bool = False,
) -> Set[str]:
    entries = load_gcdb(db_path)
    if not entries:
        return set()
    mapped: Set[str] = set()
    profiles_doc = _load_profiles(profiles_path)
    profiles_doc = _migrate_existing_sdl_auto(profiles_doc, debug=debug)
    for dev in devices:
        (name, guid, joy) = _extract_device_info(dev)
        legacy_from_our = ourdb_lookup(guid, path=our_db_path)
        if isinstance(legacy_from_our, dict) and legacy_from_our:
            key = guid or name
            profiles_doc = _merge_profile_legacy(profiles_doc, key, legacy_from_our)
            mapped.add(key)
            continue
        (entry, reason) = pick_best_with_reason(
            entries, guid, name, platform=platform, debug=debug
        )
        if entry:
            mid = _translate_tokens_to_profile(entry, joy, debug=debug)
            if mid:
                legacy = _flatten_to_legacy(mid, debug=debug)
                if legacy:
                    key = guid or name
                    profiles_doc = _merge_profile_legacy(profiles_doc, key, legacy)
                    mapped.add(key)
                    continue
    if mapped:
        _save_profiles(profiles_path, profiles_doc)
    return mapped
