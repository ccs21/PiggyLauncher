"""
l_libs/emul/* 하위 폴더의 meta.json, rom_list.json을 읽어
- rom_list의 core/core_type이 meta의 main_core/main_core_type과 '모두 동일'하면 빈 문자열("")로 비움
- rom_list의 emulator_path가 configs/emul_config.json 내 실행 경로들과 '동일'하면 빈 문자열("")로 비움
변경이 없으면 백업/저장을 하지 않음.
스레드로 백그라운드에서 실행하여 초기 로딩을 막지 않음.

[개선점]
- 자원 환원: 실행 중 방문한 디렉터리에서 rom_list.json.tmp 스위프, 대용량 컬렉션 참조 해제
- 중복 실행 가드: 이미 동작 중이면 신규 실행 스킵
"""

from __future__ import annotations
import json
import logging
import os
import threading
import traceback
from typing import Any, Dict, Set, Tuple, Optional
from shutil import copyfile

EMUL_ROOT = os.path.join("l_libs", "emul")
EMUL_CONFIG_PATH = os.path.join("configs", "emul_config.json")
_RUNNING_LOCK = threading.Lock()
_CURRENT_THREAD: Optional[threading.Thread] = None


def _log(msg: str) -> None:
    """로컬 정리 작업의 진단을 DEBUG 수준에 남긴다. 네트워크 보고는 하지 않는다."""
    logging.getLogger(__name__).debug("%s", msg)


def _normalize_path(p: str) -> str:
    try:
        return os.path.normcase(os.path.normpath(p or "").strip('"').strip())
    except Exception:
        return (p or "").strip()


def _safe_load_json(path: str) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _log(f"[⚠️] JSON 로드 실패: {path} → {e}")
        return None


