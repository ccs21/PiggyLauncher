"""교재의 영속 큐·페이지·백업을 가상 데이터로 검증한다."""
from pathlib import Path
import tempfile
import unittest
import threading
from http.server import ThreadingHTTPServer
import requests
from test_public_source import example


class TeachingExamplesTests(unittest.TestCase):
    def test_http_pagination_and_logout(self):
        server_module = example("lab_server")
        store_module = example("notice_store")
        sync_module = example("notice_sync")
        with tempfile.TemporaryDirectory() as folder:
            store = store_module.NoticeStore(Path(folder) / "notices.sqlite")
            for i in range(23):
                store.append(str(i))
            state = server_module.LabState("local-example-only", store)
            server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.handler_for(state))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = "http://127.0.0.1:" + str(server.server_port)
                session = requests.Session()
                session.trust_env = False
                with session:
                    token = session.post(base + "/lab/login", json={"password": "local-example-only"}, timeout=3).json()["token"]
                    session.headers["Authorization"] = "Bearer " + token
                    self.assertEqual(session.get(base + "/lab/session", timeout=3).status_code, 200)
                    inbox = sync_module.DurableInbox(Path(folder) / "queue.json")
                    sync_module.synchronize(base, inbox, session)
                    sync_module.synchronize(base, inbox, session)
                    self.assertEqual(len(inbox.state["pending"]), 23)
                    self.assertEqual(session.get(base + "/lab/notices?limit=0", timeout=3).status_code, 400)
                    session.post(base + "/lab/logout", timeout=3).raise_for_status()
                    self.assertEqual(session.get(base + "/lab/session", timeout=3).status_code, 401)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_notice_paging_backup_and_validation(self):
        module = example("notice_store")
        with tempfile.TemporaryDirectory() as folder:
            store = module.NoticeStore(Path(folder) / "source.sqlite")
            for i in range(23):
                store.append("notice " + str(i))
            first = store.page(limit=20)
            self.assertTrue(first["has_more"])
            self.assertEqual(len(store.page(first["next_after"])["items"]), 3)
            backup = Path(folder) / "backup.sqlite"
            store.backup(backup)
            store.append("after backup")
            self.assertEqual(module.NoticeStore(backup).page(23)["items"], [])
            with self.assertRaises(FileExistsError):
                store.backup(backup)
            with self.assertRaises(ValueError):
                store.append(" ")
            with self.assertRaises(ValueError):
                store.page(limit=101)

    def test_durable_queue_restart_ack_and_duplicate(self):
        module = example("notice_sync")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "inbox.json"
            inbox = module.DurableInbox(path)
            page = {"items": [{"sequence": 1, "text": "hello"}], "next_after": 1}
            inbox.ingest(page)
            inbox = module.DurableInbox(path)
            inbox.ingest(page)
            self.assertEqual(len(inbox.state["pending"]), 1)
            inbox.acknowledge_first()
            self.assertEqual(module.DurableInbox(path).state, {"after": 1, "pending": []})
            with self.assertRaises(ValueError):
                inbox.ingest({"items": [], "next_after": 2})
            self.assertEqual(module.DurableInbox(path).state["after"], 1)

    def test_theme_strings_are_not_paths(self):
        from theme_manager import ThemeManager
        theme = ThemeManager.__new__(ThemeManager)
        theme.theme_dir = "assets"
        theme.theme = {"color": "transparent", "family": "Arial", "image": "sample.svg"}
        self.assertEqual(theme.get("color"), "transparent")
        self.assertEqual(theme.get("family"), "Arial")
        self.assertEqual(Path(theme.get("image")), Path("assets/sample.svg"))


if __name__ == "__main__":
    unittest.main()
