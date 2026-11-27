import hashlib
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, Mock, patch

from installation.installation_manager import InstallationManager


class EeCacheTests(unittest.TestCase):
    def setUp(self):
        self.manager = InstallationManager.__new__(InstallationManager)
        self.manager._cancel_event = threading.Event()
        self.manager.window = None

    def test_valid_cache_is_reused_on_not_modified(self):
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "ee.zip"
            info_path = Path(temp_dir) / "cache_info.json"
            content = b"cached-ee"
            dest.write_bytes(content)
            info_path.write_text(json.dumps({
                "file_sha256": hashlib.sha256(content).hexdigest(),
                "etags": {"https://example.invalid/ee.zip": '"etag-1"'},
            }), encoding="utf-8")
            response = Mock(status_code=304)

            with patch("installation.installation_manager.requests.get", return_value=response) as get:
                result = self.manager._download_ee_from_url(
                    "https://example.invalid/ee.zip", dest, info_path, "EE test", 5)

            self.assertTrue(result)
            self.assertEqual(dest.read_bytes(), content)
            get.assert_called_once_with(
                "https://example.invalid/ee.zip", stream=True,
                headers={"If-None-Match": '"etag-1"'}, proxies=ANY,
                auth=ANY, timeout=(5, 60),
            )

    def test_changed_response_replaces_cache_and_records_etag(self):
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "ee.zip"
            info_path = Path(temp_dir) / "cache_info.json"
            response = Mock(status_code=200, headers={"ETag": '"etag-2"'})
            response.iter_content.return_value = [b"new-", b"ee"]

            with patch("installation.installation_manager.requests.get", return_value=response):
                result = self.manager._download_ee_from_url(
                    "https://example.invalid/ee.zip", dest, info_path, "EE test", 5)

            self.assertTrue(result)
            self.assertEqual(dest.read_bytes(), b"new-ee")
            metadata = json.loads(info_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["file_sha256"], hashlib.sha256(b"new-ee").hexdigest())
            self.assertEqual(metadata["etags"]["https://example.invalid/ee.zip"], '"etag-2"')

    def test_corrupt_cache_is_not_used_for_conditional_request(self):
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "ee.zip"
            info_path = Path(temp_dir) / "cache_info.json"
            dest.write_bytes(b"corrupt")
            info_path.write_text(json.dumps({
                "file_sha256": hashlib.sha256(b"expected").hexdigest(),
                "etags": {"https://example.invalid/ee.zip": '"etag-1"'},
            }), encoding="utf-8")
            response = Mock(status_code=200, headers={})
            response.iter_content.return_value = [b"fresh"]

            with patch("installation.installation_manager.requests.get", return_value=response) as get:
                result = self.manager._download_ee_from_url(
                    "https://example.invalid/ee.zip", dest, info_path, "EE test", 5)

            self.assertTrue(result)
            self.assertEqual(get.call_args.kwargs["headers"], None)
            self.assertEqual(dest.read_bytes(), b"fresh")


if __name__ == "__main__":
    unittest.main()
