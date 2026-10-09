"""로컬 서버와만 통신하는 로그인·공지 큐 예제. 런처 시작 시 자동 실행하지 않는다."""

from collections import deque
import os
import requests


class NoticeInbox:
    def __init__(self):
        self.seen = set()
        self.pending = deque()

    def ingest(self, items):
        """순서대로 큐에 넣는다. 같은 응답을 다시 받아도 중복 추가하지 않는다."""
        for item in sorted(items, key=lambda row: row["sequence"]):
            if item["sequence"] not in self.seen:
                self.seen.add(item["sequence"])
                self.pending.append(item)


def main():
    base = "http://127.0.0.1:8000"
    with requests.Session() as session:
        response = session.post(
            base + "/lab/login",
            json={"password": os.environ.get("LAB_PASSWORD", "")},
            timeout=5,
        )
        response.raise_for_status()
        session.headers["Authorization"] = "Bearer " + response.json()["token"]
        response = session.get(base + "/lab/session", timeout=5)
        response.raise_for_status()
        print("로그인 확인 완료 (토큰은 출력하지 않음)")
        response = session.get(base + "/lab/notices", timeout=5)
        response.raise_for_status()
        inbox = NoticeInbox()
        inbox.ingest(response.json()["items"])
        inbox.ingest(response.json()["items"])
        while inbox.pending:
            print(inbox.pending.popleft()["text"])


if __name__ == "__main__":
    main()
