"""저장된 GUID 매핑과 현재 연결 장치를 비교하는 보조 모듈.
입력 이벤트 루프는 gamepad_handler가 담당한다. 장치 목록 조회와 버튼 처리의 책임을 구분한다.
"""

import os
import json
import pygame

PROFILE_FILE = os.path.join("configs", "gamepad_profiles.json")


def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unmapped_gamepads(full=False):
    profiles = load_profiles()
    unmapped = []
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        guid = joystick.get_guid()
        name = joystick.get_name()
        if guid not in profiles:
            if full:
                unmapped.append((joystick, guid, name))
            else:
                unmapped.append((guid, name))
    return unmapped
