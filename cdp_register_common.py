"""로컬 Chrome의 탭 조회와 JavaScript 평가를 묶은 CDP 어댑터.

CDP는 HTTP로 탭을 찾고 WebSocket으로 명령을 전달한다. 응답 사이에
이벤트가 끼어들 수 있으므로 요청 ID가 같은 응답만 선택한다. 실패 시
빈 결과를 반환하는 기존 호출 규약을 유지하며, 연결은 반드시 닫는다.
브라우저를 띄우거나 로그인하는 책임은 이 모듈에 없다.
"""

import json
import time
import requests
import websocket
from contextlib import closing

CDP_PORT = 9222


def get_all_tabs():
    """디버깅 포트의 탭 목록을 조회한다. Chrome이 없으면 빈 목록이다."""
    try:
        with requests.get(f"http://localhost:{CDP_PORT}/json", timeout=5) as response:
            response.raise_for_status()
            tabs = response.json()
        return (
            [tab for tab in tabs if isinstance(tab, dict)]
            if isinstance(tabs, list)
            else []
        )
    except Exception:
        return []


def is_valid_ws_url(url):
    """탭 응답의 WebSocket 주소 형식을 확인한다. 접근 권한 검사는 아니다."""
    return isinstance(url, str) and url.startswith("ws://") and (len(url) > 10)


def evaluate(ws_url, js_code):
    """JavaScript의 직렬화 가능한 결과를 반환하고 연결을 정리한다.

    수신 제한과 전체 마감 시간을 함께 둔다. 이벤트가 계속 들어오면 소켓의
    개별 recv 타임아웃만으로는 무한 대기를 막을 수 없기 때문이다.
    호출자는 이 함수를 작업 스레드에서 실행해야 화면이 멈추지 않는다.
    """
    try:
        message = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": js_code, "returnByValue": True},
        }
        deadline = time.monotonic() + 10
        with closing(websocket.create_connection(ws_url, timeout=5)) as ws:
            ws.send(json.dumps(message))
            while time.monotonic() < deadline:
                ws.settimeout(max(0.001, min(5, deadline - time.monotonic())))
                response = json.loads(ws.recv())
                if response.get("id") == 1:
                    return response.get("result", {}).get("result", {}).get("value", "")
    except Exception:
        pass
    return ""
