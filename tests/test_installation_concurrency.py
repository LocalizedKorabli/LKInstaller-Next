import queue
import threading
import unittest
from unittest.mock import Mock, patch

from installation.installation_manager import DownloadJob, InstallationManager


class ImmediateRoot:
    def after(self, _delay, callback, *args):
        callback(*args)


def make_task(name="Task"):
    task = Mock()
    task.task_name = name
    task.status = "downloading"
    task.log_callback = None
    task.progress_callback = None
    return task


def make_manager(tasks):
    manager = InstallationManager.__new__(InstallationManager)
    manager.root_tk = ImmediateRoot()
    manager.tasks = tasks
    manager.download_queue = queue.Queue()
    manager.download_jobs = {}
    manager.window = Mock()
    manager._cancel_event = threading.Event()
    manager._lock = threading.Lock()
    manager._install_phase_started = False
    manager._all_finished_notified = False
    manager.is_uninstalling = False
    manager.on_complete_callback = Mock()
    return manager


class InstallationConcurrencyTests(unittest.TestCase):
    def test_mo_download_failure_does_not_reacquire_manager_lock(self):
        task = make_task()
        manager = make_manager([task])
        job = DownloadJob("mo-job", "mo", "zh_cn")
        job.dependent_tasks.add(task)

        worker = threading.Thread(
            target=manager._on_download_complete,
            args=(job, False),
            daemon=True,
        )
        worker.start()
        worker.join(timeout=1)

        self.assertFalse(worker.is_alive(), "MO failure callback deadlocked")
        self.assertEqual(task.status, "failed")
        self.assertTrue(manager._all_finished_notified)
        manager.on_complete_callback.assert_called_once_with()

    def test_downloads_start_after_all_shared_job_dependents_are_registered(self):
        first = make_task("First")
        second = make_task("Second")
        manager = make_manager([first, second])
        manager.download_routes_priority = ["primary"]
        shared_job = DownloadJob("shared", "mo", "zh_cn")
        registration_lock = threading.Lock()
        download_started = threading.Event()
        observed_dependents = []

        def resolve(task):
            with registration_lock:
                shared_job.dependent_tasks.add(task)
                if not shared_job._queued:
                    manager.download_queue.put(shared_job)
                    shared_job._queued = True

        def download_worker():
            observed_dependents.extend(shared_job.dependent_tasks)
            download_started.set()

        manager._resolve_task_version = resolve
        manager._download_worker = download_worker

        with patch("installation.installation_manager.utils.clear_temp_dir"):
            manager._control_thread()

        self.assertTrue(download_started.wait(timeout=1))
        self.assertCountEqual(observed_dependents, [first, second])

    def test_unhandled_download_error_fails_job_and_balances_queue(self):
        task = make_task()
        manager = make_manager([task])
        manager._version_all_done = threading.Event()
        manager._version_all_done.set()
        job = DownloadJob("mo-job", "mo", "zh_cn")
        job.dependent_tasks.add(task)
        manager.download_queue.put(job)
        manager._perform_download = Mock(side_effect=OSError("disk failure"))

        worker = threading.Thread(target=manager._download_worker, daemon=True)
        worker.start()
        worker.join(timeout=2)

        self.assertFalse(worker.is_alive(), "Download worker did not terminate")
        self.assertEqual(task.status, "failed")
        self.assertEqual(manager.download_queue.unfinished_tasks, 0)


if __name__ == "__main__":
    unittest.main()
