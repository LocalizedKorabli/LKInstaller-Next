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
        self.use_fonts: bool = preset_data.get('use_fonts', True)  # <-- (新增)

        # 跟踪依赖
        self.mo_job_id: Optional[str] = None
        self.ee_job_id: Optional[str] = None if not self.use_ee else f"ee_{self.lang_code}"
        self.fo_job_id: Optional[str] = None if not self.use_fonts else "fonts_srcwagon"  # <-- (新增)

        self.mo_ready: bool = False
        self.ee_ready: bool = not self.use_ee
        self.fo_ready: bool = not self.use_fonts  # <-- (新增)

        self.status: str = "pending"
        self.log_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None

    def is_ready_for_install(self) -> bool:
        return self.mo_ready and self.ee_ready and self.fo_ready and self.status == "downloading"


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
        self.is_uninstalling: bool = False  # (新增)

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
        self.is_uninstalling = False  # (新增)

        task_names = [t.task_name for t in self.tasks]
        # (已修改：传入 title 和 strings)
        self.window = InstallProgressWindow(self.root_tk, task_names, self.cancel_installation,
                                            title=_('lki.install.title'),
                                            starting_text=_('lki.install.status.starting'),
                                            pending_text=_('lki.install.status.pending'))

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
        # (已修改：根据状态使用不同的字符串)
        cancel_key = 'lki.uninstall.status.cancelling' if self.is_uninstalling else 'lki.install.status.cancelling'
        _log_overall(self, _(cancel_key))
        self._cancel_event.set()
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except queue.Empty:
                break

    def start_uninstallation(self, tasks: List[InstallationTask], on_complete_callback: Optional[Callable] = None):
        from localizer import _

        if self.window and self.window.winfo_exists():
            messagebox.showwarning(_('lki.uninstall.title'), _('lki.install.error.already_running'))
            self.window.focus_force()
            return

        self._cancel_event.clear()
        self.tasks = tasks
        self.on_complete_callback = on_complete_callback
        self.is_uninstalling = True  # (新增)

        task_names = [t.task_name for t in self.tasks]
        # (新增：使用卸载标题)
        self.window = InstallProgressWindow(self.root_tk, task_names, self.cancel_installation,
                                            title=_('lki.uninstall.title'),
                                            starting_text=_('lki.uninstall.status.starting'),
                                            pending_text=_('lki.uninstall.status.pending'))

        for task in self.tasks:
            task.log_callback = lambda msg, p=..., t=task: self.root_tk.after(
                0, self.window.update_task_progress, t.task_name,
                p if p is not ... else task.progress_callback(), msg
            )
            task.progress_callback = lambda t=task: self.window.widgets[t.task_name]['progress_bar']['value']

        threading.Thread(target=self._uninstall_control_thread, daemon=True).start()

    # (新增：卸载控制线程)
    def _uninstall_control_thread(self):
        from localizer import _
        _log_overall(self, _('lki.uninstall.status.starting'))

        for task in self.tasks:
            if self._cancel_event.is_set(): return
            task.status = "running"  # (使用 'running' 状态)
            threading.Thread(target=self._uninstall_worker, args=(task,), daemon=True).start()

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
                proxies = self._get_configured_proxies()
                resp = requests.get(v_url, timeout=5, proxies=proxies)
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

            # --- (新增：字体任务) ---
            if task.use_fonts and task.fo_job_id not in self.download_jobs:
                fo_job = DownloadJob(task.fo_job_id, 'fonts', 'global')
                self.download_jobs[task.fo_job_id] = fo_job
            if task.use_fonts:
                self.download_jobs[task.fo_job_id].dependent_tasks.add(task)
            # --- (新增结束) ---

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

    def _get_configured_proxies(self) -> Optional[Dict[str, str]]:
        """
        从全局设置中读取代理配置，并返回 requests 库所需的字典。
        - 'disabled': 返回 {'http': None, 'https': None}
        - 'system':   返回 None (requests 会自动检测)
        - 'manual':   返回 {'http': '...', 'https': '...'}
        """
        proxy_mode = settings.global_settings.get('proxy.mode', 'disabled')

        if proxy_mode == 'disabled':
            return {'http': None, 'https': None}

        if proxy_mode == 'system':
            return None  # requests 库会自动处理

        if proxy_mode == 'manual':
            host = settings.global_settings.get('proxy.host', '')
            port = settings.global_settings.get('proxy.port', '')
            user = settings.global_settings.get('proxy.user', '')
            password = settings.global_settings.get('proxy.password', '')

            if not host or not port:
                print("警告: 代理模式为 'manual'，但未配置主机或端口。")
                return {'http': None, 'https': None}

            if user and password:
                proxy_url = f"http://{user}:{password}@{host}:{port}"
            elif user:
                proxy_url = f"http://{user}@{host}:{port}"
            else:
                proxy_url = f"http://{host}:{port}"

            # (假设代理同时适用于 http 和 https)
            return {
                'http': proxy_url,
                'https': proxy_url
            }

        return {'http': None, 'https': None}  # (默认禁用)

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

        # --- 3. 字体优化包 (.mkmod 缓存) ---
        if job.file_type == 'fonts':
            from localizer import _  # (为日志导入)

            asset_id = job.job_id  # (例如 "fonts_srcwagon")
            urls = None

            # 1. (新) 按优先级查找 URL
            for route_id in self.download_routes_priority:
                if self._cancel_event.is_set(): return False, None

                urls = global_source_manager.get_global_asset_urls(asset_id, route_id)
                if urls and urls.get('zip') and urls.get('version'):
                    _log_overall(self, f"Fonts: Using route {route_id}")
                    break

            if not urls:
                _log_overall(self, "Fonts: No valid download URLs found.")
                return False, None

            VER_URL = urls.get('version')
            ZIP_URL = urls.get('zip')

            # --- (从这里开始，缓存逻辑与我之前的提议相同) ---
            cache_dir = utils.FONTS_CACHE
            mkmod_path = cache_dir / "srcwagon_mk.mkmod"
            info_path = cache_dir / "cache_info.json"
            utils.mkdir(cache_dir)

            proxies = self._get_configured_proxies()
            remote_version = None

            # 2. 获取远程版本
            try:
                resp = requests.get(VER_URL, timeout=5, proxies=proxies)
                resp.raise_for_status()
                remote_info = resp.json()
                remote_version = remote_info.get('version')
            except Exception as e:
                _log_overall(self, f"Font version check failed: {e}")
                return False, None  # (继续尝试其他路由可能更健壮, 但目前保持简单)

            if not remote_version:
                _log_overall(self, "Font version info invalid.")
                return False, None

            # 3. 检查缓存
            if info_path.is_file() and mkmod_path.is_file():
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        local_info = json.load(f)
                    local_version = local_info.get('version')
                    expected_hash = local_info.get('file_sha256')

                    if local_version == remote_version:
                        actual_hash = utils.get_sha256(mkmod_path)
                        if actual_hash == expected_hash:
                            print(f"Cache HIT for {job.job_id}")
                            return True, mkmod_path
                except Exception as e:
                    print(f"Font cache check failed: {e}")

            # 4. 缓存未命中 - 下载并重新打包
            _log_overall(self, _('lki.install.status.packing_fonts'))

            temp_zip_path = utils.TEMP_DIR / "fonts.zip"
            # (注意：我们在这里使用已配置的代理)
            if not self._download_file_with_retry(ZIP_URL, temp_zip_path, f"Fonts ({job.job_id})", 10):
                return False, None

            unpack_dir = utils.FONTS_UNPACK_TEMP
            if unpack_dir.exists():
                shutil.rmtree(unpack_dir)
            utils.mkdir(unpack_dir)

            with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                utils.process_possible_gbk_zip(zf).extractall(unpack_dir)

            files_to_add: Dict[str, Path] = {}
            for root, _, files in os.walk(unpack_dir):
                for file in files:
                    local_path = Path(root) / file
                    arcname = str(local_path.relative_to(unpack_dir)).replace("\\", "/")
                    files_to_add[arcname] = local_path

            if not files_to_add:
                _log_overall(self, "Font zip was empty.")
                return False, None

            utils.create_mkmod(mkmod_path, files_to_add)

            # 5. 写入新缓存信息
            new_hash = utils.get_sha256(mkmod_path)
            try:
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump({'version': remote_version, 'file_sha256': new_hash}, f)
            except Exception as e:
                print(f"Error writing font cache info: {e}")

            return True, mkmod_path
        # --- (新增结束) ---

        return False, None

    def _download_file_with_retry(self, url: str, dest: Path, log_prefix: str, timeout: int) -> bool:
        """使用 requests 下载文件。"""
        from localizer import _  # <-- (修复 UnboundLocalError)
        try:
            _log_overall(self, f"{log_prefix}: {_('lki.install.status.connecting')} {url}")
            proxies = self._get_configured_proxies()

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
                    elif job.file_type == 'fonts':  # <-- (新增)
                        task.fo_ready = True  # <-- (新增)
                    tasks_to_check.append(task)
        elif job:  # 下载失败
            from localizer import _  # (为日志导入)
            for task in job.dependent_tasks:
                with self._lock:
                    if job.file_type == 'mo':
                        # MO 是关键任务，使整个任务失败
                        self._mark_task_failed(task, _('lki.install.status.download_failed') % job.job_id)
                    elif job.file_type == 'ee':
                        # EE 不是关键任务，记录日志并解除阻塞
                        _log_task(task, _('lki.install.status.ee_failed_skip') % job.job_id)
                        task.ee_ready = True  # <-- 设为 True 以便安装可以开始
                        tasks_to_check.append(task)
                    elif job.file_type == 'fonts':
                        # 字体不是关键任务，记录日志并解除阻塞
                        _log_task(task, _('lki.install.status.fonts_failed_skip') % job.job_id)
                        task.fo_ready = True  # <-- 设为 True 以便安装可以开始
                        tasks_to_check.append(task)
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
        from localizer import _

        # (新增) 跟踪非关键错误
        non_critical_errors: List[str] = []

        try:
            if self._cancel_event.is_set(): return

            _log_task(task, _('lki.install.status.preparing_files'), 10)

            mo_job = self.download_jobs[task.mo_job_id]
            mo_file_path = mo_job.result_path

            ee_zip_path: Optional[Path] = None
            fo_mkmod_path: Optional[Path] = None

            if task.use_ee:
                ee_job = self.download_jobs[task.ee_job_id]
                ee_zip_path = ee_job.result_path

            if task.use_fonts:
                fo_job = self.download_jobs[task.fo_job_id]
                fo_mkmod_path = fo_job.result_path

            # --- 关键检查 ---
            if not mo_file_path or not mo_file_path.is_file():
                raise Exception(f"MO file {mo_file_path} not found!")
            # --- 关键检查结束 ---

            # --- (修改) 非关键检查 ---
            if task.use_ee and (not ee_zip_path or not ee_zip_path.is_file()):
                _log_task(task, _('lki.install.status.ee_failed_skip') % task.ee_job_id)
                non_critical_errors.append("EE")
                ee_zip_path = None  # 确保后续步骤跳过它

            if task.use_fonts and (not fo_mkmod_path or not fo_mkmod_path.is_file()):
                _log_task(task, _('lki.install.status.fonts_failed_skip') % task.fo_job_id)
                non_critical_errors.append("Fonts")
                fo_mkmod_path = None  # 确保后续步骤跳过它
            # --- 非关键检查结束 ---

            _log_task(task, _('lki.install.status.writing_config'), 25)
            locale_config_path = utils.write_locale_config_to_temp(task.lang_code)

            # --- 关键打包 ---
            _log_task(task, _('lki.install.status.packing_core'), 40)
            core_mod_files = {
                "texts/ru/LC_MESSAGES/global.mo": mo_file_path
            }
            if locale_config_path:
                core_mod_files["locale_config.xml"] = locale_config_path

            core_mkmod_path = utils.TEMP_DIR / f"{task.instance.instance_id}_core.mkmod"
            utils.create_mkmod(core_mkmod_path, core_mod_files)
            # --- 关键打包结束 ---

            # --- (修改) 非关键打包：EE ---
            _log_task(task, _('lki.install.status.packing_ee'), 60)
            ee_mkmod_path: Optional[Path] = None
            if task.use_ee and ee_zip_path:
                try:
                    ee_unpack_dir = utils.EE_UNPACK_TEMP / task.instance.instance_id
                    _log_task(task, "正在解压 EE 文件...", 61)

                    if ee_unpack_dir.exists():
                        shutil.rmtree(ee_unpack_dir)

                    utils.mkdir(ee_unpack_dir)
                    with zipfile.ZipFile(ee_zip_path, 'r') as zf:
                        utils.process_possible_gbk_zip(zf).extractall(ee_unpack_dir)

                    ee_files_to_add: Dict[str, Path] = {}
                    for root, dirnames, files in os.walk(ee_unpack_dir):
                        for file in files:
                            local_path = Path(root) / file
                            arcname = str(local_path.relative_to(ee_unpack_dir)).replace("\\", "/")
                            ee_files_to_add[arcname] = local_path

                    if ee_files_to_add:
                        ee_mkmod_path = utils.TEMP_DIR / f"{task.instance.instance_id}_ee.mkmod"
                        utils.create_mkmod(ee_mkmod_path, ee_files_to_add)
                except Exception as e:
                    _log_task(task, f"EE pack failed: {e}")
                    non_critical_errors.append("EE Pack")
                    ee_mkmod_path = None  # 确保不安装
            # --- 非关键打包结束 ---

            if self._cancel_event.is_set(): return

            for version_folder in task.instance.versions:
                exe_version = version_folder.exe_version or ""
                major_version = ".".join(exe_version.split('.')[:2])

                mods_dir = version_folder.bin_folder_path / "mods"
                dest_core_mod_path = mods_dir / "lk_i18n_mod.mkmod"
                dest_ee_mod_path = mods_dir / "lk_i18n_ee.mkmod"
                dest_fo_mod_path = mods_dir / "srcwagon_mk.mkmod"
                info_json_path = task.instance.path / "lki" / "info" / version_folder.bin_folder_name
                info_file = info_json_path / "installation_info.json"

                if major_version == mo_job.version_info['main']:
                    # --- 关键安装步骤 ---
                    _log_task(task, _('lki.install.status.installing_to') % version_folder.bin_folder_name, 80)
                    utils.mkdir(mods_dir)

                    shutil.copy(core_mkmod_path, dest_core_mod_path)
                    files_info = {"i18n": {}, "ee": {}, "font": {}}
                    try:
                        # (修改) 2. 使用相对路径作为键，存储在 "i18n" 下
                        core_rel_path = f"mods/{dest_core_mod_path.name}"
                        files_info["i18n"][core_rel_path] = utils.get_sha256(dest_core_mod_path)

                        if ee_mkmod_path and ee_mkmod_path.is_file():
                            shutil.copy(ee_mkmod_path, dest_ee_mod_path)
                            # (修改) 3. 存储在 "ee" 下
                            ee_rel_path = f"mods/{dest_ee_mod_path.name}"
                            files_info["ee"][ee_rel_path] = utils.get_sha256(dest_ee_mod_path)

                        if fo_mkmod_path and fo_mkmod_path.is_file():
                            shutil.copy(fo_mkmod_path, dest_fo_mod_path)
                            # (修改) 4. 存储在 "font" 下
                            font_rel_path = f"mods/{dest_fo_mod_path.name}"
                            files_info["font"][font_rel_path] = utils.get_sha256(dest_fo_mod_path)

                    except Exception as e:
                        print(f"[{task.task_name}] 无法计算 mkmod 的哈希值: {e}")
                    # --- 非关键安装结束 ---

                    # --- 关键的 Info.json 写入 ---
                    utils.mkdir(info_json_path)
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "version": f"{mo_job.version_info['main']}.{mo_job.version_info['sub']}",
                            "l10n_sub_version": mo_job.version_info['sub'],
                            "lang_code": task.lang_code,
                            "files": files_info
                        }, f, indent=2)
                    # --- 关键写入结束 ---

                else:
                    # --- (修改) 非关键清理 ---
                    _log_task(task, _('lki.install.status.inactive_skip') % version_folder.bin_folder_name, 85)
                    try:
                        if dest_core_mod_path.is_file():
                            os.remove(dest_core_mod_path)
                        if dest_ee_mod_path.is_file():
                            os.remove(dest_ee_mod_path)
                        if dest_fo_mod_path.is_file():
                            os.remove(dest_fo_mod_path)

                        utils.mkdir(info_json_path)
                        with open(info_file, 'w', encoding='utf-8') as f:
                            json.dump({
                                "version": "INACTIVE",
                                "l10n_sub_version": None,
                                "files": {}
                            }, f, indent=2)
                    except OSError as e:
                        _log_task(task, f"警告: 无法清理或写入 {version_folder.bin_folder_name} 的非活跃状态: {e}")
                    # --- 非关键清理结束 ---

            # --- (修改) 检查最终状态 ---
            if non_critical_errors:
                error_summary = ", ".join(list(set(non_critical_errors)))  # (去重)
                _log_task(task, _('lki.install.status.warn_done') % error_summary, 100)
                self._mark_task_finished(task, success=True, status_key='lki.install.status.warn_done_short')
            else:
                _log_task(task, _('lki.install.status.done'), 100)
                self._mark_task_finished(task, success=True, status_key='lki.install.status.done')
            # --- 修改结束 ---

        except Exception as e:
            # (这现在只捕获关键错误)
            import traceback
            print(f"Error in install worker for {task.task_name}: {e}")
            traceback.print_exc()
            self._mark_task_failed(task, str(e))

    def _uninstall_worker(self, task: InstallationTask):
        """(在线程中) 为单个实例执行文件删除。"""
        from localizer import _
        import os
        import json

        try:
            instance = task.instance
            if not instance.versions:
                _log_task(task, _('lki.install.error.no_version_for_instance') % instance.name, 100)
                self._mark_task_finished(task, success=True, status_key='lki.uninstall.status.done')
                return

            total_versions = len(instance.versions)
            for i, game_version in enumerate(instance.versions):
                if self._cancel_event.is_set(): return

                progress = (i / total_versions) * 100
                _log_task(task, _('lki.uninstall.status.removing_files_for') % game_version.bin_folder_name, progress)

                info_file = game_version.game_root_path / "lki" / "info" / game_version.bin_folder_name / "installation_info.json"

                if not info_file.is_file():
                    _log_task(task, _('lki.uninstall.status.no_info_skip') % game_version.bin_folder_name, progress)
                    continue

                # 1. 读取 info.json 来获取文件列表
                files_to_delete: List[Path] = []
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    files_data = data.get("files", {})
                    for component_name, path_dict in files_data.items():
                        for relative_path in path_dict.keys():
                            # relative_path 是 "mods/lk_i18n_mod.mkmod"
                            absolute_path = game_version.bin_folder_path / relative_path
                            files_to_delete.append(absolute_path)

                except Exception as e:
                    _log_task(task, f"Error reading {info_file.name}: {e}")
                    # (即使读取失败，我们仍将尝试删除 info_file)

                # 2. 删除所有引用的文件
                for file_path in files_to_delete:
                    try:
                        if file_path.is_file():
                            os.remove(file_path)
                    except OSError as e:
                        _log_task(task, f"Warn: Could not remove {file_path.name}: {e}")

                # 3. (最后) 删除 info.json 文件本身
                try:
                    os.remove(info_file)
                except OSError as e:
                    _log_task(task, f"Error: Could not remove {info_file.name}: {e}")

            # (所有版本循环完毕)
            _log_task(task, _('lki.uninstall.status.done'), 100)
            self._mark_task_finished(task, success=True, status_key='lki.uninstall.status.done')

        except Exception as e:
            import traceback
            print(f"Error in uninstall worker for {task.task_name}: {e}")
            traceback.print_exc()
            self._mark_task_failed(task, str(e))

    def _mark_task_failed(self, task: InstallationTask, reason: str = ""):
        from localizer import _
        with self._lock:
            task.status = "failed"
            # (已修改：根据状态使用不同的失败字符串)
            status_key = 'lki.uninstall.status.failed' if self.is_uninstalling else 'lki.install.status.failed'
            status_text = f"{_(status_key)}: {reason}"
            _log_task(task, status_text, 100)  # (日志现在也使用最终文本)

    def _mark_task_finished(self, task: InstallationTask, success: bool, status_key: str = 'lki.install.status.done'):
        from localizer import _
        with self._lock:
            task.status = "done"  # (如果 success=True，我们总是设置 "done")
            status_text = _(status_key)  # (获取 "完成" 或 "完成（有警告）")
            self.root_tk.after(0, self.window.mark_task_complete, task.task_name, success, status_text)
        self._check_if_all_finished()

    def _check_if_all_finished(self):
        from localizer import _  # <-- (修复 UnboundLocalError)
        with self._lock:
            all_done = all(t.status in ["done", "failed"] for t in self.tasks)
            if all_done:
                # (已修改：根据状态使用不同的完成字符串)
                all_done_key = 'lki.uninstall.status.all_done' if self.is_uninstalling else 'lki.install.status.all_done'
                _log_overall(self, _(all_done_key))
                self.root_tk.after(0, self.window.all_tasks_finished)


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