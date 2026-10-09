"""Windows 장치·시스템 표시 정보를 읽는 보조 함수.
운영체제 API 실패와 실제 값이 없는 경우를 기본 표시값으로 변환하는 경계다.
"""

import ctypes
import comtypes


def get_system_volume_percent():
    try:
        comtypes.CoInitialize()
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return int(volume.GetMasterVolumeLevelScalar() * 100)
    except Exception as e:
        return f"오류: {e}"
    finally:
        try:
            comtypes.CoUninitialize()
        except:
            pass


def get_monitor_info():
    user32 = ctypes.windll.user32
    EnumDisplayDevices = user32.EnumDisplayDevicesW
    EnumDisplaySettings = user32.EnumDisplaySettingsW
    DISPLAY_DEVICE_ACTIVE = 1
    monitors = []

    class DEVMODE(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName", ctypes.c_wchar * 32),
            ("dmSpecVersion", ctypes.c_ushort),
            ("dmDriverVersion", ctypes.c_ushort),
            ("dmSize", ctypes.c_ushort),
            ("dmDriverExtra", ctypes.c_ushort),
            ("dmFields", ctypes.c_ulong),
            ("dmOrientation", ctypes.c_short),
            ("dmPaperSize", ctypes.c_short),
            ("dmPaperLength", ctypes.c_short),
            ("dmPaperWidth", ctypes.c_short),
            ("dmScale", ctypes.c_short),
            ("dmCopies", ctypes.c_short),
            ("dmDefaultSource", ctypes.c_short),
            ("dmPrintQuality", ctypes.c_short),
            ("dmColor", ctypes.c_short),
            ("dmDuplex", ctypes.c_short),
            ("dmYResolution", ctypes.c_short),
            ("dmTTOption", ctypes.c_short),
            ("dmCollate", ctypes.c_short),
            ("dmFormName", ctypes.c_wchar * 32),
            ("dmLogPixels", ctypes.c_ushort),
            ("dmBitsPerPel", ctypes.c_ulong),
            ("dmPelsWidth", ctypes.c_ulong),
            ("dmPelsHeight", ctypes.c_ulong),
            ("dmDisplayFlags", ctypes.c_ulong),
            ("dmDisplayFrequency", ctypes.c_ulong),
            ("dmICMMethod", ctypes.c_ulong),
            ("dmICMIntent", ctypes.c_ulong),
            ("dmMediaType", ctypes.c_ulong),
            ("dmDitherType", ctypes.c_ulong),
            ("dmReserved1", ctypes.c_ulong),
            ("dmReserved2", ctypes.c_ulong),
            ("dmPanningWidth", ctypes.c_ulong),
            ("dmPanningHeight", ctypes.c_ulong),
        ]

    class DISPLAY_DEVICE(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("DeviceName", ctypes.c_wchar * 32),
            ("DeviceString", ctypes.c_wchar * 128),
            ("StateFlags", ctypes.c_ulong),
            ("DeviceID", ctypes.c_wchar * 128),
            ("DeviceKey", ctypes.c_wchar * 128),
        ]

    i = 0
    while True:
        display_device = DISPLAY_DEVICE()
        display_device.cb = ctypes.sizeof(DISPLAY_DEVICE)
        if not EnumDisplayDevices(None, i, ctypes.byref(display_device), 0):
            break
        if not display_device.StateFlags & DISPLAY_DEVICE_ACTIVE:
            i += 1
            continue
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        if not EnumDisplaySettings(
            display_device.DeviceName, -1, ctypes.byref(devmode)
        ):
            i += 1
            continue
        monitors.append(
            {
                "model": display_device.DeviceString,
                "id": display_device.DeviceName,
                "adapter": display_device.DeviceID.split("\\")[0]
                if display_device.DeviceID
                else "알 수 없음",
                "resolution": f"{devmode.dmPelsWidth}x{devmode.dmPelsHeight}",
                "refresh_rate": str(devmode.dmDisplayFrequency),
                "primary": bool(display_device.StateFlags & 4),
            }
        )
        i += 1
    return monitors


def get_available_display_modes(display_id="\\\\.\\DISPLAY1"):
    import ctypes

    class DEVMODE(ctypes.Structure):
        _fields_ = [
            ("dmDeviceName", ctypes.c_wchar * 32),
            ("dmSpecVersion", ctypes.c_ushort),
            ("dmDriverVersion", ctypes.c_ushort),
            ("dmSize", ctypes.c_ushort),
            ("dmDriverExtra", ctypes.c_ushort),
            ("dmFields", ctypes.c_ulong),
            ("dmOrientation", ctypes.c_short),
            ("dmPaperSize", ctypes.c_short),
            ("dmPaperLength", ctypes.c_short),
            ("dmPaperWidth", ctypes.c_short),
            ("dmScale", ctypes.c_short),
            ("dmCopies", ctypes.c_short),
            ("dmDefaultSource", ctypes.c_short),
            ("dmPrintQuality", ctypes.c_short),
            ("dmColor", ctypes.c_short),
            ("dmDuplex", ctypes.c_short),
            ("dmYResolution", ctypes.c_short),
            ("dmTTOption", ctypes.c_short),
            ("dmCollate", ctypes.c_short),
            ("dmFormName", ctypes.c_wchar * 32),
            ("dmLogPixels", ctypes.c_ushort),
            ("dmBitsPerPel", ctypes.c_ulong),
            ("dmPelsWidth", ctypes.c_ulong),
            ("dmPelsHeight", ctypes.c_ulong),
            ("dmDisplayFlags", ctypes.c_ulong),
            ("dmDisplayFrequency", ctypes.c_ulong),
            ("dmICMMethod", ctypes.c_ulong),
            ("dmICMIntent", ctypes.c_ulong),
            ("dmMediaType", ctypes.c_ulong),
            ("dmDitherType", ctypes.c_ulong),
            ("dmReserved1", ctypes.c_ulong),
            ("dmReserved2", ctypes.c_ulong),
            ("dmPanningWidth", ctypes.c_ulong),
            ("dmPanningHeight", ctypes.c_ulong),
        ]

    devmode = DEVMODE()
    devmode.dmSize = ctypes.sizeof(DEVMODE)
    mode_map = {}
    i = 0
    user32 = ctypes.windll.user32
    while user32.EnumDisplaySettingsW(display_id, i, ctypes.byref(devmode)):
        key = (devmode.dmPelsWidth, devmode.dmPelsHeight)
        hz = devmode.dmDisplayFrequency
        if key not in mode_map:
            mode_map[key] = set()
        mode_map[key].add(hz)
        i += 1
    return mode_map


def get_system_log_string():
    volume = get_system_volume_percent()
    monitors = get_monitor_info()
    lines = []
    lines.append(
        f"현재 시스템의 볼륨 : {volume}%" if isinstance(volume, int) else volume
    )
    lines.append("")
    lines.append(f"감지된 모니터의 갯수 : {len(monitors)}개")
    lines.append("")
    for m in monitors:
        lines.extend(
            [
                f"모니터 번호 : {m['id']}",
                f"모델명 : [{m['model']}]",
                f"그래픽카드 : {m['adapter']}",
                f"해상도 : {m['resolution']} @ {m['refresh_rate']}Hz",
                f"주 모니터 여부 : {('예' if m['primary'] else '아니오')}",
                "",
            ]
        )
    return "\n".join(lines)
