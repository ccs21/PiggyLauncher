"""공지 페이지와 미표시 큐를 함께 저장한다. 실행은 사용자 요청 시에만 한다."""
import json
import os
from pathlib import Path
import requests


class DurableInbox:
    def __init__(self, path):
        self.path = Path(path)
        self.state = {"after": 0, "pending": []}
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(self.state.get("after"), int) or not isinstance(self.state.get("pending"), list):
                raise ValueError("큐 파일 형식 오류: 원본을 보존하고 조사하세요.")

    def _save(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)
        self.state = state

    def ingest(self, page):
        """커서와 큐를 한 파일에 확정한다. 커서만 앞서 저장하면 알림이 유실된다."""
        after = self.state["after"]
        added = []
        for item in page["items"]:
            if not isinstance(item["sequence"], int) or not isinstance(item["text"], str):
                raise ValueError("잘못된 공지 항목")
            if item["sequence"] > after:
                added.append(item)
                after = item["sequence"]
        if page["next_after"] != after:
            raise ValueError("페이지 커서 불일치")
        self._save({"after": after, "pending": self.state["pending"] + added})

    def acknowledge_first(self):
        """실제로 표시한 뒤 호출한다. 표시 직후 전원 차단 시 중복은 가능하나 유실은 피한다."""
        if self.state["pending"]:
            self._save({"after": self.state["after"], "pending": self.state["pending"][1:]})


def synchronize(base, inbox, session=None):
    client = session or requests
    while True:
        before = inbox.state["after"]
        response = client.get(base + "/lab/notices", params={"after": before, "limit": 20}, timeout=5)
        response.raise_for_status()
        page = response.json()
        inbox.ingest(page)
        if not page["has_more"]:
            break
        if inbox.state["after"] <= before:
            raise ValueError("진행하지 않는 페이지 응답")


def main():
    inbox = DurableInbox("lab_data/inbox.local.json")
    try:
        synchronize("http://127.0.0.1:8000", inbox)
    except requests.RequestException:
        print("연결할 수 없어 저장된 상태를 유지합니다.")
    while inbox.state["pending"]:
        print(inbox.state["pending"][0]["text"])
        inbox.acknowledge_first()


if __name__ == "__main__":
    main()
