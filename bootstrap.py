"""처음 실행할 때 빈 로컬 작업 공간을 만든다. 기존 파일은 덮어쓰지 않는다."""

import json
from pathlib import Path


def prepare_workspace(root):
    """실행 폴더에 최소 설정과 빈 라이브러리를 준비한다.
    기존 파일은 읽거나 덮어쓰지 않는다. 설치된 제품의 사용자 설정을 복사하는
    마이그레이션 함수가 아니라, 소스만 받은 학습자가 시작할 수 있게 하는 함수다.
    """
    root = Path(root)
    for directory in ("configs", "user", "logs", "tools", "launcher_temp", "l_libs"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    for platform in ("steam", "epic", "gog", "stove", "user", "emul"):
        (root / "l_libs" / platform).mkdir(exist_ok=True)
    defaults = {
        "l_config.json": {"theme": "default", "launch_on_startup": False},
        "emul_config.json": {"executables": {}},
        "user_categories.json": [],
        "gamepad_profiles.json": {},
        "version_info.json": {"launcher": "0.4.9-source"},
    }
    for name, data in defaults.items():
        path = root / "configs" / name
        if not path.exists():
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
