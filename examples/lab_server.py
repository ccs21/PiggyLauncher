"""독립적인 로컬 로그인·공지 교재. 실제 제품의 API나 데이터 구조와 무관하다.

127.0.0.1에만 바인딩한다. 세션은 메모리에만 보관하며 재시작하면 사라진다.
암호 방식은 흐름 학습용이다. 실제 Google 인증은 oauth_desktop.py를 참고한다.
"""

import hmac
import json
import os
import secrets
import threading
import time
from urllib.parse import urlsplit, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LabState:
    def __init__(self, password, notice_store=None):
        self.password = password
        self.sessions = {}
        self.lock = threading.Lock()
        self.notice_store = notice_store
        self.notices = [
            {"sequence": 1, "text": "첫 번째 가상 공지"},
            {"sequence": 2, "text": "두 번째 가상 공지"},
        ]

    def login(self, password):
        if not hmac.compare_digest(password.encode(), self.password.encode()):
            return None
        token = secrets.token_urlsafe(32)
        with self.lock:
            now = time.monotonic()
            self.sessions = {k: v for k, v in self.sessions.items() if v > now}
            if len(self.sessions) >= 100:
                return None
            self.sessions[token] = now + 300
        return token

    def valid(self, token):
        with self.lock:
            return self.sessions.get(token, 0) > time.monotonic()

    def logout(self, token):
        with self.lock:
            self.sessions.pop(token, None)


def handler_for(state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            # 토큰·비밀번호·요청 본문이 콘솔 로그에 남지 않게 한다.
            pass

        def reply(self, status, data):
            payload = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            if self.path == "/lab/logout":
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                state.logout(token)
                self.reply(200, {"authenticated": False})
                return
            if self.path != "/lab/login":
                self.reply(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                password = body["password"]
                if not isinstance(password, str):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                self.reply(400, {"error": "bad_request"})
                return
            token = state.login(password)
            self.reply(
                200 if token else 401,
                {"token": token, "expires_in": 300}
                if token
                else {"error": "unauthorized"},
            )

        def do_GET(self):
            parsed = urlsplit(self.path)
            if self.path == "/lab/session":
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                ok = state.valid(token)
                self.reply(200 if ok else 401, {"authenticated": ok})
            elif parsed.path == "/lab/notices":
                try:
                    params = parse_qs(parsed.query)
                    after = int(params.get("after", ["0"])[0])
                    limit = int(params.get("limit", ["20"])[0])
                    if after < 0 or not 1 <= limit <= 100:
                        raise ValueError()
                    if state.notice_store:
                        page = state.notice_store.page(after, limit)
                    else:
                        rows = [n for n in state.notices if n["sequence"] > after]
                        items = rows[:limit]
                        page = {"items": items, "next_after": items[-1]["sequence"] if items else after, "has_more": len(rows) > limit}
                    self.reply(200, page)
                except ValueError:
                    self.reply(400, {"error": "bad_cursor"})
            else:
                self.reply(404, {"error": "not_found"})

    return Handler


def main():
    password = os.environ.get("LAB_PASSWORD", "")
    if len(password) < 16:
        raise SystemExit("실습용 LAB_PASSWORD를 16자 이상 설정하세요.")
    from notice_store import NoticeStore

    store_path = os.environ.get("LAB_NOTICE_DB", "")
    store = NoticeStore(store_path) if store_path else None
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler_for(LabState(password, store)))
    print("로컬 실습 서버: http://127.0.0.1:8000 (Ctrl+C로 종료)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
