"""빈 설정에서는 외부 통신을 시작하지 않는 교육용 연결 설정.

주소는 운영 코드에서 복사하지 않고 학습자가 자신의 서버 주소를 입력한다.
"""

import json
from pathlib import Path
from urllib.parse import urlsplit


def endpoint(name):
    """설정된 HTTP 주소만 반환한다. 로컬 실습 외에는 HTTPS를 요구한다."""
    path = Path("configs/services.local.json")
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    value = data.get(name, "")
    if not value:
        return ""
    parsed = urlsplit(value)
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.username or parsed.password or (not parsed.hostname):
        raise ValueError("연결 주소 형식을 확인하세요.")
    if parsed.scheme != "https" and (not (local and parsed.scheme == "http")):
        raise ValueError("외부 서버에는 HTTPS를 사용하세요.")
    return value
