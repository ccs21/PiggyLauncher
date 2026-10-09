"""실제 장치·게임·브라우저 없이 실패 복구와 스레드 경계를 재현한다."""

import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"


class CdpTests(unittest.TestCase):
    def test_event_before_reply_and_socket_closed(self):
        import cdp_register_common as cdp

        ws = Mock()
        ws.recv.side_effect = [
            json.dumps({"method": "event"}),
            json.dumps({"id": 1, "result": {"result": {"value": "ok"}}}),
        ]
        with patch.object(cdp.websocket, "create_connection", return_value=ws):
            self.assertEqual(cdp.evaluate("ws://localhost/example", "1"), "ok")
        ws.close.assert_called_once()

    def test_broken_reply_closes_socket(self):
        import cdp_register_common as cdp

        ws = Mock()
        ws.recv.return_value = "invalid json"
        with patch.object(cdp.websocket, "create_connection", return_value=ws):
            self.assertEqual(cdp.evaluate("ws://localhost/example", "1"), "")
        ws.close.assert_called_once()

    def test_unsolicited_events_have_total_deadline(self):
        import cdp_register_common as cdp

        ws = Mock()
        ws.recv.return_value = json.dumps({"method": "event"})
        with (
            patch.object(cdp.websocket, "create_connection", return_value=ws),
            patch.object(cdp.time, "monotonic", side_effect=[0, 0, 1, 11]),
        ):
            self.assertEqual(cdp.evaluate("ws://localhost/example", "1"), "")
        ws.recv.assert_called_once()
        ws.close.assert_called_once()


@unittest.skipUnless(os.name == "nt", "Windows adapter")
class PresetTests(unittest.TestCase):
    def setUp(self):
        import system_config_handler as system

        self.system = system
        self.temporary = tempfile.TemporaryDirectory()
        self.previous = Path.cwd()
        os.chdir(self.temporary.name)
        Path("configs").mkdir()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(os.chdir, self.previous)

    def write_preset(self, value):
        Path("configs/user_test_preset.json").write_text(json.dumps(value))

    def test_failed_resolution_keeps_journal_but_restores_volume(self):
        Path("current_resolution.json").write_text(
            json.dumps({"display": "lab", "resolution": "1280x720", "refresh_rate": 60})
        )
        Path("current_volume.json").write_text('{"volume":0.3}')
        with (
            patch.object(self.system, "apply_resolution", return_value=False),
            patch.object(self.system, "set_audio_volume") as volume,
        ):
            self.assertFalse(self.system.restore_system_settings())
            volume.assert_called_once_with(0.3)
        self.assertTrue(Path("current_resolution.json").exists())
        self.assertFalse(Path("current_volume.json").exists())

    def test_unreadable_display_cannot_create_fake_snapshot(self):
        self.write_preset({"resolution_enabled": True, "resolution": "1280x720"})
        with (
            patch.object(
                self.system, "get_current_resolution", side_effect=RuntimeError
            ),
            patch.object(self.system, "apply_resolution") as change,
            patch.object(self.system, "CustomAlertDialog"),
        ):
            self.assertFalse(self.system.apply_preset("user", "test", None, None))
            change.assert_not_called()
        self.assertFalse(Path("current_resolution.json").exists())

    def test_volume_failure_rolls_back_resolution(self):
        self.write_preset(
            {
                "resolution_enabled": True,
                "resolution": "1280x720",
                "volume_enabled": True,
                "volume": "50%",
            }
        )
        original = {"display": "lab", "resolution": "1920x1080", "refresh_rate": 60}
        with (
            patch.object(self.system, "get_current_resolution", return_value=original),
            patch.object(self.system, "apply_resolution", return_value=True) as change,
            patch.object(self.system, "get_default_audio_volume", return_value=0.7),
            patch.object(
                self.system, "set_audio_volume", side_effect=[RuntimeError(), None]
            ) as volume,
            patch.object(self.system, "CustomAlertDialog"),
        ):
            self.assertFalse(self.system.apply_preset("user", "test", None, None))
            self.assertEqual(change.call_args_list[-1].args, ("lab", 1920, 1080, 60))
            self.assertEqual(volume.call_args_list[-1].args, (0.7,))
        self.assertFalse(Path("current_resolution.json").exists())
        self.assertFalse(Path("current_volume.json").exists())

    def test_invalid_preset_fails_before_change(self):
        self.write_preset({"resolution_enabled": True, "resolution": "broken"})
        with (
            patch.object(self.system, "apply_resolution") as change,
            patch.object(self.system, "CustomAlertDialog"),
        ):
            self.assertFalse(self.system.apply_preset("user", "test", None, None))
            change.assert_not_called()
        self.assertEqual(self.system.parse_resolution("0x720"), (None, None))


