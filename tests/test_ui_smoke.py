"""실게임이나 실제 모니터를 조작하지 않고 공개본의 주요 화면을 생성한다."""

import logging
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@unittest.skipUnless(os.name == "nt", "Classic UI는 Windows 전용입니다.")
class UiSmokeTests(unittest.TestCase):
    def test_empty_library_and_unlocked_settings(self):
        from PySide6.QtWidgets import QApplication, QWidget
        from bootstrap import prepare_workspace
        from theme_manager import ThemeManager
        from main import PiggyLauncher
        from settings_popup import SettingsPopup
        from scraper_setting_popup import ScraperSettingPopup
        from batch_setting_popup import BatchSettingPopup
        from update_popup import UpdatePopup

        root = Path(__file__).resolve().parents[1]
        previous = Path.cwd()
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                prepare_workspace(folder)
                shutil.copytree(root / "theme", Path(folder) / "theme")
                theme = ThemeManager("theme/default")
                parent = QWidget()
                parent.theme_manager = theme
                with (
                    patch(
                        "socket.socket.connect",
                        side_effect=AssertionError("network forbidden"),
                    ),
                    patch(
                        "requests.get", side_effect=AssertionError("network forbidden")
                    ),
                    patch(
                        "subprocess.Popen",
                        side_effect=AssertionError("process forbidden"),
                    ),
                    patch.object(
                        PiggyLauncher, "start_gamepad_handling", lambda self: None
                    ),
                ):
                    constructors = [
                        lambda: SettingsPopup(parent),
                        lambda: ScraperSettingPopup(theme, "arcade", parent),
                        lambda: BatchSettingPopup("user", "example", theme, parent),
                        lambda: UpdatePopup(theme, parent),
                        lambda: PiggyLauncher(theme),
                    ]
                    for make in constructors:
                        widget = make()
                        widget.show()
                        app.processEvents()
                        widget.close()
                        widget.deleteLater()
                        app.processEvents()
            finally:
                logging.shutdown()
                os.chdir(previous)
