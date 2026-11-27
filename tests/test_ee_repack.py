import threading
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from installation import installation_utils
from installation.installation_manager import InstallationManager


class EeRepackTests(unittest.TestCase):
    def setUp(self):
        self.manager = InstallationManager.__new__(InstallationManager)
        self.manager._cancel_event = threading.Event()
        self.manager.window = None

    def _make_task(self, instance_id: str):
        return SimpleNamespace(
            instance=SimpleNamespace(instance_id=instance_id),
            task_name="EE Test",
            log_callback=None,
            progress_callback=None,
            window=None,
        )

    def test_build_ee_mkmod_preserves_long_paths_without_disk_unpack(self):
        long_internal_path = (
            "gui/unbound2/mods/"
            + "/".join(["very_long_nested_directory_segment_name"] * 7)
            + "/extremely_long_localization_experience_enhancement_asset_filename.xml"
        )
        self.assertGreater(len(long_internal_path), 300)

        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            ee_zip_path = temp_root / "ee.zip"
            with zipfile.ZipFile(ee_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("gui/unbound2/mods/", "")
                zf.writestr(long_internal_path, b"<root>ok</root>")

            task = self._make_task("inst-long")
            errors = []

            with patch.object(installation_utils, "TEMP_DIR", temp_root / "temp"), \
                 patch.object(installation_utils, "EE_UNPACK_TEMP", temp_root / "temp" / "ee"):
                mkmod_path = self.manager._build_ee_mkmod(task, ee_zip_path, errors)

                self.assertEqual(errors, [])
                self.assertIsNotNone(mkmod_path)
                self.assertTrue(mkmod_path.is_file())
                self.assertFalse((temp_root / "temp" / "ee").exists())

                with zipfile.ZipFile(mkmod_path, "r") as out_zf:
                    self.assertEqual(out_zf.namelist(), [long_internal_path])
                    info = out_zf.getinfo(long_internal_path)
                    self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                    self.assertEqual(out_zf.read(long_internal_path), b"<root>ok</root>")

    def test_build_ee_mkmod_returns_none_for_empty_zip(self):
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            ee_zip_path = temp_root / "empty_ee.zip"
            with zipfile.ZipFile(ee_zip_path, "w") as zf:
                zf.writestr("empty_dir/", "")

            task = self._make_task("inst-empty")
            errors = []

            with patch.object(installation_utils, "TEMP_DIR", temp_root / "temp"):
                mkmod_path = self.manager._build_ee_mkmod(task, ee_zip_path, errors)

            self.assertEqual(errors, [])
            self.assertIsNone(mkmod_path)
            self.assertFalse((temp_root / "temp" / "inst-empty_ee.mkmod").exists())


if __name__ == "__main__":
    unittest.main()
