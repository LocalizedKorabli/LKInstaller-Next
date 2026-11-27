import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core import dirs
from core.localizer import select_best_font
from ui.tabs.tab_settings import SettingsTab


class FontSelectionTests(unittest.TestCase):
    def test_cjk_languages_prefer_vector_cjk_ui_fonts_over_segoe_ui(self):
        available = ["Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", "Microsoft JhengHei UI", "Yu Gothic UI"]
        self.assertEqual(select_best_font("zh_CN", available), "Microsoft YaHei UI")
        self.assertEqual(select_best_font("zh_TW", available), "Microsoft JhengHei UI")
        self.assertEqual(select_best_font("ja", available), "Yu Gothic UI")

    def test_latin_and_cyrillic_languages_prefer_segoe_ui(self):
        available = ["Segoe UI", "Arial", "Microsoft YaHei UI"]
        for lang in ("en", "de", "es", "ru"):
            self.assertEqual(select_best_font(lang, available), "Segoe UI")

    def test_falls_back_to_next_available_candidate(self):
        self.assertEqual(select_best_font("zh_CN", ["Segoe UI", "Microsoft YaHei"]), "Microsoft YaHei")
        self.assertEqual(select_best_font("ja", ["Meiryo UI", "Segoe UI"]), "Meiryo UI")


class DirsRealPathTests(unittest.TestCase):
    def test_resolve_real_path_returns_existing_path_without_extended_prefix(self):
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "nested"
            target.mkdir()
            resolved = dirs.resolve_real_path(target)
            self.assertTrue(resolved.is_dir())
            self.assertFalse(str(resolved).startswith("\\\\?\\"))

    def test_resolve_real_path_returns_original_when_missing(self):
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "does_not_exist"
            self.assertEqual(dirs.resolve_real_path(missing), missing)

    def test_open_directory_creates_and_resolves_target_before_startfile(self):
        tab = SettingsTab.__new__(SettingsTab)
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "appdata"
            resolved_fake = Path(temp_dir) / "resolved_appdata"
            resolved_fake.mkdir()

            with patch("ui.tabs.tab_settings.sys.platform", "win32"), \
                 patch("ui.tabs.tab_settings.resolve_real_path", return_value=resolved_fake) as mock_resolve, \
                 patch("ui.tabs.tab_settings.os.startfile", create=True) as mock_startfile:
                tab._open_directory(target)

            self.assertTrue(target.is_dir())
            mock_resolve.assert_called_once_with(target)
            mock_startfile.assert_called_once_with(str(resolved_fake))


if __name__ == "__main__":
    unittest.main()
