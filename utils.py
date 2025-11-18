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
import locale
import os
import shutil
import sys
import time
import tkinter as tk
from os import PathLike
from pathlib import Path
from typing import Optional, Tuple, Set, Dict, List

import dirs
from logger import log as logger_log
from ui.windows.window_action import ActionProgressWindow

major2exact: Dict[str, str] = {
    'zh': 'zh_CN',
    'en': 'en'
}


def get_system_language_codes() -> Tuple[Optional[str], Optional[str]]:
    try:
        default_locale = locale.getdefaultlocale()
        if default_locale and default_locale[0]:
            exact_lang = default_locale[0].replace('-', '_')
            major_lang = exact_lang.split('_')[0].lower()
            return exact_lang, major_lang

    except Exception as e:
        logger_log(f'Error getting system locale: {e}')
        return None, None

    return None, None


# --- (新增：时区检查) ---
def is_system_gmt8_timezone() -> bool:
    """检查本地系统时区是否为 GMT+8。"""
    try:
        # time.timezone 返回 UTC 以西的偏移秒数。
        # 对于 GMT+8（中国），在非夏令时期间，该值应为 -28800。
        is_dst = time.daylight and time.localtime().tm_isdst
        offset_seconds = -time.altzone if is_dst else -time.timezone

        if offset_seconds == 28800:  # 8 * 60 * 60
            return True
    except Exception as e:
        logger_log(f"Error checking timezone: {e}")
    return False


# --- (新增结束) ---


'''
Returns sets of exact languages and major languages.
'''


def gather_locales() -> Tuple[Set[str], Set[str]]:
    exact = set([])
    major = set([])
    for _locale in os.listdir(dirs.base_path.joinpath('resources/locales')):
        if not _locale.endswith('.json'):
            continue
        _locale = _locale.replace('.json', '')
        exact.add(_locale)
        major.add(_locale.split('_')[0])
    return exact, major


def select_locale_by_system_lang_code():
    exact, major = get_system_language_codes()
    available_exact, available_major = gather_locales()
    if exact and exact in available_exact:
        return exact
    elif major and major in available_major:
        return major2exact.get(major, 'en')
    else:
        return 'en'


def determine_default_l10n_lang(ui_lang: str) -> str:
    """
    根据 UI 语言确定默认的*本地化*语言。
    """
    mapping = {
        'zh_CN': 'zh_CN',
        'zh_TW': 'zh_TW',
        'ja': 'ja'
    }

    # 回退到 'en'
    return mapping.get(ui_lang, 'en')


def scale_dpi(widget: tk.Misc, value: int) -> int:
    """
    使用存储在 Toplevel 上的缩放因子来缩放像素值。
    """
    try:
        # 获取存储在根窗口上的 scaling_factor

        scaling_factor = widget.winfo_toplevel().scaling_factor
        return int(value * scaling_factor)
    except Exception:
        # 如果 scaling_factor 不存在，则回退
        return value


# --- (NEW) Proxy Util (Moved from installation_manager.py) ---
def get_configured_proxies() -> Optional[Dict[str, str]]:
    """
    从全局设置中读取代理配置，并返回 requests 库所需的字典。
    - 'disabled': 返回 {'http': None, 'https': None}
    - 'system':   返回 None (requests 会自动检测)
    - 'manual':   返回 {'http': '...', 'https': '...'}
    """
    import settings  # Local import
    from localizer import _  # Local import

    proxy_mode = settings.global_settings.get('proxy.mode', 'disabled')

    if proxy_mode == 'disabled':
        return {'http': '', 'https': ''}

    if proxy_mode == 'system':
        return None  # requests 库会自动处理

    if proxy_mode == 'manual':
        host = settings.global_settings.get('proxy.host', '')
        port = settings.global_settings.get('proxy.port', '')
        user = settings.global_settings.get('proxy.user', '')
        password = settings.global_settings.get('proxy.password', '')

        if not host or not port:
            logger_log(_('lki.proxy.warn.manual_no_host'))
            return {'http': '', 'https': ''}

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

    return {'http': '', 'https': ''}  # (默认禁用)


