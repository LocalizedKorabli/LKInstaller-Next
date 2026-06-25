#  LKInstaller Next, a blazing-speed localization installer for Mir Korabley
#  Copyright (C) 2025 LocalizedKorabli <localizedkorabli@outlook.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
import os
import queue
import shutil
import threading
import tkinter as tk
import zipfile
from pathlib import Path

from installation.installation_utils import get_files_may_overwrite
from core.logger import log
from tkinter import messagebox
from typing import List, Dict, Callable, Optional, Set, Tuple

import requests

# (移除 _ 的顶层导入)
from core import settings
import installation.installation_utils as utils
from core import utils as root_utils
from instance.game_instance import GameInstance
from installation.localization_sources import global_source_manager, get_route_id_to_name
from ui.windows.window_action import ActionProgressWindow

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
        self._queued: bool = False

        # MO 特有
        self.version_info: Optional[Dict[str, str]] = None


class InstallationTask:
    """代表一个要安装到单个实例的完整任务。"""

    def __init__(self, instance: GameInstance, preset_data: dict, root_tk: tk.Tk):
        from core.localizer import _  # (新增局部导入)
        self.instance = instance
        self.preset = preset_data
        self.root_tk = root_tk  # (新增)
        # (已修改：使用本地化键回退)
        self.task_name = f"{instance.name} ({preset_data.get('name', _('lki.preset.default.name'))})"

        self.lang_code: str = preset_data.get('lang_code', 'en')
        self.use_ee: bool = preset_data.get('use_ee', False)
        self.use_fonts: str = preset_data.get('use_fonts', "")  # 字体 ID, ""=不安装, True=推荐
        # 解析 True → 语言默认字体
        if self.use_fonts is True:
            from installation.localization_sources import global_source_manager
            self.use_fonts = global_source_manager.get_default_font_id(self.lang_code)
        self.use_mods: bool = preset_data.get('use_mods', False)
        self.use_lk_mods: bool = preset_data.get('use_lk_mods')
        # None = 跟随全局设置
        if self.use_lk_mods is None:
            from core import settings as core_settings
            self.use_lk_mods = core_settings.global_settings.get('use_lk_mods', False)

        # 跟踪依赖
        self.mo_job_id: Optional[str] = None
        self.ee_job_id: Optional[str] = None if not self.use_ee else f"ee_{self.lang_code}"
        self.fo_job_id: Optional[str] = None if not self.use_fonts else self.use_fonts  # 字体 ID 作为 job_id

        self.mo_ready: bool = False
        self.ee_ready: bool = not self.use_ee
        self.fo_ready: bool = not bool(self.use_fonts)  # <-- (新增)

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
        self.window: Optional[ActionProgressWindow] = None
        self.download_routes_priority: List[str] = []
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()
        self.on_complete_callback: Optional[Callable] = None
        self.is_uninstalling: bool = False  # (新增)
        self._install_phase_started = False  # <-- (修改 1: 新增标志)

    def start_installation(self, tasks: List[InstallationTask], on_complete_callback: Optional[Callable] = None):
        from core.localizer import _  # (为 Messagebox 导入)

        # (检查是否有任务已在进行)
        if self.window and self.window.winfo_exists():
            messagebox.showwarning(_('lki.install.title'), _('lki.install.error.already_running'))
            self.window.focus_force()
            return

        self._cancel_event.clear()
        self.tasks = tasks
        self.on_complete_callback = on_complete_callback
        self.is_uninstalling = False  # (新增)
        self._install_phase_started = False  # <-- (修改 2: 重置标志)
        self.download_routes_priority = settings.global_settings.get('download_routes_priority')

        tasks_data = {t.task_name : t.instance for t in self.tasks}
        # (已修改：传入 title 和 strings)
        self.window = ActionProgressWindow(self.root_tk, tasks_data, self.cancel_installation,
                                           title=_('lki.install.title'),
                                           starting_text=_('lki.install.status.starting'),
                                           pending_text=_('lki.install.status.pending'))

        self._assign_task_ui_callbacks()

        threading.Thread(target=self._control_thread, daemon=True).start()

    def cancel_installation(self):
        from core.localizer import _  # (为日志导入)
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
        from core.localizer import _

        if self.window and self.window.winfo_exists():
            messagebox.showwarning(_('lki.uninstall.title'), _('lki.install.error.already_running'))
            self.window.focus_force()
            return

        self._cancel_event.clear()
        self.tasks = tasks
        self.on_complete_callback = on_complete_callback
        self.is_uninstalling = True  # (新增)

        tasks_data = {t.task_name : None for t in self.tasks}
        # (新增：使用卸载标题)
        self.window = ActionProgressWindow(self.root_tk, tasks_data, self.cancel_installation,
                                           title=_('lki.uninstall.title'),
                                           starting_text=_('lki.uninstall.status.starting'),
                                           pending_text=_('lki.uninstall.status.pending'))

        self._assign_task_ui_callbacks()

        threading.Thread(target=self._uninstall_control_thread, daemon=True).start()

    def _assign_task_ui_callbacks(self):
        """为所有任务分配 UI 进度回调和日志回调。"""
        for task in self.tasks:
            def safe_progress_callback(t=task):
                try:
                    if self.window and self.window.winfo_exists():
                        return self.window.widgets[t.task_name]['progress_bar']['value']
                except (tk.TclError, KeyError):
                    pass
                return 0.0

            task.log_callback = lambda msg, p=..., t=task: self.root_tk.after(
                0, self.window.update_task_progress, t.task_name,
                p if p is not ... else safe_progress_callback(t), msg
            )
            task.progress_callback = safe_progress_callback

    # (新增：卸载控制线程)
    def _uninstall_control_thread(self):
        from core.localizer import _
        _log_overall(self, _('lki.uninstall.status.starting'))

        for task in self.tasks:
            if self._cancel_event.is_set(): return
            task.status = "running"  # (使用 'running' 状态)
            threading.Thread(target=self._uninstall_worker, args=(task,), daemon=True).start()

    def _control_thread(self):
        from core.localizer import _

        _log_overall(self, _('lki.install.status.preparing_files'))
        utils.clear_temp_dir()
        self.download_jobs = {}

        _log_overall(self, _('lki.install.status.getting_versions'))

        self._pending_version_count = len(self.tasks)
        self._version_all_done = threading.Event()

        def _resolve_and_notify(task):
            try:
                self._resolve_task_version(task)
            finally:
                with self._lock:
                    self._pending_version_count -= 1
                    if self._pending_version_count == 0:
                        self._version_all_done.set()

        for task in self.tasks:
            if self._cancel_event.is_set():
                return
            t = threading.Thread(target=_resolve_and_notify, args=(task,), daemon=True)
            t.start()

        num_workers = min(6, max(len(self.tasks) * 3, 1))
        _log_overall(self, _('lki.install.status.downloading_files') % (len(self.tasks) * 3))

        for _i in range(num_workers):
            threading.Thread(target=self._download_worker, daemon=True).start()

        self._version_all_done.wait()

        if self._cancel_event.is_set():
            return

        if self.download_queue.empty():
            _log_overall(self, _('lki.install.status.install_phase'))
            self._install_phase_started = True
            self.root_tk.after(0, self._on_download_complete, None, True)

    def _resolve_task_version(self, task: InstallationTask):
        from core.localizer import _

        if self._cancel_event.is_set(): return

        source = global_source_manager.get_source(task.lang_code)
        if not source:
            self._mark_task_failed(task, _('lki.install.error.no_source') % task.lang_code)
            return

        available_route_ids = source.get_available_route_ids()
        has_valid_config = False

        for route_id in available_route_ids:
            info_map = source.get_urls(task.instance.type, route_id)

            if info_map and 'version' in info_map:
                has_valid_config = True
                break

        if not has_valid_config:
            self._mark_task_failed(task, _('lki.install.error.no_version_url') % task.lang_code)
            return

        route_remote = {}  # route_id → remote_major, 在本task内复用
        for game_version_obj in task.instance.versions:
            if self._cancel_event.is_set(): return

            if not game_version_obj or not game_version_obj.exe_version:
                log(f"Warning: No valid executable version found in {game_version_obj.bin_folder_name}. Skipping.")
                continue

            major_version = ".".join(game_version_obj.exe_version.split('.')[:2])

            log(f"Attempting to find remote version for local major version: {major_version}")

            sub_version = None
            for route_id in self.download_routes_priority:
                if self._cancel_event.is_set(): return

                route_urls = source.get_urls(task.instance.type, route_id)
                if not route_urls: continue

                if route_id in route_remote:
                    if route_remote[route_id] == major_version:
                        _log_task(task, _('lki.install.status.version_match_found') % '(cached)')
                    continue

                v_url = route_urls.get('version')
                _log_task(task,
                          _('lki.install.status.getting_version_from') % get_route_id_to_name().get(route_id, route_id))

                try:
                    proxies, proxy_auth = root_utils.get_configured_proxies()
                    resp = requests.get(v_url, timeout=5, proxies=proxies, auth=proxy_auth)
                    resp.raise_for_status()
                    lines = resp.text.splitlines()
                    if len(lines) >= 2:
                        remote_major = lines[1].strip()
                        route_remote[route_id] = remote_major
                        if remote_major == major_version:
                            sub_version = lines[0].strip()
                            _log_task(task, _('lki.install.status.version_match_found') % sub_version)
                            break
                        else:
                            _log_task(task, _('lki.install.status.version_mismatch') % (remote_major, major_version))

                except requests.exceptions.RequestException as e:
                    _log_task(task, f"{_('lki.install.status.failed')}: {route_id} ({e})")

            if sub_version:
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

                    if task.use_fonts and task.fo_job_id not in self.download_jobs:
                        fo_job = DownloadJob(task.fo_job_id, 'fonts', 'global')
                        self.download_jobs[task.fo_job_id] = fo_job
                    if task.use_fonts:
                        self.download_jobs[task.fo_job_id].dependent_tasks.add(task)

                    task.status = "downloading"
                    for jid in [mo_job_id, task.ee_job_id, task.fo_job_id]:
                        if jid and jid in self.download_jobs:
                            j = self.download_jobs[jid]
                            if not j._queued:
                                self.download_queue.put(j)
                                j._queued = True
                return

        # Compatible version not found
        self._mark_task_failed(task, _('lki.install.status.no_compatible_version'))

    def _download_worker(self):
        from core.localizer import _

        while not self._cancel_event.is_set():
            try:
                job = self.download_queue.get(timeout=1.0)
            except queue.Empty:
                if getattr(self, '_version_all_done', threading.Event()).is_set():
                    return
                continue

            if not job:
                self.download_queue.task_done()
                continue

            try:
                representative_task = next(iter(job.dependent_tasks))
            except StopIteration:
                self.download_queue.task_done()
                continue

            for task in list(job.dependent_tasks):
                _log_task(task, _('lki.install.status.downloading_file') % job.job_id)

            success, result_path = self._perform_download(job, representative_task)

            if self._cancel_event.is_set():
                self.download_queue.task_done()
                return

            if success:
                job.result_path = result_path

            self.root_tk.after(0, self._on_download_complete, job, success)
            self.download_queue.task_done()

    def _perform_download(self, job: DownloadJob, task: InstallationTask) -> Tuple[bool, Optional[Path]]:
        from core.localizer import _

        source = global_source_manager.get_source(job.lang_code)

        if job.file_type == 'mo':
            return self._download_mo(job, task, source)
        if job.file_type == 'ee':
            return self._download_ee(job, task, source)
        if job.file_type == 'fonts':
            return self._download_fonts(job, task)

        return False, None

    def _download_mo(self, job: DownloadJob, task: InstallationTask, source) -> Tuple[bool, Optional[Path]]:
        from core.localizer import _

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
                    log(_('lki.install.debug.cache_hit') % job.job_id)
                    return True, mo_path
            except Exception as e:
                log(_('lki.install.debug.cache_check_failed') % e)

        utils.mkdir(cache_path)

        for route_id in self.download_routes_priority:
            if self._cancel_event.is_set():
                return False, None

            urls = source.get_urls(task.instance.type, route_id)
            if not urls or not urls.get('mo'):
                continue

            mo_url = urls.get('mo')
            if self._download_file_with_retry(mo_url, mo_path, f"MO ({job.job_id}) - {route_id}", 5):
                dl_hash = utils.get_sha256(mo_path)
                with open(info_path, 'w') as f:
                    json.dump({'file_sha256': dl_hash}, f)
                return True, mo_path

        return False, None

    def _download_ee(self, job: DownloadJob, task: InstallationTask, source) -> Tuple[bool, Optional[Path]]:
        from core.localizer import _

        cache_path = EE_CACHE / job.lang_code / task.instance.type
        ee_zip_path = cache_path / "ee.zip"

        utils.mkdir(cache_path)

        for route_id in self.download_routes_priority:
            if self._cancel_event.is_set():
                return False, None

            urls = source.get_urls(task.instance.type, route_id)
            if not urls or not urls.get('ee'):
                continue

            ee_url = urls.get('ee')
            if self._download_file_with_retry(ee_url, ee_zip_path, f"EE ({job.job_id}) - {route_id}", 5):
                return True, ee_zip_path

        return False, None

    def _download_fonts(self, job: DownloadJob, task: InstallationTask) -> Tuple[bool, Optional[Path]]:
        from core.localizer import _

        font_id = job.job_id  # 例如 "SrcWagon-MainlandCN"
        cache_dir = utils.FONTS_CACHE / font_id
        mkmod_path = cache_dir / f"{font_id}.mkmod"
        info_path = cache_dir / "cache_info.json"
        utils.mkdir(cache_dir)

        proxies, proxy_auth = root_utils.get_configured_proxies()

        for route_id in self.download_routes_priority:
            if self._cancel_event.is_set():
                return False, None

            urls = global_source_manager.get_global_asset_urls("fonts", route_id)
            if not urls or not urls.get('metadata') or not urls.get('download_template'):
                continue

            METADATA_URL = urls['metadata']
            DOWNLOAD_URL = urls['download_template'].replace('{font_id}', font_id)

            remote_version = None
            remote_sha256 = None

            try:
                _log_task(task, _('lki.install.status.fonts_route') % get_route_id_to_name().get(route_id, route_id))
                resp = requests.get(METADATA_URL, timeout=10, proxies=proxies, auth=proxy_auth)
                resp.raise_for_status()
                metadata = resp.json()
                fonts_data = metadata.get('fonts', {})
                font_info = fonts_data.get(font_id)
                if font_info:
                    remote_version = font_info.get('version')
                    remote_sha256 = font_info.get('sha256')
            except Exception as e:
                _log_task(task, _('lki.install.error.fonts_version_check') % f"{route_id}: {e}")
                continue

            if not remote_version:
                _log_task(task, _('lki.install.error.fonts_version_invalid') + f" ({route_id})")
                continue

            # 缓存命中检查
            if info_path.is_file() and mkmod_path.is_file():
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        local_info = json.load(f)
                    if local_info.get('version') == remote_version and local_info.get('font_id') == font_id:
                        actual_hash = utils.get_sha256(mkmod_path)
                        expected_hash = local_info.get('file_sha256')
                        if actual_hash == expected_hash:
                            log(_('lki.install.debug.cache_hit') % job.job_id)
                            return True, mkmod_path
                except Exception as e:
                    log(_('lki.install.debug.cache_check_failed') % e)

            # 下载 7z
            _log_task(task, _('lki.install.status.packing_fonts'))
            temp_7z_path = utils.TEMP_DIR / f"{font_id}.7z"

            def _report_font_progress(downloaded, total):
                pct = min(int(downloaded * 45 / total), 45) if total > 0 else 0
                _log_task(task, _('lki.install.status.downloading_file') % font_id, 50 + pct)

            if not self._download_file_with_retry(DOWNLOAD_URL, temp_7z_path, f"Fonts ({font_id}) - {route_id}", 30,
                                                  on_progress=_report_font_progress):
                continue

            try:
                # 用 py7zr 解压
                unpack_dir = utils.FONTS_UNPACK_TEMP / font_id
                if unpack_dir.exists():
                    shutil.rmtree(unpack_dir)
                utils.mkdir(unpack_dir)

                import py7zr
                with py7zr.SevenZipFile(temp_7z_path, mode='r') as sz:
                    sz.extractall(path=unpack_dir)

                # 收集解压后的文件
                files_to_add: Dict[str, Path] = {}
                for root, _dirnames, files in os.walk(unpack_dir):
                    for file in files:
                        local_path = Path(root) / file
                        arcname = str(local_path.relative_to(unpack_dir)).replace("\\", "/")
                        files_to_add[arcname] = local_path

                if not files_to_add:
                    raise Exception("Empty 7z archive")

                # 打包为 mkmod
                utils.create_mkmod(mkmod_path, files_to_add)

                new_hash = utils.get_sha256(mkmod_path)
                with open(info_path, 'w', encoding='utf-8') as f:
                    json.dump({'font_id': font_id, 'version': remote_version, 'file_sha256': new_hash}, f)

                return True, mkmod_path

            except Exception as e:
                _log_task(task, f"Fonts packing failed for {route_id}, retrying next: {e}")
                continue

        _log_task(task, _('lki.install.error.fonts_no_url'))
        return False, None

    def _download_file_with_retry(self, url: str, dest: Path, log_prefix: str, timeout: int,
                                  on_progress: Optional[Callable[[int, int], None]] = None) -> bool:
        """使用 requests 下载文件。支持可选的进度回调 (已下载字节, 总字节)。"""
        from core.localizer import _  # <-- (修复 UnboundLocalError)
        try:
            # (已修改：修复 %s 格式化)
            _log_overall(self, f"{log_prefix}: {_('lki.install.status.connecting') % url}")
            proxies, proxy_auth = root_utils.get_configured_proxies()

            response = requests.get(url, stream=True, proxies=proxies, auth=proxy_auth, timeout=(timeout, 60))
            response.raise_for_status()

            total = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancel_event.is_set():
                        _log_overall(self, f"{log_prefix}: {_('lki.install.status.cancelled')}")
                        return False
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress and total > 0:
                        on_progress(downloaded, total)

            _log_overall(self, f"{log_prefix}: {_('lki.install.status.success')}")
            return True

        except requests.exceptions.RequestException as e:
            _log_overall(self, f"{log_prefix}: {_('lki.install.status.failed')} ({e})")
            return False

    def _on_download_complete(self, job: Optional[DownloadJob], success: bool):
        """(在主线程中) 在下载完成后更新任务状态。"""
        from core.localizer import _  # <-- (修复 UnboundLocalError)

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

                # 若该任务仍有其他下载未完成，将状态更新为仍在进行的那个下载项，
                # 避免已完成的包名称残留在状态栏中
                if task.status == "downloading" and not task.is_ready_for_install():
                    pending_ids = []
                    if not task.mo_ready and task.mo_job_id:
                        pending_ids.append(task.mo_job_id)
                    if not task.ee_ready and task.use_ee and task.ee_job_id:
                        pending_ids.append(task.ee_job_id)
                    if not task.fo_ready and task.use_fonts and task.fo_job_id:
                        pending_ids.append(task.fo_job_id)
                    if pending_ids:
                        _log_task(task, _('lki.install.status.downloading_file') % pending_ids[0])
        elif job:  # 下载失败
            from core.localizer import _  # (为日志导入)
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

        # (修改 4: 跟踪此回调是否启动了任何安装)
        did_start_install = False
        for task in tasks_to_check:
            if task.is_ready_for_install():
                task.status = "installing"
                _log_task(task, _('lki.install.status.starting_install'), 0)
                threading.Thread(target=self._install_worker, args=(task,), daemon=True).start()
                did_start_install = True

        # (修改 5: 如果这是第一个启动的安装任务，则更新全局状态)
        if did_start_install and not self._install_phase_started:
            with self._lock:
                if not self._install_phase_started:  # (双重检查)
                    self._install_phase_started = True
                    _log_overall(self, _('lki.install.status.install_phase'))

        self._check_if_all_finished()

    def _install_worker(self, task: InstallationTask):
        from core.localizer import _

        non_critical_errors: List[str] = []

        try:
            if self._cancel_event.is_set():
                return

            _log_task(task, _('lki.install.status.preparing_files'), 10)

            mo_job = self.download_jobs[task.mo_job_id]
            mo_file_path = mo_job.result_path

            ee_zip_path = self._validate_optional_path(task, 'ee', task.ee_job_id, non_critical_errors)
            fo_mkmod_path = self._validate_optional_path(task, 'fonts', task.fo_job_id, non_critical_errors)
            mods_mo_mkmod_path, mods_json_mkmod_path = self._process_mods(task, mo_file_path, non_critical_errors)

            if not mo_file_path or not mo_file_path.is_file():
                raise Exception(_('lki.install.error.mo_file_not_found') % mo_file_path)

            locale_config_path = utils.write_locale_config_to_temp(task.lang_code, bool(task.use_fonts))

            core_mkmod_path = self._build_core_mkmod(task, mo_file_path, locale_config_path)
            ee_mkmod_path = self._build_ee_mkmod(task, ee_zip_path, non_critical_errors)

            if self._cancel_event.is_set():
                return

            for version_folder in task.instance.versions:
                if self._cancel_event.is_set():
                    return
                self._cleanup_version(task, version_folder)
                if self._version_matches_mo(version_folder, mo_job):
                    self._install_components_to_version(
                        task, version_folder, mo_job, core_mkmod_path,
                        ee_mkmod_path, fo_mkmod_path,
                        mods_mo_mkmod_path, mods_json_mkmod_path,
                        non_critical_errors
                    )
                else:
                    self._mark_version_inactive(task, version_folder)

            if non_critical_errors:
                error_summary = ", ".join(list(set(non_critical_errors)))
                _log_task(task, _('lki.install.status.warn_done') % error_summary, 100)
                self._mark_task_finished(task, success=True, status_key='lki.install.status.warn_done_short')
            else:
                _log_task(task, _('lki.install.status.done'), 100)
                self._mark_task_finished(task, success=True, status_key='lki.install.status.done')

        except Exception as e:
            import traceback
            log(f"Error in install worker for {task.task_name}: {e}")
            traceback.print_exc()
            self._mark_task_failed(task, str(e))

    def _validate_optional_path(self, task, component_key, job_id, errors):
        from core.localizer import _
        if not job_id:
            return None
        job = self.download_jobs.get(job_id)
        if not job:
            return None
        path = job.result_path
        if not path or not path.is_file():
            key_map = {'ee': 'lki.component.ee', 'fonts': 'lki.component.font'}
            skip_key_map = {'ee': 'lki.install.status.ee_failed_skip', 'fonts': 'lki.install.status.fonts_failed_skip'}
            _log_task(task, _(skip_key_map.get(component_key, '')) % job_id)
            errors.append(_(key_map.get(component_key, '')))
            return None
        return path

    def _process_mods(self, task, mo_file_path, errors):
        from core.localizer import _
        mods_mo_path = None
        mods_json_path = None
        if not task.use_mods:
            return mods_mo_path, mods_json_path
        _log_task(task, _('lki.install.status.packing_mods'), 20)
        try:
            mods_mo_path, mods_json_path = utils.process_mods_for_installation(
                task.instance.instance_id, task.instance.path, mo_file_path, task.lang_code
            )
        except Exception as e:
            _log_task(task, _('lki.install.status.mods_failed_skip') % e)
            errors.append(_('lki.component.mods'))
        return mods_mo_path, mods_json_path

    def _build_core_mkmod(self, task, mo_file_path, locale_config_path):
        from core.localizer import _
        _log_task(task, _('lki.install.status.writing_config'), 25)
        _log_task(task, _('lki.install.status.packing_core'), 40)
        core_mod_files = {"texts/ru/LC_MESSAGES/global.mo": mo_file_path}
        if locale_config_path:
            core_mod_files["locale_config.xml"] = locale_config_path
        core_mkmod_path = utils.TEMP_DIR / f"{task.instance.instance_id}_core.mkmod"
        utils.create_mkmod(core_mkmod_path, core_mod_files)
        return core_mkmod_path

    def _build_ee_mkmod(self, task, ee_zip_path, errors):
        from core.localizer import _
        _log_task(task, _('lki.install.status.packing_ee'), 60)
        if not ee_zip_path:
            return None
        try:
            ee_unpack_dir = utils.EE_UNPACK_TEMP / task.instance.instance_id
            _log_task(task, _('lki.install.status.unpacking_ee'), 61)
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
                return ee_mkmod_path
        except Exception as e:
            _log_task(task, _('lki.install.error.ee_pack_failed') % e)
            errors.append(_('lki.component.ee'))
        return None

    def _version_matches_mo(self, version_folder, mo_job):
        exe_version = version_folder.exe_version or ""
        major_version = ".".join(exe_version.split('.')[:2])
        return major_version == mo_job.version_info['main']

    def _cleanup_version(self, task, version_folder):
        from core.localizer import _
        _log_task(task, _('lki.uninstall.status.removing_files_for') % version_folder.bin_folder_name, 5)
        bin_folder = version_folder.bin_folder_path
        files_to_delete: Set[Path] = get_files_may_overwrite(bin_folder)
        info_file = version_folder.game_root_path / "lki" / "info" / version_folder.bin_folder_name / "installation_info.json"
        if info_file.is_file():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                files_data = data.get("files", {})
                for component_name, path_dict in files_data.items():
                    for relative_path in path_dict.keys():
                        absolute_path = (bin_folder / relative_path).absolute()
                        files_to_delete.add(absolute_path)
            except Exception as e:
                _log_task(task, _('lki.install.warn.cleanup_read_failed') % (info_file.name, e))
        for file_path in files_to_delete:
            try:
                if file_path.is_file():
                    os.remove(file_path)
                    log(f'Deleting {str(file_path)}...')
            except OSError as e:
                _log_task(task, _('lki.install.warn.cleanup_remove_failed') % (file_path.name, e))
        if info_file.is_file():
            try:
                os.remove(info_file)
            except OSError as e:
                _log_task(task, _('lki.install.warn.cleanup_remove_failed') % (info_file.name, e))

    def _install_components_to_version(self, task, version_folder, mo_job, core_mkmod_path,
                                        ee_mkmod_path, fo_mkmod_path,
                                        mods_mo_mkmod_path, mods_json_mkmod_path,
                                        errors):
        from core.localizer import _

        _log_task(task, _('lki.install.status.installing_to') % version_folder.bin_folder_name, 80)

        mods_dir_name = "lk_mods" if task.use_lk_mods else "mods"
        mods_dir = version_folder.bin_folder_path / mods_dir_name
        dest_core_mod_path = mods_dir / "aa_lk_i18n_pack.mkmod"
        dest_ee_mod_path = mods_dir / "aaaa_lk_i18n_ee.mkmod"
        dest_fo_mod_path = mods_dir / "aaa_lk_font_opt.mkmod"
        dest_mo_mod_path = mods_dir / "aaaa_lk_i18n_mo_mod.mkmod"
        dest_json_mod_path = mods_dir / "aaaa_lk_i18n_json_mod.mkmod"

        info_json_path = task.instance.path / "lki" / "info" / version_folder.bin_folder_name
        info_file = info_json_path / "installation_info.json"

        utils.mkdir(mods_dir)

        # 安装前清理：删除 mods/ 和 lk_mods/ 中可能存在的同名文件
        #（防止 Most 模组站清空 mods/ 后又写入同名文件造成冲突）
        mod_filenames = [
            "aa_lk_i18n_pack.mkmod",
            "aaaa_lk_i18n_ee.mkmod",
            "aaa_srcwagon_mk.mkmod",
            "aaa_lk_font_opt.mkmod",
            "aaaa_lk_i18n_mo_mod.mkmod",
            "aaaa_lk_i18n_json_mod.mkmod",
        ]
        bin_path = version_folder.bin_folder_path
        for candidate_dir in [bin_path / "mods", bin_path / "lk_mods"]:
            for fname in mod_filenames:
                candidate_file = candidate_dir / fname
                try:
                    if candidate_file.is_file():
                        os.remove(candidate_file)
                        log(f"Pre-install cleanup: removed {candidate_file}")
                except OSError as e:
                    log(f"Pre-install cleanup warning: could not remove {candidate_file}: {e}")

        try:
            _log_task(task, _('lki.install.status.patching_paths_xml'), 81)
            utils.fix_paths_xml(version_folder.bin_folder_path)
        except Exception as e:
            _log_task(task, _('lki.install.error.paths_xml_failed') % e)
            log(f"Warning: Failed to fix paths.xml for {version_folder.bin_folder_path}: {e}")

        root_utils.copy_with_log(core_mkmod_path, dest_core_mod_path)
        files_info = {'i18n': {}, 'ee': {}, 'font': {}, 'mods': {}}
        try:
            files_info["i18n"][f"{mods_dir_name}/{dest_core_mod_path.name}"] = utils.get_sha256(dest_core_mod_path)
        except Exception as e:
            raise Exception(f"Critical error hashing core mod: {e}") from e

        _copy_and_hash_component(root_utils.copy_with_log, ee_mkmod_path, dest_ee_mod_path, "ee", task, files_info, errors, mods_dir_name)
        _copy_and_hash_component(root_utils.copy_with_log, fo_mkmod_path, dest_fo_mod_path, "font", task, files_info, errors, mods_dir_name)
        _copy_and_hash_component(root_utils.copy_with_log, mods_mo_mkmod_path, dest_mo_mod_path, "mods", task, files_info, errors, mods_dir_name)
        _copy_and_hash_component(root_utils.copy_with_log, mods_json_mkmod_path, dest_json_mod_path, "mods", task, files_info, errors, mods_dir_name)

        utils.mkdir(info_json_path)
        # 读取字体版本信息
        font_version = None
        if task.use_fonts:
            font_cache_info = utils.FONTS_CACHE / task.use_fonts / "cache_info.json"
            try:
                with open(font_cache_info, 'r', encoding='utf-8') as f:
                    font_cache_data = json.load(f)
                font_version = font_cache_data.get('version')
            except Exception:
                pass
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump({
                "version": f"{mo_job.version_info['main']}.{mo_job.version_info['sub']}",
                "l10n_sub_version": mo_job.version_info['sub'],
                "lang_code": task.lang_code,
                "font_id": task.use_fonts,
                "font_version": font_version,
                "files": files_info
            }, f, indent=2)

    def _mark_version_inactive(self, task, version_folder):
        from core.localizer import _
        _log_task(task, _('lki.install.status.inactive_skip') % version_folder.bin_folder_name, 85)
        mods_dir_name = "lk_mods" if task.use_lk_mods else "mods"
        mods_dir = version_folder.bin_folder_path / mods_dir_name
        info_json_path = task.instance.path / "lki" / "info" / version_folder.bin_folder_name
        info_file = info_json_path / "installation_info.json"
        for name in ["aa_lk_i18n_pack.mkmod", "aaaa_lk_i18n_ee.mkmod",
                      "aaa_srcwagon_mk.mkmod", "aaa_lk_font_opt.mkmod",
                      "aaaa_lk_i18n_mo_mod.mkmod", "aaaa_lk_i18n_json_mod.mkmod"]:
            mod_file = mods_dir / name
            try:
                if mod_file.is_file():
                    os.remove(mod_file)
            except OSError:
                pass
        try:
            utils.mkdir(info_json_path)
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump({"version": "INACTIVE", "l10n_sub_version": None, "files": {}}, f, indent=2)
        except OSError as e:
            _log_task(task, _('lki.install.warn.inactive_cleanup_failed') % (version_folder.bin_folder_name, e))

    def _uninstall_worker(self, task: InstallationTask):
        """(在线程中) 为单个实例执行文件删除。"""
        from core.localizer import _
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

                bin_folder = game_version.bin_folder_path
                files_to_delete: Set[Path] = get_files_may_overwrite(bin_folder)
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    files_data = data.get("files", {})
                    for component_name, path_dict in files_data.items():
                        for relative_path in path_dict.keys():
                            # relative_path 是 "mods/lk_i18n_pack.mkmod"
                            absolute_path = bin_folder / relative_path
                            files_to_delete.add(absolute_path)

                except Exception as e:
                    _log_task(task, _('lki.uninstall.error.read_info_failed') % (info_file.name, e))

                # 2. 删除所有引用的文件
                for file_path in files_to_delete:
                    try:
                        if file_path.is_file():
                            os.remove(file_path)
                            log(self, f'Deleting {str(file_path)}...')  # Consider making this localized
                    except OSError as e:
                        # (已修改：本地化)
                        _log_task(task, _('lki.uninstall.warn.remove_failed') % (file_path.name, e))
                        raise Exception(_('lki.uninstall.warn.remove_failed') % (file_path.name, e))

                # 3. (最后) 删除 info.json 文件本身
                try:
                    os.remove(info_file)
                except OSError as e:
                    # (已修改：本地化)
                    _log_task(task, _('lki.uninstall.error.remove_info_failed') % (info_file.name, e))
                    # (已修改：本地化)
                    raise Exception(_('lki.uninstall.error.remove_info_failed_critical') % info_file.name)


            # (所有版本循环完毕)
            _log_task(task, _('lki.uninstall.status.done'), 100)
            self._mark_task_finished(task, success=True, status_key='lki.uninstall.status.done')

        except Exception as e:
            import traceback
            log(f"Error in uninstall worker for {task.task_name}: {e}")
            traceback.print_exc()
            self._mark_task_failed(task, str(e))

    def _mark_task_failed(self, task: InstallationTask, reason: str = ""):
        from core.localizer import _
        with self._lock:
            task.status = "failed"
            status_key = 'lki.uninstall.status.failed' if self.is_uninstalling else 'lki.install.status.failed'
            if reason:
                status_text = f"{_(status_key)}: {reason}"
            else:
                status_text = _(status_key)
            _log_task(task, status_text, 100)

    def _mark_task_finished(self, task: InstallationTask, success: bool, status_key: str = 'lki.install.status.done'):
        from core.localizer import _
        with self._lock:
            task.status = "done"  # (如果 success=True，我们总是设置 "done")
            status_text = _(status_key)  # (获取 "完成" 或 "完成（有警告）")
            self.root_tk.after(0, self.window.mark_task_complete, task.task_name, success, status_text)
        self._check_if_all_finished()

    def _check_if_all_finished(self):
        from core.localizer import _
        with self._lock:
            all_done = all(t.status in ["done", "failed"] for t in self.tasks)
            if all_done:
                all_done_key = 'lki.uninstall.status.all_done' if self.is_uninstalling else 'lki.action.status.all_done'
                _log_overall(self, _(all_done_key))
                self.root_tk.after(0, self.window.all_tasks_finished)
                if self.on_complete_callback:
                    self.root_tk.after(0, self.on_complete_callback)


