"""독립 교재용 공지 저장소와 로컬 작성 CLI. 실제 제품의 서버/DB와 무관하다."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3


class NoticeStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("CREATE TABLE IF NOT EXISTS lab_bulletins (sequence INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL)")

    def append(self, text):
        """추가만 허용한다. 순번을 재사용하지 않아 커서 뒤의 공지를 놓치지 않는다."""
        text = text.strip()
        if not 1 <= len(text) <= 2000:
            raise ValueError("공지 길이는 1~2000자입니다.")
        with closing(sqlite3.connect(self.path, timeout=5)) as conn, conn:
            return conn.execute("INSERT INTO lab_bulletins(text) VALUES (?)", (text,)).lastrowid

    def page(self, after=0, limit=20):
        if after < 0 or not 1 <= limit <= 100:
            raise ValueError("잘못된 페이지 범위")
        with closing(sqlite3.connect(self.path, timeout=5)) as conn:
            rows = conn.execute("SELECT sequence,text FROM lab_bulletins WHERE sequence>? ORDER BY sequence LIMIT ?", (after, limit + 1)).fetchall()
        items = [{"sequence": n, "text": t} for n, t in rows[:limit]]
        return {"items": items, "next_after": items[-1]["sequence"] if items else after, "has_more": len(rows) > limit}

    def backup(self, destination):
        """SQLite backup API는 열린 DB도 일관된 사본으로 복사한다. 기존 파일은 덮어쓰지 않는다."""
        target = Path(destination)
        with target.open("xb"):
            pass
        with closing(sqlite3.connect(self.path)) as source, closing(sqlite3.connect(target)) as output:
            source.backup(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="lab_data/notices.sqlite")
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--add")
    command.add_argument("--list", action="store_true")
    command.add_argument("--backup")
    args = parser.parse_args()
    store = NoticeStore(args.db)
    if args.add is not None:
        print("추가 순번:", store.append(args.add))
    elif args.backup:
        store.backup(args.backup)
        print("백업 완료")
    else:
        after = 0
        while True:
            page = store.page(after)
            for item in page["items"]:
                print(item["sequence"], item["text"])
            if not page["has_more"]:
                break
            after = page["next_after"]


if __name__ == "__main__":
    main()