def _atomic_write_json(path: str, data: Any) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _collect_all_string_values(obj: Any, out: Optional[Set[str]] = None) -> Set[str]:
    """
    configs/emul_config.json에서 '실행기 경로'를 특정 키에 한정하지 않고
    모든 문자열 값을 수집하여 경로 후보로 사용한다.
    (구조 변화에 강인)
    """
    if out is None:
        out = set()
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_all_string_values(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_all_string_values(v, out)
    elif isinstance(obj, str):
        out.add(obj)
    return out


def _load_emul_config_paths() -> Set[str]:
    """
    emul_config.json에서 실행 경로 후보들을 수집하고 정규화하여 반환
    """
    paths: Set[str] = set()
    if not os.path.exists(EMUL_CONFIG_PATH):
        _log(f"[ℹ️] emul_config 없음 → 경로 비교 스킵: {EMUL_CONFIG_PATH}")
        return paths
    obj = _safe_load_json(EMUL_CONFIG_PATH)
    if obj is None:
        return paths
    raw_strs = _collect_all_string_values(obj)
    for s in raw_strs:
        n = _normalize_path(s)
        if n:
            paths.add(n)
    if paths:
        _log(f"[🔍] emul_config 경로 후보 {len(paths)}개 수집 완료")
    else:
        _log("[ℹ️] emul_config 내 문자열 경로 후보가 비어있음")
    return paths


def _read_meta_main_core(meta_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    meta.json에서 main_core, main_core_type을 읽어 반환.
    키 미존재 시 None으로 처리.
    """
    meta = _safe_load_json(meta_path)
    if not isinstance(meta, dict):
        return (None, None)
    main_core = meta.get("main_core")
    main_core_type = meta.get("main_core_type")
    if main_core is None and isinstance(meta.get("main"), dict):
        main_core = meta["main"].get("core")
    if main_core_type is None and isinstance(meta.get("main"), dict):
        main_core_type = meta["main"].get("core_type")
    return (main_core, main_core_type)


def _process_one_emul_dir(dir_path: str, emul_exec_paths_norm: Set[str]) -> None:
    """
    단일 기종 폴더 처리:
      - meta.json, rom_list.json 동시에 존재할 때만 처리
      - 변경 없으면 백업/저장 없음
    """
    app_id = os.path.basename(dir_path)
    meta_path = os.path.join(dir_path, "meta.json")
    rom_list_path = os.path.join(dir_path, "rom_list.json")
    backup_path = os.path.join(dir_path, "clnbkup_rom_list.json")
    if not (os.path.exists(meta_path) and os.path.exists(rom_list_path)):
        _log(f"[⏭️] {app_id}: meta.json 또는 rom_list.json 없음 → 스킵")
        return
    (main_core, main_core_type) = _read_meta_main_core(meta_path)
    if main_core is None or main_core_type is None:
        _log(f"[⏭️] {app_id}: meta에 main_core/main_core_type 누락 → 스킵")
        return
    rom_list = _safe_load_json(rom_list_path)
    if not isinstance(rom_list, list):
        _log(f"[⏭️] {app_id}: rom_list.json 형식이 리스트가 아님 → 스킵")
        return
    changed_core = 0
    changed_exec = 0
    for item in rom_list:
        if not isinstance(item, dict):
            continue
        core = item.get("core")
        core_type = item.get("core_type")
        if core == main_core and core_type == main_core_type:
            if core or core_type:
                item["core"] = ""
                item["core_type"] = ""
                changed_core += 1
        emulator_path = item.get("emulator_path")
        if isinstance(emulator_path, str) and emulator_path.strip():
            norm_item_path = _normalize_path(emulator_path)
            if norm_item_path in emul_exec_paths_norm:
                item["emulator_path"] = ""
                changed_exec += 1
    total_changes = changed_core + changed_exec
    if total_changes <= 0:
        _log(f"[ℹ️] {app_id}: 변경 없음 → 백업/저장 스킵")
        return
    try:
        copyfile(rom_list_path, backup_path)
        _atomic_write_json(rom_list_path, rom_list)
        _log(
            f"[💾] {app_id}: core/core_type 정리 {changed_core}건, emulator_path 정리 {changed_exec}건 → 저장 완료"
        )
    except Exception as e:
        _log(f"[❌] {app_id}: 저장 실패 → {e}\n{traceback.format_exc()}")


def _sweep_tmp_files(visited_dirs: Set[str]) -> None:
    """
    _atomic_write_json() 도중 예외 등으로 남았을 수 있는 rom_list.json.tmp를 정리한다.
    방문 디렉터리만 대상으로 수행하여 범위를 최소화.
    """
    for d in sorted(visited_dirs):
        try:
            tmp_path = os.path.join(d, "rom_list.json.tmp")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                _log(f"[🧹] 잔여 tmp 삭제: {tmp_path}")
        except Exception as e:
            _log(f"[⚠️] tmp 삭제 실패: {d} → {e}")


def _cleanup_after_run(locals_ref: Dict[str, Any]) -> None:
    """
    실행 종료 직전 호출되어, 임시파일 스위프 및 대용량 컬렉션 참조 해제를 수행한다.
    """
    try:
        visited_dirs: Set[str] = locals_ref.get("visited_dirs", set()) or set()
        _sweep_tmp_files(visited_dirs)
    finally:
        for k in ("visited_dirs", "emul_exec_paths_norm", "subdirs"):
            if k in locals_ref:
                v = locals_ref[k]
                try:
                    if hasattr(v, "clear"):
                        v.clear()
                except Exception:
                    pass
                locals_ref[k] = None


def _worker() -> None:
    acquired = _RUNNING_LOCK.acquire(blocking=False)
    if not acquired:
        _log("[⏭️] 정리 스레드가 이미 실행 중 → 신규 실행 스킵")
        return
    local_vars_for_cleanup: Dict[str, Any] = {
        "visited_dirs": set(),
        "emul_exec_paths_norm": None,
        "subdirs": None,
    }
    try:
        _log("[🧼] ROM 리스트 코어/경로 정리 시작")
        if not os.path.exists(EMUL_ROOT):
            _log(f"[ℹ️] emul 폴더 없음 → 전체 스킵: {EMUL_ROOT}")
            _log("[✅] 정리 스레드 종료")
            return
        emul_exec_paths_norm = _load_emul_config_paths()
        local_vars_for_cleanup["emul_exec_paths_norm"] = emul_exec_paths_norm
        try:
            subdirs = [
                os.path.join(EMUL_ROOT, d)
                for d in os.listdir(EMUL_ROOT)
                if os.path.isdir(os.path.join(EMUL_ROOT, d))
            ]
            local_vars_for_cleanup["subdirs"] = subdirs
        except Exception as e:
            _log(f"[❌] emul 하위 폴더 조회 실패 → {e}\n{traceback.format_exc()}")
            _log("[✅] 정리 스레드 종료")
            return
        if not subdirs:
            _log("[ℹ️] 처리할 하위 폴더 없음")
            _log("[✅] 정리 스레드 종료")
            return
        for d in sorted(subdirs):
            _process_one_emul_dir(d, emul_exec_paths_norm)
            local_vars_for_cleanup["visited_dirs"].add(d)
        _log("[✅] ROM 리스트 코어/경로 정리 완료")
    except Exception as e:
        _log(f"[❌] 정리 스레드 예외: {e}\n{traceback.format_exc()}")
    finally:
        _log("[🧹] 정리 스레드 종료 전 자원 환원 수행")
        try:
            _cleanup_after_run(local_vars_for_cleanup)
        except Exception as ce:
            _log(f"[⚠️] 자원 환원 중 오류: {ce}")
        try:
            _RUNNING_LOCK.release()
        except Exception:
            pass


def start_cleaner_thread() -> Optional[threading.Thread]:
    """
    정리기를 백그라운드 스레드로 기동한다.
    이미 실행 중이면 새 스레드는 만들지 않고 None을 반환한다.
    """
    global _CURRENT_THREAD
    if _RUNNING_LOCK.locked():
        _log("[⏭️] 이미 실행 중이므로 새 스레드를 만들지 않습니다")
        return None
    t = threading.Thread(target=_worker, name="RomListCoreCleaner", daemon=True)
    _CURRENT_THREAD = t
    t.start()
    return t


def run_once_blocking() -> None:
    """
    테스트/디버깅용: 동기 실행
    """
    _worker()


if __name__ == "__main__":
    run_once_blocking()
