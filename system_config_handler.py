"""게임 실행 전 Windows 설정을 보관하고, 종료 후 원래 값으로 돌린다.

복구 파일은 변경 전 상태를 나타내는 작은 저널이다. 실제 복구가 성공한
뒤에만 지운다. 해상도와 볼륨은 독립적으로 복구하므로 한 장치가 없어져도
다른 설정의 복구를 막지 않는다. 이 모듈은 게임 종료 여부를 판정하지 않는다.

Classic의 외부 ResolutionSwitcher 호출을 유지한다. 이는 Python 자체의
제약이 아니라 당시 선택한 Windows 디스플레이 제어 어댑터다.
"""

import json
import logging
import math
import os
import subprocess
import win32api
import win32con
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from popup_alert import CustomAlertDialog

CURRENT_RES_PATH = "current_resolution.json"
CURRENT_VOL_PATH = "current_volume.json"
RES_SWITCHER_PATH = os.path.join("tools", "ResolutionSwitcher.exe")
logger = logging.getLogger(__name__)


def get_default_audio_volume():
    """기본 재생 장치의 볼륨을 0~1 실수로 읽는다. 장치 오류는 호출자에게 전달한다."""
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    return volume.GetMasterVolumeLevelScalar()


def set_audio_volume(value: float):
    """기본 장치 볼륨을 설정한다. 잘못된 값으로 기존 볼륨을 덮어쓰지 않는다."""
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("볼륨은 0~1 범위여야 합니다.")
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volume.SetMasterVolumeLevelScalar(value, None)


def parse_resolution(res_string):
    """'1920x1080'을 양의 정수 쌍으로 변환한다. 잘못된 입력은 (None, None)."""
    try:
        width, height = (int(part) for part in res_string.lower().split("x"))
        if width > 0 and height > 0:
            return width, height
    except (AttributeError, TypeError, ValueError):
        pass
    return None, None


def apply_resolution(display, width, height, rate) -> bool:
    """외부 도구의 성공 종료를 확인한다. 도구가 멈춰도 15초 이상 기다리지 않는다."""
    try:
        subprocess.run(
            [
                RES_SWITCHER_PATH,
                "--monitor",
                display,
                "--width",
                str(width),
                "--height",
                str(height),
                "--refresh",
                str(int(rate)),
            ],
            check=True,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.SubprocessError, TypeError, ValueError) as error:
        logger.warning("해상도 변경 실패: %s", type(error).__name__)
        return False


def get_current_resolution(display) -> dict:
    """실제 모니터 상태를 읽는다. 실패 시 임의의 해상도를 복구값으로 만들지 않는다."""
    devmode = win32api.EnumDisplaySettings(display, win32con.ENUM_CURRENT_SETTINGS)
    return {
        "display": display,
        "resolution": f"{devmode.PelsWidth}x{devmode.PelsHeight}",
        "refresh_rate": int(devmode.DisplayFrequency),
    }


def _save_snapshot(path, data):
    """변경 전에 복구 기록을 완성한다. 쓰기 실패 시 장치 설정은 건드리지 않는다.

    단일 게임 실행을 전제로 한다. 남은 기록은 복구 실패의 증거이므로 새 게임의
    상태로 덮어쓰지 않는다. 임시 파일 교체는 쓰다가 끊긴 JSON 노출을 줄인다.
    """
    if os.path.exists(path):
        raise RuntimeError("이전 설정의 복구 기록이 남아 있습니다.")
    temporary = path + ".tmp"
    try:
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def apply_preset(platform, app_id, theme_manager, parent_window) -> bool:
    """프리셋 적용 성공 또는 미설정이면 True, 적용 실패이면 False.

    모든 입력을 먼저 해석한 후 '기록 → 변경' 순서로 처리한다. 중간 실패 시
    이미 변경한 항목을 복구하고 실행을 취소한다. False를 받은 UI도 게임 중
    상태를 해제해야 한다. 파일 경로는 등록된 플랫폼/게임 ID로 구성된다.
    """
    preset_path = os.path.join("configs", f"{platform}_{app_id}_preset.json")
    if not os.path.exists(preset_path):
        return True
    try:
        with open(preset_path, encoding="utf-8") as stream:
            preset = json.load(stream)
        resolution_enabled = preset.get("resolution_enabled", False)
        volume_enabled = preset.get("volume_enabled", False)
        if resolution_enabled:
            display = preset.get("resolution_display", "\\\\.\\DISPLAY1")
            width, height = parse_resolution(preset.get("resolution", ""))
            refresh = int(preset.get("refresh_rate", 60))
            if not width or not height or refresh < 1:
                raise ValueError("해상도 또는 주사율이 잘못되었습니다.")
        if volume_enabled:
            volume = (
                float(str(preset.get("volume", "100%")).replace("%", "").strip()) / 100
            )
            if not math.isfinite(volume) or not 0 <= volume <= 1:
                raise ValueError("볼륨이 잘못되었습니다.")
        # 이전 실행의 복구가 끝나지 않았다면 해당 값부터 복구한다.
        if not restore_system_settings():
            raise RuntimeError("이전 설정을 복구하지 못했습니다.")
        if resolution_enabled:
            _save_snapshot(CURRENT_RES_PATH, get_current_resolution(display))
            changed = apply_resolution(display, width, height, refresh)
            # 60/59 Hz처럼 드라이버가 인접한 정수값을 쓰는 Classic의 재시도 방식.
            if not changed and refresh > 1:
                changed = apply_resolution(display, width, height, refresh - 1)
            if not changed:
                raise RuntimeError("지원되지 않는 해상도 또는 주사율입니다.")
        if volume_enabled:
            _save_snapshot(CURRENT_VOL_PATH, {"volume": get_default_audio_volume()})
            set_audio_volume(volume)
        return True
    except Exception as error:
        logger.warning("프리셋 적용 취소: %s", type(error).__name__)
        restored = restore_system_settings()
        message = "실행 프리셋을 적용하지 못했습니다. 해상도·주사율·볼륨 및 장치를 확인해 주세요."
        if not restored:
            message += "\n원래 설정의 복구도 완료되지 않아 복구 기록을 보관했습니다."
        CustomAlertDialog(
            "프리셋 적용 실패", message, theme_manager, parent_window
        ).exec()
        return False


def restore_system_settings() -> bool:
    """남아 있는 복구 기록을 처리한다. 모두 복구했거나 기록이 없으면 True.

    실패한 기록은 지우지 않는다. 다음 호출에서 재시도할 수 있다. 해상도 실패
    때문에 볼륨 복구까지 생략하지 않도록 항목마다 별도의 예외 경계를 둔다.
    """
    success = True
    for path in (CURRENT_RES_PATH, CURRENT_VOL_PATH):
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as stream:
                data = json.load(stream)
            if path == CURRENT_RES_PATH:
                width, height = parse_resolution(data["resolution"])
                if not width or not height or int(data["refresh_rate"]) < 1:
                    raise ValueError("잘못된 해상도 복구 기록")
                if not apply_resolution(
                    data["display"], width, height, data["refresh_rate"]
                ):
                    raise RuntimeError("해상도 복구 실패")
            else:
                set_audio_volume(float(data["volume"]))
            os.remove(path)
        except Exception as error:
            success = False
            logger.warning("설정 복구 실패, 기록 보존: %s", type(error).__name__)
    return success