# --- (组件安装助手) ---

def _copy_and_hash_component(copy_func, src_path, dest_path, component_name, task, files_info, errors,
                             mods_dir_name="mods"):
    if not src_path or not src_path.is_file():
        return
    from core.localizer import _
    from core.logger import log as _log
    try:
        copy_func(src_path, dest_path)
        rel_path = f"{mods_dir_name}/{dest_path.name}"
        files_info[component_name][rel_path] = utils.get_sha256(dest_path)
    except Exception as e:
        _log(_('lki.install.debug.hash_failed') % (f"{task.task_name} ({component_name})", e))
        key = _('lki.component.' + component_name)
        if key not in errors:
            errors.append(key)


# --- (日志记录助手) ---

def _log_overall(manager: InstallationManager, message: str):
    """安全地记录到主 UI。"""
    from core.localizer import _  # (新增局部导入)
    # (已修改：本地化)
    log(f"[{_('lki.log.overall')}] {message}")
    if manager.window:
        manager.root_tk.after(0, manager.window.update_overall_status, message)


def _log_task(task: InstallationTask, message: str, progress: Optional[float] = None):
    """安全地记录到任务的 UI。"""
    log(f"[{task.task_name}] {message}")
    if progress is None:
        if task.progress_callback:
            progress = task.progress_callback()
        else:
            progress = 0.0  # (回退)
    if task.log_callback:
        # (使用 ... 来表示“无变化”)
        task.root_tk.after(0, task.log_callback, message, progress if progress is not None else ...)