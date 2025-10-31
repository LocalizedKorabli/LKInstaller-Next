import os
import shutil
import json
import zipfile
import threading
import queue
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Callable, Optional, Set, Tuple

import requests
import settings
import instance_manager
from game_instance import GameInstance, GameVersion
from localization_sources import global_source_manager
# (移除 _ 的顶层导入)
import installation_utils as utils
from ui.installation_window import InstallProgressWindow

# (从 utils 导入常量)
L10N_CACHE = utils.L10N_CACHE
EE_CACHE = utils.EE_CACHE


class DownloadJob:
    """代表一个单一的下载任务（一个文件）。"""

    def __init__(self, job_id: str, file_type: str, lang_code: str):
        self.job_id = job_id
        self.file_type = file_type
        self.lang_code = lang_code
        self.dependent_tasks: Set['InstallationTask'] = set()
        self.result_path: Optional[Path] = None

        # MO 特有
        self.version_info: Optional[Dict[str, str]] = None


class InstallationTask:
    """代表一个要安装到单个实例的完整任务。"""

    def __init__(self, instance: GameInstance, preset_data: dict, root_tk: tk.Tk):
        self.instance = instance
        self.preset = preset_data
        self.root_tk = root_tk  # (新增)
        self.task_name = f"{instance.name} ({preset_data.get('name', 'Default')})"  # (使用 'Default' 作为硬编码回退)

        self.lang_code: str = preset_data.get('lang_code', 'en')
        self.use_ee: bool = preset_data.get('use_ee', True)
        # (use_mods 已移除)

        # 跟踪依赖
        self.mo_job_id: Optional[str] = None
        self.ee_job_id: Optional[str] = None if not self.use_ee else f"ee_{self.lang_code}"

        self.mo_ready: bool = False
        self.ee_ready: bool = not self.use_ee

        self.status: str = "pending"
        self.log_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None

    def is_ready_for_install(self) -> bool:
        return self.mo_ready and self.ee_ready and self.status == "downloading"


