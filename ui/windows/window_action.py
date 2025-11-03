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

import os
import subprocess
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import ttk, messagebox
from typing import List, Callable, Dict, Any, Optional

import utils
from localizer import _
from ui.dialogs import BaseDialog
from instance.game_instance import GameInstance
from ui.ui_manager import get_icon_manager


class ActionProgressWindow(BaseDialog):
    """
    显示多个并行安装任务进度的弹出窗口。
    """
    # (已修改：假设 tasks_data 是一个列表，列表项为 {'name': str, 'instance': GameInstance})
    def __init__(self, parent, tasks_data: Dict[str, Any], cancel_callback: Callable,
                 title: str, starting_text: str, pending_text: str):
        super().__init__(parent)
        self.title(title)
        # (已修改：允许轻微调整大小以适应不同DPI)
        self.resizable(True, False)
        # (已修改：设置最小宽度)
        self.minsize(width=utils.scale_dpi(self, 480), height=0)

        self.cancel_callback = cancel_callback
        self.widgets: Dict[str, Dict[str, Any]] = {}
        self._is_cancelled = False
        self.icons = get_icon_manager()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        self.overall_status_label = ttk.Label(
            main_frame, text=starting_text,
            wraplength=utils.scale_dpi(self, 450)
        )
        self.overall_status_label.pack(fill='x', pady=(0, 10))

        # 为每个任务创建 UI 元素
        for name in tasks_data:  # (已修改)
            instance = tasks_data.get(name, None)  # (已修改)

            task_frame = ttk.Frame(main_frame, padding=(0, 5))
            task_frame.pack(fill='x', expand=True)

            play_btn: Optional[ttk.Button] = None
            folder_btn: Optional[ttk.Button] = None

            top_row_frame = ttk.Frame(task_frame)
            top_row_frame.pack(fill='x', expand=True)

            if instance:
            # (新增) 按钮框架，位于右侧
                button_frame = ttk.Frame(task_frame)
                button_frame.pack(side='right', anchor='n', padx=(10, 0))

                # (新增) 运行按钮
                play_btn = ttk.Button(
                    button_frame,
                    image=self.icons.play,  # (修改：从 self.master 获取图标)
                    style="Toolbutton",
                    command=partial(self._on_play_instance, instance),
                    state='disabled'
                )
                play_btn.pack(side='right')

                # (新增) 文件夹按钮
                folder_btn = ttk.Button(
                    button_frame,
                    image=self.icons.folder,  # (修改：从 self.master 获取图标)
                    style="Toolbutton",
                    command=partial(self._open_instance_folder, instance),
                    state='disabled'
                )
                folder_btn.pack(side='right', padx=(2, 0))

            # (新增) 进度框架，位于左侧
            progress_frame = ttk.Frame(task_frame)
            progress_frame.pack(fill='x', expand=True, side='left')

            name_label = ttk.Label(progress_frame, text=name)
            name_label.pack(fill='x')

            status_label = ttk.Label(
                progress_frame,
                text=pending_text,
                style="Hint.TLabel",
                # (已修改) 减小宽度以适应按钮
                wraplength=utils.scale_dpi(self, 350)
            )
            status_label.pack(fill='x')

            progress_bar = ttk.Progressbar(progress_frame, mode='determinate')  # (已修改) 移除固定长度，使其可缩放
            progress_bar.pack(fill='x', pady=2)

            widget: Dict[str, Any] = {
                'frame': task_frame,
                'name_label': name_label,
                'status_label': status_label,
                'progress_bar': progress_bar,
            }

            if instance:
                widget['instance'] = instance
                widget['play_btn'] = play_btn
                widget['folder_btn'] = folder_btn

            self.widgets[name] = widget

        # 关闭按钮
        self.close_btn = ttk.Button(main_frame, text=_('lki.btn.cancel'), command=self._on_close,
                                    style="danger.TButton")
        self.close_btn.pack(side='right', pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._is_cancelled = True
        if self.cancel_callback:
            self.cancel_callback()
        self.destroy()

    def is_cancelled(self) -> bool:
        """检查窗口是否已被用户取消。"""
        return self._is_cancelled

    def update_task_progress(self, task_name: str, progress: float, status: str):
        """从外部更新特定任务的 UI。"""
        if not self.winfo_exists(): return
        if task_name in self.widgets:
            try:
                self.widgets[task_name]['progress_bar']['value'] = progress
                self.widgets[task_name]['status_label'].config(text=status)
            except (tk.TclError, KeyError):
                pass

    def update_overall_status(self, status: str):
        """更新顶部的总体状态标签。"""
        if not self.winfo_exists(): return
        try:
            self.overall_status_label.config(text=status)
        except tk.TclError:
            pass

    def mark_task_complete(self, task_name: str, success: bool, status_text: str):
        """
        (已修改)
        任务完成时调用，更新UI并启用“运行”/“文件夹”按钮。
        """
        if not self.winfo_exists(): return
        if task_name in self.widgets:
            try:
                self.widgets[task_name]['progress_bar'].config(value=100)
                self.widgets[task_name]['status_label'].config(text=status_text)

                # (新增) 任务完成，启用按钮
                # 检查实例是否存在，因为卸载任务可能没有实例
                if self.widgets[task_name]['instance']:
                    self.widgets[task_name]['play_btn'].config(state='normal')
                    self.widgets[task_name]['folder_btn'].config(state='normal')

            except (tk.TclError, KeyError):
                pass  # 窗口或组件已销毁

    def all_tasks_finished(self):
        """所有任务完成后，将“取消”按钮更改为“关闭”。"""
        if not self.winfo_exists(): return
        self.cancel_callback = None

        try:
            self.overall_status_label.config(text=_('lki.action.status.all_done'))
            if self.close_btn and self.close_btn.winfo_exists():
                self.close_btn.config(text=_('lki.btn.close'), style="success.TButton", command=self.destroy,
                                      state='normal')
        except tk.TclError:
            pass  # 窗口已销毁

    # --- (新增方法) ---

    def _open_instance_folder(self, instance: GameInstance):
        """打开所选实例的根文件夹"""
        if not instance:
            print("ActionProgress: No instance provided for folder action.")
            return

        path = instance.path
        if not path:
            print(f"ActionProgress: No path for instance {instance.name}")
            return

        try:
            os.startfile(path)
        except AttributeError:
            try:
                # (已修改) 确保路径是字符串
                subprocess.run(['explorer', os.path.normpath(str(path))])
            except Exception as e:
                print(f"Error opening folder: {e}")
                webbrowser.open(f'file:///{path}')

    def _on_play_instance(self, instance: GameInstance):
        """点击“运行”按钮的回调。"""
        if not instance:
            print("ActionProgress: No instance provided for play action.")
            return

        success, exe_name = instance.launch_game()

        if not success:
            messagebox.showwarning(
                _('lki.app.title'),
                _('lki.game.error.play_failed') % ("lgc_api.exe", "Korabli.exe/WorldOfWarships.exe"),
                parent=self  # (已修改) 将此窗口设为父窗口
            )