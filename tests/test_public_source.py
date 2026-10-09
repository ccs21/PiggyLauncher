"""운영 데이터 없이 공개본의 설정 경계와 가상 서버를 검증한다."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import requests
import scraper_credentials
from bootstrap import prepare_workspace

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "examples" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicSourceTests(unittest.TestCase):
    def test_empty_keys_and_password_not_saved(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {}, clear=True),
        ):
            p = Path(folder) / "api_keys.local.json"
            self.assertEqual(scraper_credentials.load_flags(p)["devpassword"], "")
            p = Path(folder) / "scraper.local.json"
            scraper_credentials.save_flags(
                p, {"id": "example", "pw": "do-not-persist", "region": "미국"}
            )
            self.assertEqual(json.loads(p.read_text()), {"region": "미국"})
            self.assertEqual(scraper_credentials.load_flags(p)["pw"], "")

    def test_environment_key_and_no_legacy_decryption(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(
                os.environ,
                {
                    "SCREENSCRAPER_DEV_ID": "lab-id",
                    "SCREENSCRAPER_DEV_PASSWORD": "lab-only",
                },
            ),
        ):
            keys = scraper_credentials.load_flags(Path(folder) / "api_keys.local.json")
            self.assertEqual(keys["devid"], "lab-id")
            with self.assertRaises(ValueError):
                scraper_credentials.load_flags(Path(folder) / "dev_keys.dat")

    def test_bootstrap_preserves_user_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            prepare_workspace(folder)
            p = Path(folder) / "configs/l_config.json"
            p.write_text('{"custom":true}')
            prepare_workspace(folder)
            self.assertEqual(json.loads(p.read_text()), {"custom": True})

    def test_unconfigured_slug_does_not_connect(self):
        import epic_scanner, stove_scanner

        with (
            patch("service_settings.endpoint", return_value=""),
            patch("requests.get", side_effect=AssertionError("unexpected network")),
        ):
            self.assertEqual(epic_scanner.load_slug_map(), [])
            self.assertEqual(stove_scanner.load_slug_map(), [])

    def test_local_login_and_notice_queue(self):
        server_module = example("lab_server")
        client_module = example("lab_client")
        state = server_module.LabState("only-for-local-test")
        server = ThreadingHTTPServer(("127.0.0.1", 0), server_module.handler_for(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            self.assertEqual(
                requests.post(
                    base + "/lab/login", json={"password": "wrong"}, timeout=3
                ).status_code,
                401,
            )
            response = requests.post(
                base + "/lab/login", json={"password": "only-for-local-test"}, timeout=3
            )
            token = response.json()["token"]
            self.assertEqual(
                requests.get(
                    base + "/lab/session",
                    headers={"Authorization": "Bearer " + token},
                    timeout=3,
                ).status_code,
                200,
            )
            state.sessions[token] = 0
            self.assertEqual(
                requests.get(
                    base + "/lab/session",
                    headers={"Authorization": "Bearer " + token},
                    timeout=3,
                ).status_code,
                401,
            )
            items = requests.get(base + "/lab/notices", timeout=3).json()["items"]
            inbox = client_module.NoticeInbox()
            inbox.ingest(items)
            inbox.ingest(items)
            self.assertEqual([x["sequence"] for x in inbox.pending], [1, 2])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_release_hash_and_oauth_state(self):
        release = example("release_client")
        oauth = example("oauth_desktop")
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "sample"
            p.write_bytes(b"example")
            self.assertTrue(
                release.verify_file(p, hashlib.sha256(b"example").hexdigest())
            )
            self.assertFalse(release.verify_file(p, "0" * 64))
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "example-client"}):
            url, state, verifier = oauth.authorization_request()
            self.assertIn("code_challenge_method=S256", url)
            self.assertNotIn(verifier, url)
            with patch(
                "requests.post", side_effect=AssertionError("unexpected network")
            ):
                with self.assertRaises(ValueError):
                    oauth.exchange_code("code", "wrong", state, verifier)


if __name__ == "__main__":
    unittest.main()
