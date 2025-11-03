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

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict, Any

import utils
from localizer import _
from ui.dialogs import BaseDialog


class ActionProgressWindow(BaseDialog):
    """
    显示多个并行安装任务进度的弹出窗口。
    """

    def __init__(self, parent, task_names: List[str], cancel_callback: Callable,
                 title: str, starting_text: str, pending_text: str):
        super().__init__(parent)
        self.title(title)  # (已修改)
        self.resizable(False, False)

        self.cancel_callback = cancel_callback
        self.widgets: Dict[str, Dict[str, Any]] = {}
        self._is_cancelled = False

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        self.overall_status_label = ttk.Label(
            main_frame, text=starting_text,
            wraplength=utils.scale_dpi(self, 450)
        )  # (已修改)
        self.overall_status_label.pack(fill='x', pady=(0, 10))

        # 为每个任务创建 UI 元素
        for name in task_names:
            task_frame = ttk.Frame(main_frame, padding=(0, 5))
            task_frame.pack(fill='x', expand=True)

            name_label = ttk.Label(task_frame, text=name)
            name_label.pack(fill='x')

            status_label = ttk.Label(
                task_frame,
                text=pending_text,
                style="Hint.TLabel",
                wraplength=utils.scale_dpi(self, 450)
            )  # (已修改)
            status_label.pack(fill='x')

            progress_bar = ttk.Progressbar(task_frame, length=450, mode='determinate')
            progress_bar.pack(fill='x', pady=2)

            self.widgets[name] = {
                'frame': task_frame,
                'name_label': name_label,
                'status_label': status_label,
                'progress_bar': progress_bar
            }

        # 关闭按钮
        self.close_btn = ttk.Button(main_frame, text=_('lki.btn.cancel'), command=self._on_close, style="danger.TButton")
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
        if not self.winfo_exists(): return  # <-- 修复2：添加检查
        if task_name in self.widgets:
            try:  # (新增 try/except 进一步加固)
                self.widgets[task_name]['progress_bar']['value'] = progress
                self.widgets[task_name]['status_label'].config(text=status)
            except (tk.TclError, KeyError):
                pass  # 窗口或组件已销毁

    def update_overall_status(self, status: str):
        """更新顶部的总体状态标签。"""
        if not self.winfo_exists(): return  # <-- 修复2：添加检查
        try: # (新增 try/except 进一步加固)
            self.overall_status_label.config(text=status)
        except tk.TclError:
            pass # 窗口已销毁

    def mark_task_complete(self, task_name: str, success: bool, status_text: str):
        if not self.winfo_exists(): return  # <-- 修复2：添加检查
        if task_name in self.widgets:
            try:  # (新增 try/except 进一步加固)
                self.widgets[task_name]['progress_bar'].config(value=100)
                # (状态文本现在由管理器直接提供)
                self.widgets[task_name]['status_label'].config(text=status_text)
            except (tk.TclError, KeyError):
                pass  # 窗口或组件已销毁

    def all_tasks_finished(self):
        """所有任务完成后，将“取消”按钮更改为“关闭”。"""
        if not self.winfo_exists(): return  # <-- 修复2：添加检查
        self.cancel_callback = None
        self.overall_status_label.config(text=_('lki.action.status.all_done'))
        if self.close_btn and self.close_btn.winfo_exists():
            self.close_btn.config(text=_('lki.btn.close'), style="success.TButton", command=self.destroy,
                                  state='normal')
