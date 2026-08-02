import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from installation.installation_manager import InstallationManager


class InstallationVersionResolutionTests(unittest.TestCase):
    def test_uses_cached_remote_version_for_second_local_version(self):
        manager = InstallationManager.__new__(InstallationManager)
        manager._cancel_event = threading.Event()
        manager._lock = threading.Lock()
        manager.download_routes_priority = ["primary"]
        manager.download_jobs = {}
        manager.download_queue = queue.Queue()

        instance = SimpleNamespace(
            type="mir_korabley",
            versions=[
                SimpleNamespace(exe_version="26.8.0.0", bin_folder_name="1000001"),
                SimpleNamespace(exe_version="26.7.0.0", bin_folder_name="999999"),
            ],
        )
        task = Mock(
            task_name="Mir Korabley",
            instance=instance,
            lang_code="zh_cn",
            use_ee=False,
            use_fonts=False,
            ee_job_id=None,
            fo_job_id=None,
            mo_job_id=None,
            status="pending",
            log_callback=None,
            progress_callback=None,
        )

        source = Mock()
        source.get_available_route_ids.return_value = ["primary"]
        source.get_urls.return_value = {
            "version": "https://example.invalid/version.txt",
            "mo": "https://example.invalid/global.mo",
        }
        response = Mock(text="2026.08.01\n26.7\n")

        with patch(
                "installation.installation_manager.global_source_manager.get_source",
                return_value=source,
            ):
            with patch(
                "installation.installation_manager.requests.get",
                return_value=response,
            ) as get:
                manager._resolve_task_version(task)

        self.assertEqual(get.call_count, 1)
        self.assertEqual(task.mo_job_id, "zh_cn_26.7_2026.08.01")
        self.assertEqual(task.status, "downloading")
        self.assertEqual(manager.download_jobs[task.mo_job_id].version_info, {
            "main": "26.7",
            "sub": "2026.08.01",
        })


if __name__ == "__main__":
    unittest.main()
