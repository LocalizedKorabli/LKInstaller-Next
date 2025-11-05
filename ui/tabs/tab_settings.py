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

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
import os  # (新增)
import sys  # (新增)
import subprocess  # (新增)
import shutil  # (新增)

import settings
import utils  # (新增)
import logger  # (新增)
from localization_sources import global_source_manager
from localizer import _, get_available_languages
from ui.dialogs import RoutePriorityWindow, BaseDialog
from ui.tabs.tab_base import BaseTab

try:
    from tktooltip import ToolTip
except ImportError:
    print("Warning: tktooltip not found. Tooltips will be disabled.")
    ToolTip = None


class SettingsTab(BaseTab):
    """
    “设置”选项卡 UI。
    """

    def __init__(self, master, icons, on_theme_change_callback, on_language_change_callback, on_reload_callback):
        super().__init__(master, padding='10 10 10 10')

        self.icons = icons
        self.on_theme_change_callback = on_theme_change_callback
        self.on_language_change_callback = on_language_change_callback
        self.on_reload_callback = on_reload_callback

        self.theme_var = tk.StringVar(value=settings.global_settings.get('theme', 'light'))

        self.available_ui_langs = get_available_languages()
        self.ui_lang_name_to_code = {v: k for k, v in self.available_ui_langs.items()}
        current_locale = settings.global_settings.language
        self.current_lang_name = self.available_ui_langs.get(current_locale,
                                                             self.available_ui_langs.get('en', 'English'))

        self.proxy_status_text = self._get_proxy_status_text()

        # (新增：路由名称映射)
        self.route_id_to_name = {
            'gitee': _('lki.i18n.route.gitee'),
            'gitlab': _('lki.i18n.route.gitlab'),
            'github': _('lki.i18n.route.github'),
            'cloudflare': _('lki.i18n.route.cloudflare')
        }

        self._create_settings_tab_widgets()

    def _create_settings_tab_widgets(self):
        """创建“设置”选项卡中的所有小部件"""

        # 配置主选项卡（self）的列
        self.columnconfigure(0, weight=1)

        # --- “外观”设置组 ---
        appearance_frame = ttk.LabelFrame(self, text=_('lki.settings.category.appearance'), padding=10)
        appearance_frame.grid(row=0, column=0, sticky='we', pady=(0, 5))
        appearance_frame.columnconfigure(1, weight=1)

        # 语言设置
        lang_label = ttk.Label(appearance_frame, text=_('lki.settings.language'))
        lang_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        lang_frame = ttk.Frame(appearance_frame)
        lang_frame.grid(row=0, column=1, sticky='we', pady=10)

        self.lang_combobox = ttk.Combobox(lang_frame, values=list(self.get_available_ui_langs()), state='readonly')
        self.lang_combobox.set(self.current_lang_name)
        self.lang_combobox.pack(side='left', fill='x', expand=True)

        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_language_select)

        self.lang_reload_label = ttk.Label(appearance_frame, text="", foreground='gray')
        self.lang_reload_label.grid(row=1, column=1, sticky='w', padx=5, pady=(0, 10))

        # 主题设置
        theme_label = ttk.Label(appearance_frame, text=_('lki.settings.theme'))
        theme_label.grid(row=2, column=0, sticky='e', padx=(0, 10), pady=(10, 0))

        rb_light = ttk.Radiobutton(appearance_frame, text=_('lki.settings.theme.light'), variable=self.theme_var,
                                   value='light', command=self._on_theme_select)
        rb_light.grid(row=2, column=1, sticky='w', pady=(10, 5))  # 调整了pady

        rb_dark = ttk.Radiobutton(appearance_frame, text=_('lki.settings.theme.dark'), variable=self.theme_var,
                                  value='dark', command=self._on_theme_select)
        rb_dark.grid(row=3, column=1, sticky='w', pady=(0, 10))

        # --- “下载”设置组 ---
        download_frame = ttk.LabelFrame(self, text=_('lki.settings.category.download'), padding=10)
        download_frame.grid(row=1, column=0, sticky='we', pady=5)
        download_frame.columnconfigure(1, weight=1)

        # 代理设置
        proxy_label = ttk.Label(download_frame, text=_('lki.settings.proxy'))
        proxy_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        proxy_frame = ttk.Frame(download_frame)
        proxy_frame.grid(row=0, column=1, sticky='we', pady=10)
        proxy_frame.columnconfigure(0, weight=1)

        self.proxy_status_label = ttk.Label(proxy_frame, text=self.proxy_status_text)
        self.proxy_status_label.grid(row=0, column=0, sticky='w', padx=5)

        self.proxy_config_btn = ttk.Button(proxy_frame, text=_('lki.btn.configure'), command=self._open_proxy_window)
        self.proxy_config_btn.grid(row=0, column=1, sticky='e')

        # 下载线路优先级
        route_label = ttk.Label(download_frame, text=_('lki.settings.download_routes_priority'))
        route_label.grid(row=1, column=0, sticky='e', padx=(0, 10), pady=10)

        route_frame = ttk.Frame(download_frame)
        route_frame.grid(row=1, column=1, sticky='we', pady=10)
        route_frame.columnconfigure(0, weight=1)

        self.route_priority_display_label = ttk.Label(route_frame, text="")
        self.route_priority_display_label.grid(row=0, column=0, sticky='w', padx=5)

        self.route_config_btn = ttk.Button(route_frame, text=_('lki.btn.configure'),
                                           command=self._open_route_priority_window)
        self.route_config_btn.grid(row=0, column=1, sticky='e')

        # --- (新增) “文件”设置组 ---
        files_frame = ttk.LabelFrame(self, text=_('lki.settings.category.files'), padding=10)
        files_frame.grid(row=2, column=0, sticky='we', pady=5)
        files_frame.columnconfigure(1, weight=1)

        # 工作路径
        work_path_label = ttk.Label(files_frame, text=_('lki.settings.paths.work_path'))
        work_path_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        work_path_frame = ttk.Frame(files_frame)
        work_path_frame.grid(row=0, column=1, sticky='we', pady=10)
        work_path_frame.columnconfigure(0, weight=1)

        work_path = os.getcwd()
        self.work_path_display = ttk.Label(work_path_frame, text=self._truncate_path(work_path, 30))
        self.work_path_display.grid(row=0, column=0, sticky='w', padx=5)

        work_path_btn = ttk.Button(work_path_frame, text=_('lki.btn.open_dir'),
                                   command=lambda: self._open_directory(utils.base_path))
        work_path_btn.grid(row=0, column=1, sticky='e')

        # 数据路径
        data_path_label = ttk.Label(files_frame, text=_('lki.settings.paths.data_path'))
        data_path_label.grid(row=1, column=0, sticky='e', padx=(0, 10), pady=10)

        data_path_frame = ttk.Frame(files_frame)
        data_path_frame.grid(row=1, column=1, sticky='we', pady=10)
        data_path_frame.columnconfigure(0, weight=1)

        app_data_path = str(utils.APP_DATA_PATH.absolute())
        self.data_path_display = ttk.Label(data_path_frame, text=self._truncate_path(app_data_path, 30))
        self.data_path_display.grid(row=0, column=0, sticky='w', padx=5)

        data_path_btn = ttk.Button(data_path_frame, text=_('lki.btn.open_dir'),
                                   command=lambda: self._open_directory(utils.APP_DATA_PATH))
        data_path_btn.grid(row=0, column=1, sticky='e')

        # 清除按钮
        clear_frame = ttk.Frame(files_frame)
        clear_frame.grid(row=2, column=0, columnspan=2, sticky='e', pady=(10, 5))

        self.clear_logs_btn = ttk.Button(clear_frame, text=_('lki.settings.btn.clear_logs'),
                                         command=self._on_clear_logs)
        self.clear_logs_btn.pack(side='right', padx=(5, 0))

        self.clear_cache_btn = ttk.Button(clear_frame, text=_('lki.settings.btn.clear_cache'),
                                          command=self._on_clear_cache)
        self.clear_cache_btn.pack(side='right')
        # --- (新增结束) ---

        # --- 占位和重载按钮 ---

        # 垂直占位
        self.rowconfigure(3, weight=1)  # (已修改：2 -> 3)

        # 重载按钮
        reload_frame = ttk.Frame(self)
        reload_frame.grid(row=4, column=0, columnspan=2, sticky='se', pady=(20, 0))  # (已修改：3 -> 4)

        self.reload_btn = ttk.Button(reload_frame, text=_('lki.settings.btn.reload'),
                                     command=self._on_reload_click, style="Link.TButton")
        self.reload_btn.pack(side='right')

        # (新增：初始化摘要)
        self._update_route_priority_display()

        if ToolTip:
            ToolTip(self.work_path_display, work_path)
            ToolTip(self.data_path_display, app_data_path)

    def get_available_ui_langs(self) -> List[str]:
        # Consider the user base
        keys = ['zh_CN'] + [key for key in self.available_ui_langs if key != 'zh_CN']
        return [self.available_ui_langs[key] for key in keys]

    def _on_language_select(self, event=None):
        selected_name = self.lang_combobox.get()
        selected_code = self.ui_lang_name_to_code.get(selected_name)

        if selected_code and selected_code != settings.global_settings.language:
            # 1. 立即保存设置
            settings.global_settings.language = selected_code

            # 2. 更新内部状态，以防用户点击“否”时UI回弹
            self.current_lang_name = selected_name

            # 3. 立即询问是否重载
            if messagebox.askyesno(
                    _('lki.reload.title'),
                    _('lki.reload.confirm'),
                    parent=self
            ):
                # 4a. 如果“是”，则清除标签并执行重载
                self.lang_reload_label.config(text="")
                self.on_reload_callback()
            else:
                # 4b. 如果“否”，则显示“需要重载”标签
                self.lang_reload_label.config(text=_('lki.settings.language.reload_required'))
                # (我们不再调用 on_language_change_callback，因为它会触发多余的弹窗)

    # --- (修改结束) ---

    def _on_theme_select(self):
        selected_theme = self.theme_var.get()
        settings.global_settings.set('theme', selected_theme)
        self.on_theme_change_callback(selected_theme)

    def _get_proxy_status_text(self):
        proxy_mode = settings.global_settings.get('proxy.mode', 'disabled')
        key_map = {
            'disabled': 'lki.settings.proxy.disabled',
            'system': 'lki.settings.proxy.system',
            'manual': 'lki.settings.proxy.manual',
        }
        return _(key_map.get(proxy_mode, 'lki.settings.proxy.disabled'))

    def _open_proxy_window(self):
        window = ProxyConfigWindow(self.master.master, self._on_proxy_config_saved)

    def _on_proxy_config_saved(self):
        self.proxy_status_label.config(text=self._get_proxy_status_text())

    def update_icons(self):
        """当主题更改时更新此选项卡上的图标（如果需要）"""
        pass

    # (新增：更新摘要)
    def _update_route_priority_display(self):
        """更新设置页面上显示的下载线路优先级摘要。"""
        route_ids = settings.global_settings.get('download_routes_priority', [])

        display_names = []
        for r_id in route_ids:
            display_names.append(self.route_id_to_name.get(r_id, r_id))

        if len(display_names) > 3:
            display_text = ", ".join(display_names[:3]) + ", ..."
        else:
            display_text = ", ".join(display_names)

        if not display_text:
            display_text = _('lki.routes.not_configured')

        self.route_priority_display_label.config(text=display_text)

    def _open_route_priority_window(self):
        current_list = settings.global_settings.get('download_routes_priority', ['gitee', 'gitlab', 'github'])
        all_routes = global_source_manager.get_all_available_route_ids()

        window = RoutePriorityWindow(
            self.master.master,
            self.icons,
            current_list,
            all_routes,
            self._on_route_priority_save
        )

    # (已修改：保存后更新摘要)
    def _on_route_priority_save(self, new_list: List[str]):
        settings.global_settings.set('download_routes_priority', new_list)
        settings.global_settings.save()
        self._update_route_priority_display()  # <-- (新增)
        messagebox.showinfo(_('lki.routes.title'), _('lki.routes.saved'), parent=self)

    def _on_reload_click(self):
        if messagebox.askyesno(
                _('lki.reload.title'),
                _('lki.reload.confirm'),
                parent=self
        ):
            self.on_reload_callback()

    # --- (新增：文件操作方法) ---

    def _truncate_path(self, path_obj, max_chars: int):
        """将路径缩短到最大字符数，在末尾添加省略号。"""
        path_str = str(path_obj)
        if len(path_str) > max_chars:
            return path_str[:max_chars - 3] + "..."
        return path_str

    def _open_directory(self, path_to_open):
        """在系统的文件资源管理器中打开一个目录。"""
        try:
            path_str = str(path_to_open)
            if sys.platform == "win32":
                os.startfile(path_str)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(['open', path_str])
            else:  # Linux
                subprocess.Popen(['xdg-open', path_str])
        except Exception as e:
            print(f"Error opening directory: {e}")
            messagebox.showerror(_('lki.settings.clear.error'), f"Could not open directory: {e}", parent=self)

    def _on_clear_logs(self):
        """清除日志文件（保留当前日志）。"""
        if not messagebox.askyesno(
                _('lki.settings.clear_logs.confirm.title'),
                _('lki.settings.clear_logs.confirm.message'),
                parent=self
        ):
            return

        try:
            cleared_count = 0
            for f in utils.LOG_DIR.glob('*.log'):
                if f.name != logger.current_log_file_name:
                    os.remove(f)
                    cleared_count += 1
            print(f"Cleared {cleared_count} log files.")
            messagebox.showinfo(_('lki.settings.clear_logs.confirm.title'),
                                _('lki.settings.clear_logs.success'), parent=self)
        except Exception as e:
            print(f"Error clearing logs: {e}")
            messagebox.showerror(_('lki.settings.clear.error'), f"{e}", parent=self)

    def _on_clear_cache(self):
        """清除下载缓存。"""
        if not messagebox.askyesno(
                _('lki.settings.clear_cache.confirm.title'),
                _('lki.settings.clear_cache.confirm.message'),
                parent=self
        ):
            return

        try:
            # 删除 CACHE_DIR 的 *内容*
            for item in utils.CACHE_DIR.iterdir():
                try:
                    if item.is_file():
                        os.remove(item)
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"Could not remove item {item}: {e}")

            print("Cache cleared.")
            messagebox.showinfo(_('lki.settings.clear_cache.confirm.title'),
                                _('lki.settings.clear_cache.success'), parent=self)
        except Exception as e:
            print(f"Error clearing cache: {e}")
            messagebox.showerror(_('lki.settings.clear.error'), f"{e}", parent=self)

    # --- (新增结束) ---