@unittest.skipUnless(os.name == "nt", "Windows UI")
class UiBoundaryTests(unittest.TestCase):
    def test_duplicate_initialization_removed(self):
        from PySide6.QtWidgets import QApplication
        from game_detail_screen import GameDetailScreen
        from core_edit_popup import RomEditPopup as CorePopup
        from rom_edit_popup import RomEditPopup
        from theme_manager import ThemeManager

        app = QApplication.instance() or QApplication([])
        theme = ThemeManager("theme/default")
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                for cls, args in (
                    (
                        GameDetailScreen,
                        dict(
                            game_metadata={},
                            theme_manager=theme,
                            app_id="test",
                            platform="user",
                        ),
                    ),
                    (CorePopup, dict(theme_manager=theme, app_id="test", rom_data={})),
                    (
                        RomEditPopup,
                        dict(theme_manager=theme, app_id="test", rom_data={}),
                    ),
                ):
                    with patch.object(cls, "init_ui") as init:
                        dialog = cls(**args)
                        init.assert_called_once()
                        self.assertIs(dialog.theme_manager, theme)
                        dialog.deleteLater()
                        app.processEvents()
            finally:
                os.chdir(old)

    def test_concurrent_emulator_completion_returns_on_gui_once(self):
        from PySide6.QtWidgets import QApplication, QWidget
        from rom_list_popup import GameRunner

        app = QApplication.instance() or QApplication([])
        parent = QWidget()
        parent.is_game_running = True
        parent.central_content = Mock()
        runner = GameRunner("test", {}, parent)
        ids = []
        with patch(
            "rom_list_popup.notification_manager.resume",
            side_effect=lambda: ids.append(threading.get_ident()),
        ):
            threads = [
                threading.Thread(target=runner.restore_launcher) for _ in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(ids, [])
            app.processEvents()
            self.assertEqual(ids, [threading.get_ident()])
            parent.central_content.force_reload_all.assert_called_once()
            self.assertFalse(parent.is_game_running)
        parent.close()
        parent.deleteLater()
        app.processEvents()


class RegistrationTests(unittest.TestCase):
    def test_failure_isolated_and_empty_output_list_shared(self):
        from register_thread import RegisterThread

        failures = []
        seen = []

        def crawler(game, folder):
            seen.append(game["title"])
            if game["title"] == "broken":
                raise ValueError("fixture")
            return True

        worker = RegisterThread(
            [{"title": "broken"}, {"title": "ok"}],
            "user",
            crawler,
            "unused",
            fail_list=failures,
        )
        worker.run()
        self.assertEqual(seen, ["broken", "ok"])
        self.assertEqual(failures, [("broken", "ValueError")])
        self.assertFalse(worker.success)

    def test_auth_marker_from_previous_attempt_is_not_reused(self):
        from register_thread import RegisterThread

        worker = RegisterThread(
            [{"title": "ok", "auth_required": True}],
            "steam",
            lambda *args: True,
            "unused",
        )
        worker.run()
        self.assertEqual(worker.get_auth_queue(), [])
        self.assertTrue(worker.success)

    def test_registration_waits_for_finished_before_auth_retry(self):
        from auto_register_popup import AutoRegisterPopup

        runner = Mock(platform="steam", fail_list=[])
        runner.crawler_fn = Mock(__name__="register_game")
        runner.get_auth_queue.return_value = [{"title": "auth"}]
        fake = Mock(
            current_runner=runner,
            total_fail_list=[],
            platform_index=0,
            _close_when_finished=False,
        )
        fake.sender.return_value = runner
        AutoRegisterPopup.on_runner_finished(fake)
        fake.on_auth_required.assert_called_once_with([{"title": "auth"}])
        fake.start_next_platform.assert_not_called()
        self.assertEqual(fake.platform_index, 0)
        # An old completion callback cannot advance the replacement worker.
        fake.current_runner = Mock()
        AutoRegisterPopup.on_runner_finished(fake)
        self.assertEqual(fake.on_auth_required.call_count, 1)


@unittest.skipUnless(os.name == "nt", "Windows adapters")
class ResourceTests(unittest.TestCase):
    def test_gog_missing_database_is_not_created(self):
        from gog_scanner import scan_gog_installed_games

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.db"
            self.assertEqual(scan_gog_installed_games(path), [])
            self.assertFalse(path.exists())

    def test_bad_core_archive_keeps_existing_dll_and_cleans_temp(self):
        from core_installer import CoreDownloadWorker
        import io, zipfile

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("wrong_libretro.dll", b"wrong")
        response = Mock(status_code=200, headers={})
        response.iter_content.return_value = [archive.getvalue()]
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        with tempfile.TemporaryDirectory() as folder:
            cores = Path(folder) / "cores"
            cores.mkdir()
            expected = cores / "fbneo_libretro.dll"
            expected.write_bytes(b"existing")
            worker = CoreDownloadWorker("fbneo", folder)
            original_mkstemp = tempfile.mkstemp
            with (
                patch("core_installer.requests.get", return_value=context),
                patch(
                    "core_installer.tempfile.mkstemp",
                    side_effect=lambda **kw: original_mkstemp(dir=folder, **kw),
                ),
            ):
                self.assertFalse(
                    worker._download_and_install(
                        "https://example.invalid/core.zip", True
                    )
                )
            self.assertEqual(expected.read_bytes(), b"existing")
            self.assertEqual(list(Path(folder).iterdir()), [cores])

    def test_notice_queue_advances_only_on_actual_close(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QObject, Signal
        from notification_manager import NotificationManager

        app = QApplication.instance() or QApplication([])

        class FakePopup(QObject):
            closed = Signal()

            def __init__(self, **kwargs):
                super().__init__()

        manager = NotificationManager()
        with (
            patch("notification_manager.NotificationPopup", FakePopup),
            patch.object(manager, "_play_notify_sound_async"),
        ):
            manager.push("one", theme_manager=object())
            first = manager.popup
            manager.push("two", theme_manager=object())
            self.assertIs(manager.popup, first)
            self.assertEqual(len(manager.queue), 1)
            first.closed.emit()
            self.assertIsNot(manager.popup, first)
            self.assertEqual(len(manager.queue), 0)
        app.processEvents()


@unittest.skipUnless(os.name == "nt", "Windows UI")
class FormTests(unittest.TestCase):
    def test_extra_input_does_not_shift_metadata_fields(self):
        from PySide6.QtWidgets import QApplication, QWidget, QLineEdit
        from theme_manager import ThemeManager
        from user_register_popup import GameRegisterEditPopup

        app = QApplication.instance() or QApplication([])
        theme = ThemeManager("theme/default")
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                parent = QWidget()
                parent.theme_manager = theme
                form = GameRegisterEditPopup(parent=parent, theme_manager=theme)
                extra = QLineEdit(form.top_right)
                extra.setText("unrelated")
                form.edit_data = {
                    "title": "lab title",
                    "developer": "lab dev",
                    "publisher": "lab publisher",
                    "release_date": "2000-01-01",
                }
                form.fill_existing_data()
                for key in ("title", "developer", "publisher", "release_date"):
                    self.assertEqual(
                        form.metadata_inputs[key].text(), form.edit_data[key]
                    )
                self.assertEqual(extra.text(), "unrelated")
                form.close()
                parent.close()
                form.deleteLater()
                parent.deleteLater()
                app.processEvents()
            finally:
                os.chdir(previous)