def copy_with_log(src: Path, dst: Path, *, follow_symlinks=True):
    shutil.copy(src, dst, follow_symlinks=True)
    logger_log(f'Copying {str(src.absolute())} to {str(dst.absolute())}...')


def _get_prioritized_update_routes() -> List[Dict[str, str]]:
    """
    获取按优先级排序的更新线路列表。
    列表中的每一项都是一个字典 {'version': url, 'download': url}。
    """
    import settings
    from localization_sources import LKI_UPDATE_ROUTES

    priority_keys = settings.global_settings.get('download_routes_priority', [])

    sorted_routes = []
    added_keys = set()

    # 1. 添加设置中指定的优先线路
    for key in priority_keys:
        if key in LKI_UPDATE_ROUTES and key not in added_keys:
            sorted_routes.append(LKI_UPDATE_ROUTES[key])
            added_keys.add(key)

    # 2. 如果设置中遗漏了某些线路，将其补充在最后 (作为安全回退)
    for key, route in LKI_UPDATE_ROUTES.items():
        if key not in added_keys:
            sorted_routes.append(route)

    return sorted_routes


# --- (NEW) Update Logic ---
def update_worker(window: ActionProgressWindow, root_tk: tk.Tk):
    """
    在工作线程中执行更新检查和下载。
    支持多线路故障转移 (Fallback)。
    通过检查 window.is_cancelled() 来支持取消。
    """
    import requests
    import semver
    import constants
    import subprocess
    import threading
    from localizer import _  # 局部导入
    from tkinter import messagebox  # 局部导入
    import settings

    # (新增导入)
    from pathlib import Path

    UPDATE_DIR = dirs.TEMP_DIR / 'updates'
    INSTALLER_PATH = UPDATE_DIR / 'lki_setup.exe'

    # 辅助函数：安全地更新UI
    ui_log = lambda msg, p: root_tk.after(0, window.update_task_progress, _('lki.update.title'), p, msg)

    def _download_and_run(remote_ver_str: str, proxies: Optional[dict], routes_list: List[Dict[str, str]]):
        """
        下载部分，在用户确认后在*新*线程中运行。
        会在 routes_list 中依次尝试下载，直到成功。
        """
        try:
            if window.is_cancelled():
                return

            download_success = False

            # --- 遍历所有线路进行下载 ---
            for route in routes_list:
                if window.is_cancelled():
                    ui_log(_('lki.install.status.cancelled'), 100)
                    return

                download_url = route.get('download')
                if not download_url:
                    continue

                try:
                    ui_log(_('lki.update.status.downloading') + f" ({remote_ver_str})...", 20)
                    logger_log(f"Attempting update download from: {download_url}")

                    # 下载
                    dl_resp = requests.get(download_url, stream=True, proxies=proxies, timeout=30)
                    dl_resp.raise_for_status()

                    total_size = int(dl_resp.headers.get('content-length', 0))
                    downloaded = 0

                    with open(INSTALLER_PATH, 'wb') as f:
                        for chunk in dl_resp.iter_content(chunk_size=8192):
                            if window.is_cancelled():
                                ui_log(_('lki.install.status.cancelled'), 100)
                                return

                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 20 + (downloaded / total_size) * 70  # 进度从 20% 到 90%
                                ui_log(_('lki.update.status.downloading'), progress)

                    # 如果代码走到这里，说明下载成功
                    download_success = True
                    break  # 跳出循环

                except Exception as e:
                    logger_log(f"Download failed from {download_url}: {e}")
                    # 继续尝试下一个线路
                    continue

            # --- 循环结束 ---

            if not download_success:
                # 所有线路都失败
                error_msg = _('lki.update.status.download_failed') % "All routes failed"
                ui_log(error_msg, 100)
                root_tk.after(0, window.mark_task_complete, _('lki.update.title'), False, error_msg)
                return

            if window.is_cancelled():
                return

            ui_log(_('lki.update.status.starting_update'), 95)

            # 启动并退出
            try:
                # 1. 获取当前 .exe 所在的目录 (sys.executable)
                current_install_dir = Path(sys.executable).parent

                # 2. 获取当前语言
                current_lang = settings.global_settings.language

                # 3. 构建参数
                args_list = [
                    str(INSTALLER_PATH),
                    '/SILENT',
                    f'/DIR={str(current_install_dir)}',
                    f'/LANG={current_lang}'
                ]

                logger_log(f"Starting updater with args: {args_list}")

                # 4. 使用新的参数列表启动更新程序
                subprocess.Popen(args_list)

                # 5. 通知主应用在 500 毫秒后退出
                root_tk.after(500, root_tk.destroy)

            except Exception as e:
                ui_log(_('lki.update.error.start_failed') % e, 100)
                root_tk.after(0, window.mark_task_complete, _('lki.update.title'), False,
                              _('lki.update.error.start_failed') % e)

        except Exception as e:
            if window.is_cancelled():
                ui_log(_('lki.install.status.cancelled'), 100)
                return
            import traceback
            traceback.print_exc()
            error_msg = _('lki.update.status.download_failed') % str(e)
            ui_log(error_msg, 100)
            root_tk.after(0, window.mark_task_complete, _('lki.update.title'), False, error_msg)

    def _check_version_and_ask():
        """检查版本的主逻辑（在初始线程中运行）。"""
        try:
            os.makedirs(UPDATE_DIR, exist_ok=True)
            if window.is_cancelled(): return

            ui_log(_('lki.update.status.checking'), 10)
            proxies = get_configured_proxies()

            # 获取排序后的线路列表
            update_routes = _get_prioritized_update_routes()

            remote_version = None

            # --- 遍历线路查询版本 ---
            for route in update_routes:
                if window.is_cancelled(): return

                version_url = route.get('version')
                if not version_url: continue

                try:
                    logger_log(f"Checking version from: {version_url}")
                    resp = requests.get(version_url, timeout=10, proxies=proxies)
                    resp.raise_for_status()

                    data = resp.json()
                    ver_candidate = data.get('version')

                    if ver_candidate and semver.VersionInfo.is_valid(ver_candidate):
                        remote_version = ver_candidate
                        logger_log(f"Found valid version {remote_version} via {version_url}")
                        break  # 成功获取，停止尝试其他线路

                except Exception as e:
                    logger_log(f"Version check failed for {version_url}: {e}")
                    continue
            # --- 循环结束 ---

            if not remote_version:
                # 所有线路都无法获取版本
                ui_log(_('lki.update.error.check_failed') % "All routes failed", 100)
                root_tk.after(0, window.mark_task_complete, _('lki.update.title'), False,
                              _('lki.update.error.check_failed') % "All routes failed")
                return

            if semver.compare(remote_version, constants.APP_VERSION) > 0:
                # 发现新版本。必须在主线程中询问用户。

                def _ask_on_main_thread():
                    """此函数由 root_tk.after() 在主线程上调用。"""
                    if window.is_cancelled(): return

                    try:
                        proceed = messagebox.askyesno(
                            _('lki.update.confirm.title'),
                            _('lki.update.confirm.message') % (remote_version, constants.APP_VERSION),
                            parent=window
                        )
                    except tk.TclError:  # 窗口可能已关闭
                        return

                    if proceed:
                        # 在新线程中开始下载，并传入所有的线路列表以供重试
                        threading.Thread(
                            target=_download_and_run,
                            args=(remote_version, proxies, update_routes),
                            daemon=True
                        ).start()
                    else:
                        # 用户点击了“否”
                        ui_log(_('lki.install.status.cancelled'), 100)
                        root_tk.after(1000, window.destroy)

                root_tk.after(0, _ask_on_main_thread)

            else:
                # 已经是最新版本
                ui_log(_('lki.update.status.latest'), 100)
                root_tk.after(0, window.mark_task_complete, _('lki.update.title'), True,
                              _('lki.update.status.latest'))
                root_tk.after(2000, window.destroy)

        except Exception as e:
            if window.is_cancelled():
                ui_log(_('lki.install.status.cancelled'), 100)
                return

            import traceback
            traceback.print_exc()
            error_msg = _('lki.update.error.check_failed') % str(e)
            ui_log(error_msg, 100)
            root_tk.after(0, window.mark_task_complete, _('lki.update.title'), False, error_msg)

    # 启动检查版本线程
    _check_version_and_ask()