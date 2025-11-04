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
from tkinter import ttk, messagebox, filedialog  # (已修改)
from typing import List, Callable
import sys  # (新增)
import os  # (新增)
from pathlib import Path  # (新增)

import utils
from localizer import _

try:
    from tktooltip import ToolTip
except ImportError:
    print("Warning: tktooltip not found. Tooltips will be disabled.")
    ToolTip = None

# (新增)
try:
    import win32com.client
except ImportError:
    print("Warning: pywin32 not installed. Shortcut creation will be disabled.")
    win32com = None


class BaseDialog(tk.Toplevel):
    """
    一个会自动在屏幕上居中的 Toplevel 弹窗基类。
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()  # 防止在左上角闪烁
        if parent and parent.winfo_exists() and parent.state() == 'normal':
            self.transient(parent)  # 保持在父窗口之上
        self.grab_set()  # 设为模态窗口
        # 我们使用 .after() 来确保窗口大小已被计算
        self.after(50, self._center_on_screen)

    def _center_on_screen(self):
        """将窗口移动到屏幕中央。"""
        try:
            self.update_idletasks()  # 确保 winfo_width/height 是准确的

            # 屏幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # 窗口尺寸
            window_width = self.winfo_width()
            window_height = self.winfo_height()

            # 计算位置
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            self.geometry(f"+{x}+{y}")
            self.deiconify()
        except tk.Toplevel:
            pass  # 窗口可能在居中之前被销毁


class CustomAskStringDialog(BaseDialog):  # <-- 继承 BaseDialog
    def __init__(self, parent, title, prompt, initialvalue=""):
        super().__init__(parent)  # <-- 调用 BaseDialog 的 __init__
        self.title(title)

        self.result = None

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text=prompt, wraplength=utils.scale_dpi(self, 300)).pack(fill='x', pady=(0, 10))

        self.entry = ttk.Entry(main_frame)
        self.entry.insert(0, initialvalue)
        self.entry.pack(fill='x', expand=True)
        self.entry.focus_set()

        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill='x', expand=True, side='bottom')

        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self._on_cancel).pack(side='right', padx=5)

        self.entry.bind("<Return>", self._on_save)
        self.bind("<Escape>", self._on_cancel)
        self.resizable(False, False)

    def _on_save(self, event=None):
        self.result = self.entry.get()
        self.destroy()

    def _on_cancel(self, event=None):
        self.result = None
        self.destroy()

    def get_result(self):
        """
        等待窗口关闭并返回结果。
        """
        self.wait_window()
        return self.result


# --- (新增：全局路由排序窗口) ---
class RoutePriorityWindow(BaseDialog):  # <-- 继承 BaseDialog
    def __init__(self, parent, icons,
                 current_routes_ids: List[str],
                 all_routes_masterlist: List[str],
                 on_save_callback: Callable):

        super().__init__(parent)
        self.title(_('lki.routes.title'))
        self.resizable(False, False)

        self.icons = icons
        self.on_save_callback = on_save_callback

        # 准备显示名称
        self.route_id_to_name = {
            'gitee': _('lki.i18n.route.gitee'),
            'gitlab': _('lki.i18n.route.gitlab'),
            'github': _('lki.i18n.route.github'),
            'cloudflare': _('lki.i18n.route.cloudflare')  # <-- (新增)
        }
        self.route_name_to_id = {v: k for k, v in self.route_id_to_name.items()}

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # --- (路由排序 UI) ---
        route_frame = ttk.Frame(main_frame)
        route_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=5)
        route_frame.columnconfigure(0, weight=1)
        route_frame.rowconfigure(0, weight=1)

        self.route_listbox = tk.Listbox(route_frame, exportselection=False, height=5)
        self.route_listbox.grid(row=0, column=0, sticky='nsew', padx=(5, 0), pady=5)

        route_list_scrollbar = ttk.Scrollbar(route_frame, orient='vertical', command=self.route_listbox.yview)
        route_list_scrollbar.grid(row=0, column=1, sticky='ns', pady=5, padx=(0, 5))
        self.route_listbox.config(yscrollcommand=route_list_scrollbar.set)

        self.route_listbox.bind('<<ListboxSelect>>', self._on_route_listbox_select)

        route_btn_frame = ttk.Frame(route_frame)
        route_btn_frame.grid(row=0, column=2, sticky='ns', pady=5, padx=(0, 5))

        self.btn_route_up = ttk.Button(route_btn_frame, image=self.icons.up, style="Toolbutton",
                                       command=self._move_route_up, state='disabled')
        self.btn_route_up.pack(pady=2)

        self.btn_route_down = ttk.Button(route_btn_frame, image=self.icons.down, style="Toolbutton",
                                         command=self._move_route_down, state='disabled')
        self.btn_route_down.pack(pady=2)

        if ToolTip:
            ToolTip(self.btn_route_up, _('lki.tooltip.route_up'))
            ToolTip(self.btn_route_down, _('lki.tooltip.route_down'))

        ttk.Label(route_frame, text=_('lki.routes.hint'), style="Hint.TLabel", wraplength=utils.scale_dpi(self, 220)) \
            .grid(row=1, column=0, columnspan=3, sticky='w', padx=5, pady=(5, 0))

        # --- (按钮) ---
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=1, column=0, columnspan=2, sticky='e')
        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        self._populate_route_listbox(current_routes_ids, all_routes_masterlist)

    def _populate_route_listbox(self, current_routes_ids: List[str], all_routes_masterlist: List[str]):
        """填充路由列表框，确保所有路由都在其中"""
        self.route_listbox.delete(0, 'end')

        final_route_ids = []

        # 1. 按已保存的顺序添加
        for r_id in current_routes_ids:
            if r_id in all_routes_masterlist and r_id not in final_route_ids:
                final_route_ids.append(r_id)

        # 2. 添加任何在 masterlist 中但不在已保存列表中的新路由
        for r_id in all_routes_masterlist:
            if r_id not in final_route_ids:
                final_route_ids.append(r_id)

        # 填充 listbox
        for r_id in final_route_ids:
            name = self.route_id_to_name.get(r_id, r_id)
            self.route_listbox.insert('end', name)

    def _on_route_listbox_select(self, event=None):
        """更新上/下按钮的状态"""
        try:
            idx = self.route_listbox.curselection()[0]
            size = self.route_listbox.size()

            self.btn_route_up.config(state='normal' if idx > 0 else 'disabled')
            self.btn_route_down.config(state='normal' if idx < (size - 1) else 'disabled')

        except IndexError:
            self.btn_route_up.config(state='disabled')
            self.btn_route_down.config(state='disabled')

    def _move_route_up(self):
        try:
            idx = self.route_listbox.curselection()[0]
            if idx == 0:
                return

            text = self.route_listbox.get(idx)
            self.route_listbox.delete(idx)
            self.route_listbox.insert(idx - 1, text)
            self.route_listbox.selection_set(idx - 1)
            self.route_listbox.activate(idx - 1)
            self._on_route_listbox_select()
        except IndexError:
            pass

    def _move_route_down(self):
        try:
            idx = self.route_listbox.curselection()[0]
            if idx == (self.route_listbox.size() - 1):
                return

            text = self.route_listbox.get(idx)
            self.route_listbox.delete(idx)
            self.route_listbox.insert(idx + 1, text)
            self.route_listbox.selection_set(idx + 1)
            self.route_listbox.activate(idx + 1)
            self._on_route_listbox_select()
        except IndexError:
            pass

    def _on_save(self):
        new_routes_names = list(self.route_listbox.get(0, 'end'))
        new_route_ids = [self.route_name_to_id.get(name, 'gitee') for name in new_routes_names]

        self.on_save_callback(new_route_ids)
        self.destroy()
# --- (新增结束) ---


# --- (新增：自动更新快捷方式配置窗口) ---
class AutoUpdateConfigDialog(BaseDialog):
    def __init__(self, parent, instance_id: str, instance_name: str, preset_id: str, preset_name: str):
        super().__init__(parent)
        self.title(_('lki.autoupdate.title'))
        self.resizable(False, False)

        self.instance_id = instance_id
        self.instance_name = instance_name
        self.preset_id = preset_id

        # --- 获取默认保存路径 ---
        shell = win32com.client.Dispatch('WScript.Shell')
        desktop_path_str = shell.SpecialFolders('Desktop')
        desktop = Path(desktop_path_str)
        default_name = f"{_('lki.autoupdate.shortcut_default_title') % f'{self.instance_name}-{preset_name}'}.lnk"
        self.shortcut_path_var = tk.StringVar(value=str(desktop / default_name))
        self.start_game_var = tk.BooleanVar(value=True)

        # --- UI 设置 ---
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # 1. 路径选择
        ttk.Label(main_frame, text=_('lki.autoupdate.save_location')).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)

        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=0, column=1, sticky='we', pady=5)
        path_frame.columnconfigure(0, weight=1)

        path_entry = ttk.Entry(path_frame, textvariable=self.shortcut_path_var, width=50)
        path_entry.grid(row=0, column=0, sticky='we')

        browse_btn = ttk.Button(path_frame, text=_('lki.autoupdate.btn.browse'), command=self._on_browse)
        browse_btn.grid(row=0, column=1, sticky='w', padx=(5, 0))

        # 2. 复选框
        cb_run_client = ttk.Checkbutton(main_frame, text=_('lki.autoupdate.run_client'),
                                        variable=self.start_game_var)
        cb_run_client.grid(row=1, column=0, columnspan=2, sticky='w', pady=(10, 0))

        # 3. 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=2, column=0, columnspan=2, sticky='e', pady=(10, 0))

        self.ok_btn = ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_ok)
        self.ok_btn.pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        if not win32com:
            self.ok_btn.config(state='disabled')
            path_entry.config(state='disabled')
            browse_btn.config(state='disabled')
            cb_run_client.config(state='disabled')
            ttk.Label(main_frame, text="Error: pywin32 is required to create shortcuts.", foreground='red').grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

    def _on_browse(self):
        """显示保存文件对话框"""
        initial_dir = str(Path(self.shortcut_path_var.get()).parent)
        initial_file = Path(self.shortcut_path_var.get()).name

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title=_('lki.autoupdate.file_dialog_title'),
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".lnk",
            filetypes=[(_('lki.autoupdate.file_type_name'), "*.lnk"), ("All files", "*.*")]
        )

        if save_path:
            self.shortcut_path_var.set(os.path.normpath(save_path))

    def _on_ok(self):
        """创建快捷方式"""
        save_path = self.shortcut_path_var.get()
        if not save_path:
            messagebox.showwarning(_('lki.autoupdate.title'), _('lki.autoupdate.error.no_path'), parent=self)
            return

        if not win32com:
            messagebox.showerror(_('lki.autoupdate.title'), "pywin32 library is missing.", parent=self)
            return

        try:
            # 1. 获取正在运行的可执行文件路径 (lki.exe)
            target_exe = sys.executable
            # 2. 获取它所在的目录 (用于 WorkingDirectory)
            target_dir = str(Path(target_exe).parent)
            # 3. 获取图标路径
            icon_path = str(utils.base_path / 'resources' / 'logo' / 'logo.ico')

            # 4. 构建参数
            preset_arg = f'--auto-execute-preset "{self.instance_id}:{self.preset_id}"'
            run_arg = "--runclient" if self.start_game_var.get() else ""
            full_args = f"{preset_arg} {run_arg}".strip()

            # 5. 创建快捷方式
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(save_path)
            shortcut.TargetPath = target_exe
            shortcut.Arguments = full_args
            shortcut.WorkingDirectory = target_dir
            # IconLocation 格式为 "path,index"
            shortcut.IconLocation = f"{icon_path}, 0"
            shortcut.Description = f"Launch {self.instance_name} with LKI auto-update"
            shortcut.Save()

            messagebox.showinfo(
                _('lki.autoupdate.success.title'),
                _('lki.autoupdate.success.message') % save_path,
                parent=self
            )
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                _('lki.autoupdate.title'),
                _('lki.autoupdate.error.create_failed') % e,
                parent=self
            )