# (ProxyConfigWindow 保持不变)
class ProxyConfigWindow(BaseDialog):
    # (此类代码未更改)
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title(_('lki.proxy.title'))

        self.mode_var = tk.StringVar(value=settings.global_settings.get('proxy.mode', 'disabled'))
        self.host_var = tk.StringVar(value=settings.global_settings.get('proxy.host', ''))
        self.port_var = tk.StringVar(value=settings.global_settings.get('proxy.port', ''))
        self.user_var = tk.StringVar(value=settings.global_settings.get('proxy.user', ''))
        self.pass_var = tk.StringVar(value=settings.global_settings.get('proxy.password', ''))

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        mode_frame = ttk.LabelFrame(main_frame, text=_('lki.proxy.mode'), padding=10)
        mode_frame.pack(fill='x', pady=5)

        modes = [
            (_('lki.settings.proxy.disabled'), 'disabled'),
            (_('lki.settings.proxy.system'), 'system'),
            (_('lki.settings.proxy.manual'), 'manual')
        ]
        for text, value in modes:
            rb = ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=value,
                                 command=self._toggle_manual_fields)
            rb.pack(anchor='w')

        self.manual_frame = ttk.LabelFrame(main_frame, text=_('lki.proxy.manual_settings'), padding=10)
        self.manual_frame.pack(fill='x', pady=5)

        ttk.Label(self.manual_frame, text=_('lki.proxy.host')).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.host_entry = ttk.Entry(self.manual_frame, textvariable=self.host_var)
        self.host_entry.grid(row=0, column=1, sticky='we', padx=5, pady=2)

        ttk.Label(self.manual_frame, text=_('lki.proxy.port')).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.port_entry = ttk.Entry(self.manual_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)

        ttk.Label(self.manual_frame, text=_('lki.proxy.username')).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.user_entry = ttk.Entry(self.manual_frame, textvariable=self.user_var)
        self.user_entry.grid(row=2, column=1, sticky='we', padx=5, pady=2)

        ttk.Label(self.manual_frame, text=_('lki.proxy.password')).grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.pass_entry = ttk.Entry(self.manual_frame, textvariable=self.pass_var, show='*')
        self.pass_entry.grid(row=3, column=1, sticky='we', padx=5, pady=2)

        self.manual_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._save_settings).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        self._toggle_manual_fields()

        self.update_idletasks()
        self.resizable(False, False)

    def _toggle_manual_fields(self):
        """根据单选按钮启用/禁用手动设置字段"""
        state = 'normal' if self.mode_var.get() == 'manual' else 'readonly'
        for widget in self.manual_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.config(state=state)

    def _save_settings(self):
        """保存设置到 settings.global_settings 并关闭窗口"""
        mode = self.mode_var.get()
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()
        user = self.user_var.get().strip()
        password = self.pass_var.get()

        if mode == 'manual':
            if not host or not port:
                messagebox.showerror(
                    _('lki.proxy.title'),
                    _('lki.proxy.error.host_port_required')
                )
                return

        settings.global_settings.set('proxy.mode', mode)

        if mode == 'manual':
            settings.global_settings.set('proxy.host', host)
            settings.global_settings.set('proxy.port', port)
            settings.global_settings.set('proxy.user', user)
            settings.global_settings.set('proxy.password', password)

        self.on_save_callback()
        self.destroy()