class InstallationManager:
    """
    管理并行下载和安装过程。
    """

    def __init__(self, root_tk: tk.Tk):
        self.root_tk = root_tk
        self.tasks: List[InstallationTask] = []
        self.download_queue: queue.Queue = queue.Queue()
        self.download_jobs: Dict[str, DownloadJob] = {}
        self.window: Optional[InstallProgressWindow] = None

        self.download_routes_priority: List[str] = settings.global_settings.get('download_routes_priority')

        self._cancel_event = threading.Event()
        self._lock = threading.Lock()
        self.on_complete_callback: Optional[Callable] = None

    def start_installation(self, tasks: List[InstallationTask], on_complete_callback: Optional[Callable] = None):
        from localizer import _  # (为 Messagebox 导入)

        # (检查是否有任务已在进行)
        if self.window and self.window.winfo_exists():
            messagebox.showwarning(_('lki.install.title'), _('lki.install.error.already_running'))
            self.window.focus_force()
            return

        self._cancel_event.clear()
        self.tasks = tasks
        self.on_complete_callback = on_complete_callback

        task_names = [t.task_name for t in self.tasks]
        self.window = InstallProgressWindow(self.root_tk, task_names, self.cancel_installation)

        # (为每个任务分配 UI 回调)
        for task in self.tasks:
            task.log_callback = lambda msg, p=..., t=task: self.root_tk.after(
                0, self.window.update_task_progress, t.task_name,
                p if p is not ... else task.progress_callback(), msg
            )
            task.progress_callback = lambda t=task: self.window.widgets[t.task_name]['progress_bar']['value']

        threading.Thread(target=self._control_thread, daemon=True).start()

    def cancel_installation(self):
        from localizer import _  # (为日志导入)
        _log_overall(self, _('lki.install.status.cancelling'))
        self._cancel_event.set()
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except queue.Empty:
                break

    def _control_thread(self):
        from localizer import _  # <-- (修复 UnboundLocalError)

        _log_overall(self, _('lki.install.status.preparing'))
        utils.clear_temp_dir()
        self.download_jobs = {}

        _log_overall(self, _('lki.install.status.getting_versions'))
        version_threads = []
        for task in self.tasks:
            if self._cancel_event.is_set(): return

            t = threading.Thread(target=self._resolve_task_version, args=(task,), daemon=True)
            t.start()
            version_threads.append(t)

        for t in version_threads: t.join()

        if self._cancel_event.is_set(): return

        for job in self.download_jobs.values():
            self.download_queue.put(job)

        if self.download_queue.empty():
            _log_overall(self, _('lki.install.status.no_downloads'))
            self.root_tk.after(0, self._on_download_complete, None, True)
            return

        num_workers = min(6, self.download_queue.qsize())
        _log_overall(self, _('lki.install.status.downloading_files') % self.download_queue.qsize())

        for _ in range(num_workers):
            threading.Thread(target=self._download_worker, daemon=True).start()

    def _resolve_task_version(self, task: InstallationTask):
        from localizer import _  # <-- (修复 UnboundLocalError)

        if self._cancel_event.is_set(): return

        latest_version_obj = task.instance.get_latest_version()
        if not latest_version_obj or not latest_version_obj.exe_version:
            _log_task(task, _('lki.install.status.no_version_info'))
            self._mark_task_failed(task)
            return

        major_version = ".".join(latest_version_obj.exe_version.split('.')[:2])

        source = global_source_manager.get_source(task.lang_code)
        if not source:
            _log_task(task, f"Error: No source found for lang '{task.lang_code}'")
            self._mark_task_failed(task)
            return

        version_info_url_map = source.get_urls(task.instance.type, 'gitee')  # (Gitee 仅用于获取结构)
        if not version_info_url_map or 'version' not in version_info_url_map:
            _log_task(task, f"Error: No version.info URL defined for {task.lang_code}")
            self._mark_task_failed(task)
            return

        sub_version = None
        for route_id in self.download_routes_priority:
            if self._cancel_event.is_set(): return

            route_urls = source.get_urls(task.instance.type, route_id)
            if not route_urls: continue

            v_url = route_urls.get('version')
            _log_task(task, _('lki.install.status.getting_version_from') % route_id)

            try:
                resp = requests.get(v_url, timeout=5)
                resp.raise_for_status()
                lines = resp.text.splitlines()
                if len(lines) >= 2 and lines[1].strip() == major_version:
                    sub_version = lines[0].strip()
                    _log_task(task, _('lki.install.status.version_match_found') % sub_version)
                    break
                else:
                    _log_task(task, _('lki.install.status.version_mismatch') % (lines[1].strip(), major_version))

            except requests.exceptions.RequestException as e:
                _log_task(task, f"{_('lki.install.status.failed')}: {route_id} ({e})")

        if not sub_version:
            _log_task(task, _('lki.install.status.no_compatible_version'))
            self._mark_task_failed(task)
            return

        mo_job_id = f"{task.lang_code}_{major_version}_{sub_version}"
        task.mo_job_id = mo_job_id

        with self._lock:
            if mo_job_id not in self.download_jobs:
                job = DownloadJob(mo_job_id, 'mo', task.lang_code)
                job.version_info = {'main': major_version, 'sub': sub_version}
                self.download_jobs[mo_job_id] = job
            self.download_jobs[mo_job_id].dependent_tasks.add(task)

            if task.use_ee and task.ee_job_id not in self.download_jobs:
                ee_job = DownloadJob(task.ee_job_id, 'ee', task.lang_code)
                self.download_jobs[task.ee_job_id] = ee_job
            if task.use_ee:
                self.download_jobs[task.ee_job_id].dependent_tasks.add(task)

            task.status = "downloading"

    def _download_worker(self):
        from localizer import _  # <-- (修复 UnboundLocalError)

        while not self.download_queue.empty():
            if self._cancel_event.is_set(): return

            try:
                job = self.download_queue.get_nowait()
            except queue.Empty:
                return  # 队列已空

            if not job:
                self.download_queue.task_done()
                continue

            for task in job.dependent_tasks:
                _log_task(task, _('lki.install.status.downloading_file') % job.job_id)

            success, result_path = self._perform_download(job, task)

            if self._cancel_event.is_set():
                self.download_queue.task_done()
                return

            if success:
                job.result_path = result_path

            self.root_tk.after(0, self._on_download_complete, job, success)
            self.download_queue.task_done()

    def _perform_download(self, job: DownloadJob, task: InstallationTask) -> Tuple[bool, Optional[Path]]:
        """执行单个下载作业，包括缓存检查。"""
        from localizer import _  # <-- (修复 UnboundLocalError)

        source = global_source_manager.get_source(job.lang_code)

        # --- 1. MO 文件下载和缓存 ---
        if job.file_type == 'mo':
            cache_path = L10N_CACHE / job.lang_code / job.version_info['main'] / job.version_info['sub']
            mo_path = cache_path / "global.mo"
            info_path = cache_path / "file_info.json"

            if info_path.is_file() and mo_path.is_file():
                try:
                    with open(info_path, 'r') as f:
                        info_data = json.load(f)
                    expected_hash = info_data.get('file_sha256')
                    actual_hash = utils.get_sha256(mo_path)

                    if expected_hash and actual_hash == expected_hash:
                        print(f"Cache HIT for {job.job_id}")
                        return True, mo_path
                except Exception as e:
                    print(f"Cache check failed for {job.job_id}: {e}")

            utils.mkdir(cache_path)

            for route_id in self.download_routes_priority:
                if self._cancel_event.is_set(): return False, None
                urls = source.get_urls(task.instance.type, route_id)  # (类型特定)
                if not urls or not urls.get('mo'):
                    continue

                mo_url = urls.get('mo')

                if self._download_file_with_retry(mo_url, mo_path, f"MO ({job.job_id})", 5):
                    dl_hash = utils.get_sha256(mo_path)
                    with open(info_path, 'w') as f:
                        json.dump({'file_sha256': dl_hash}, f)
                    return True, mo_path

            return False, None

        # --- 2. EE 文件下载和缓存 ---
        if job.file_type == 'ee':
            # (Request 1) 按语言和客户端类型区分缓存
            cache_path = EE_CACHE / job.lang_code / task.instance.type
            ee_zip_path = cache_path / "ee.zip"

            utils.mkdir(cache_path)

            # (新增: 检查 ee.zip 是否已下载)
            if ee_zip_path.is_file() and ee_zip_path.stat().st_size > 0:
                print(f"Cache HIT for {job.job_id} (ee.zip)")
                return True, ee_zip_path

            for route_id in self.download_routes_priority:
                if self._cancel_event.is_set(): return False, None

                urls = source.get_urls(task.instance.type, route_id)
                if not urls or not urls.get('ee'):
                    continue

                ee_url = urls.get('ee')
                if self._download_file_with_retry(ee_url, ee_zip_path, f"EE ({job.job_id})", 5):
                    return True, ee_zip_path

            return False, None

        return False, None

    def _download_file_with_retry(self, url: str, dest: Path, log_prefix: str, timeout: int) -> bool:
        """使用 requests 下载文件。"""
        from localizer import _  # <-- (修复 UnboundLocalError)
        try:
            _log_overall(self, f"{log_prefix}: {_('lki.install.status.connecting')} {url}")
            proxies = {}

            response = requests.get(url, stream=True, proxies=proxies, timeout=timeout)
            response.raise_for_status()

            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancel_event.is_set():
                        _log_overall(self, f"{log_prefix}: {_('lki.install.status.cancelled')}")
                        return False
                    f.write(chunk)

            _log_overall(self, f"{log_prefix}: {_('lki.install.status.success')}")
            return True

        except requests.exceptions.RequestException as e:
            _log_overall(self, f"{log_prefix}: {_('lki.install.status.failed')} ({e})")
            return False

    def _on_download_complete(self, job: Optional[DownloadJob], success: bool):
        """(在主线程中) 在下载完成后更新任务状态。"""
        from localizer import _  # <-- (修复 UnboundLocalError)

        if self._cancel_event.is_set(): return

        tasks_to_check = []

        if job and success:
            for task in job.dependent_tasks:
                with self._lock:
                    if job.file_type == 'mo':
                        task.mo_ready = True
                    elif job.file_type == 'ee':
                        task.ee_ready = True
                    tasks_to_check.append(task)
        elif job:
            for task in job.dependent_tasks:
                self._mark_task_failed(task, _('lki.install.status.download_failed') % job.job_id)
        elif not job and success:
            tasks_to_check = self.tasks

        for task in tasks_to_check:
            if task.is_ready_for_install():
                task.status = "installing"
                _log_task(task, _('lki.install.status.starting_install'), 0)
                threading.Thread(target=self._install_worker, args=(task,), daemon=True).start()

        self._check_if_all_finished()

    def _install_worker(self, task: InstallationTask):
        """(在线程中) 为单个实例执行文件打包和复制。"""
        from localizer import _  # <-- (修复 UnboundLocalError)

        try:
            if self._cancel_event.is_set(): return

            _log_task(task, _('lki.install.status.preparing_files'), 10)

            mo_job = self.download_jobs[task.mo_job_id]
            mo_file_path = mo_job.result_path

            ee_zip_path: Optional[Path] = None
            if task.use_ee:
                ee_job = self.download_jobs[task.ee_job_id]
                ee_zip_path = ee_job.result_path

            if not mo_file_path or not mo_file_path.is_file():
                raise Exception(f"MO file {mo_file_path} not found!")
            if task.use_ee and (not ee_zip_path or not ee_zip_path.is_file()):
                raise Exception(f"EE file {ee_zip_path} not found!")

            _log_task(task, _('lki.install.status.writing_config'), 25)
            locale_config_path = utils.write_locale_config_to_temp(task.lang_code)

            _log_task(task, _('lki.install.status.packing_core'), 40)
            core_mod_files = {
                "texts/ru/LC_MESSAGES/global.mo": mo_file_path
            }
            if locale_config_path:
                core_mod_files["locale_config.xml"] = locale_config_path

            core_mkmod_path = utils.TEMP_DIR / f"{task.instance.instance_id}_core.mkmod"
            utils.create_mkmod(core_mkmod_path, core_mod_files)

            # --- (Request 2) EE 解压逻辑已修改 ---
            _log_task(task, _('lki.install.status.packing_ee'), 60)
            ee_mkmod_path: Optional[Path] = None
            if task.use_ee and ee_zip_path:

                # (Request 2) 使用实例 ID (即实例路径的sha256) 作为唯一的临时目录
                # 这也从根本上解决了 WinError 183 竞态条件
                ee_unpack_dir = utils.EE_UNPACK_TEMP / task.instance.instance_id

                _log_task(task, "正在解压 EE 文件...", 61)  # (使用你日志中已有的字符串)

                # (重要) 必须在解压前清理，以防止同一实例切换语言时发生冲突
                if ee_unpack_dir.exists():
                    try:
                        shutil.rmtree(ee_unpack_dir)
                    except OSError as e:
                        _log_task(task, f"警告: 无法清理临时 EE 目录: {e}")

                utils.mkdir(ee_unpack_dir)
                with zipfile.ZipFile(ee_zip_path, 'r') as zf:
                    utils.process_possible_gbk_zip(zf).extractall(ee_unpack_dir)

                # --- 缓存逻辑和锁已全部移除 ---

                ee_files_to_add: Dict[str, Path] = {}
                # (后续的 os.walk 逻辑保持不变)
                for root, dirnames, files in os.walk(ee_unpack_dir):
                    for file in files:
                        local_path = Path(root) / file
                        arcname = str(local_path.relative_to(ee_unpack_dir)).replace("\\", "/")
                        ee_files_to_add[arcname] = local_path

                if ee_files_to_add:
                    ee_mkmod_path = utils.TEMP_DIR / f"{task.instance.instance_id}_ee.mkmod"
                    utils.create_mkmod(ee_mkmod_path, ee_files_to_add)
            # --- EE 逻辑修改结束 ---

            if self._cancel_event.is_set(): return

            for version_folder in task.instance.versions:
                exe_version = version_folder.exe_version or ""
                major_version = ".".join(exe_version.split('.')[:2])

                # (新增) 为这个循环定义所有路径
                mods_dir = version_folder.bin_folder_path / "mods"
                dest_core_mod_path = mods_dir / "lk_i18n_mod.mkmod"
                dest_ee_mod_path = mods_dir / "lk_i18n_ee.mkmod"
                info_json_path = task.instance.path / "lki" / "info" / version_folder.bin_folder_name
                info_file = info_json_path / "installation_info.json"

                if major_version == mo_job.version_info['main']:
                    # --- (这是我们现有的安装逻辑) ---
                    _log_task(task, _('lki.install.status.installing_to') % version_folder.bin_folder_name, 80)
                    utils.mkdir(mods_dir)

                    shutil.copy(core_mkmod_path, dest_core_mod_path)

                    files_info = {}
                    try:
                        files_info["lk_i18n_mod.mkmod"] = utils.get_sha256(dest_core_mod_path)

                        if ee_mkmod_path and ee_mkmod_path.is_file():
                            shutil.copy(ee_mkmod_path, dest_ee_mod_path)
                            files_info["lk_i18n_ee.mkmod"] = utils.get_sha256(dest_ee_mod_path)

                    except Exception as e:
                        print(f"[{task.task_name}] 无法计算 mkmod 的哈希值: {e}")

                    utils.mkdir(info_json_path)
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "version": f"{mo_job.version_info['main']}.{mo_job.version_info['sub']}",
                            "lang_code": task.lang_code,
                            "files": files_info
                        }, f, indent=2)

                else:
                    # --- (BUG 修复：必须清理陈旧版本) ---
                    _log_task(task, f"正在清理陈旧版本: {version_folder.bin_folder_name}", 85)
                    try:
                        # 删除 .mkmod 文件
                        if dest_core_mod_path.is_file():
                            os.remove(dest_core_mod_path)
                        if dest_ee_mod_path.is_file():
                            os.remove(dest_ee_mod_path)

                        # 删除 info.json
                        if info_file.is_file():
                            os.remove(info_file)

                    except OSError as e:
                        _log_task(task, f"警告: 无法清理 {version_folder.bin_folder_name} 中的陈旧文件: {e}")
                    # --- (BUG 修复结束) ---

            _log_task(task, _('lki.install.status.done'), 100)

            self._mark_task_finished(task, success=True)

        except Exception as e:
            # print(f"Error in install worker for {task.task_name}: {e}")
            # self._mark_task_failed(task, str(e))
            import traceback  # 导入 traceback 模块
            print(f"Error in install worker for {task.task_name}: {e}")
            traceback.print_exc()  # 打印完整的堆栈跟踪
            self._mark_task_failed(task, str(e))

    def _mark_task_failed(self, task: InstallationTask, reason: str = ""):
        from localizer import _  # <-- (修复 UnboundLocalError)
        with self._lock:
            task.status = "failed"
            _log_task(task, f"{_('lki.install.status.failed')}: {reason}", 100)
            self.root_tk.after(0, self.window.mark_task_complete, task.task_name, False)
        self._check_if_all_finished()

    def _mark_task_finished(self, task: InstallationTask, success: bool):
        with self._lock:
            task.status = "done" if success else "failed"
            self.root_tk.after(0, self.window.mark_task_complete, task.task_name, success)
        self._check_if_all_finished()

    def _check_if_all_finished(self):
        from localizer import _  # <-- (修复 UnboundLocalError)
        with self._lock:
            all_done = all(t.status in ["done", "failed"] for t in self.tasks)
            if all_done:
                _log_overall(self, _('lki.install.status.all_done'))
                self.root_tk.after(0, self.window.all_tasks_finished)
                if self.on_complete_callback:
                    self.root_tk.after(0, self.on_complete_callback)


# --- (日志记录助手) ---

def _log_overall(manager: InstallationManager, message: str):
    """安全地记录到主 UI。"""
    print(f"[Overall] {message}")
    if manager.window:
        manager.root_tk.after(0, manager.window.update_overall_status, message)


def _log_task(task: InstallationTask, message: str, progress: Optional[float] = None):
    """安全地记录到任务的 UI。"""
    print(f"[{task.task_name}] {message}")
    if progress is None:
        progress = task.progress_callback()
    if task.log_callback:
        # (使用 ... 来表示“无变化”)
        task.root_tk.after(0, task.log_callback, message, progress if progress is not None else ...)