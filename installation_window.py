import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict, Any
from localizer import _


class InstallProgressWindow(tk.Toplevel):
    """
    显示多个并行安装任务进度的弹出窗口。
    """

    def __init__(self, parent, task_names: List[str], cancel_callback: Callable):
        super().__init__(parent)

        self.title(_('lki.install.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.cancel_callback = cancel_callback
        self.widgets: Dict[str, Dict[str, Any]] = {}

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        self.overall_status_label = ttk.Label(main_frame, text=_('lki.install.status.starting'), wraplength=450)
        self.overall_status_label.pack(fill='x', pady=(0, 10))

        # 为每个任务创建 UI 元素
        for name in task_names:
            task_frame = ttk.Frame(main_frame, padding=(0, 5))
            task_frame.pack(fill='x', expand=True)

            name_label = ttk.Label(task_frame, text=name)
            name_label.pack(fill='x')

            status_label = ttk.Label(task_frame, text=_('lki.install.status.pending'), style="Hint.TLabel")
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
        close_btn = ttk.Button(main_frame, text=_('lki.btn.cancel'), command=self._on_close, style="danger.TButton")
        close_btn.pack(side='right', pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """当用户点击“取消”或关闭窗口时调用。"""
        if self.cancel_callback:
            self.cancel_callback()
        self.destroy()

    def update_task_progress(self, task_name: str, progress: float, status: str):
        """从外部更新特定任务的 UI。"""
        if task_name in self.widgets:
            self.widgets[task_name]['progress_bar']['value'] = progress
            self.widgets[task_name]['status_label'].config(text=status)

    def update_overall_status(self, status: str):
        """更新顶部的总体状态标签。"""
        self.overall_status_label.config(text=status)

    def mark_task_complete(self, task_name: str, success: bool):
        """将任务标记为完成（绿色）或失败（红色）。"""
        if task_name in self.widgets:
            style = "success.TProgressbar" if success else "danger.TProgressbar"
            self.widgets[task_name]['progress_bar'].config(style=style, value=100)
            status = _('lki.install.status.done') if success else _('lki.install.status.failed')
            self.widgets[task_name]['status_label'].config(text=status)

    def all_tasks_finished(self):
        """所有任务完成后，将“取消”按钮更改为“关闭”。"""
        self.cancel_callback = None  # 禁用取消功能
        self.overall_status_label.config(text=_('lki.install.status.all_done'))
        close_btn = ttk.Button(self, text=_('lki.btn.close'), command=self.destroy, style="success.TButton")
        # (这会替换旧按钮，但我们需要找到它... 简单起见，我们只更改文本)
        for child in self.winfo_children():  # -> main_frame
            for btn in child.winfo_children():
                if isinstance(btn, ttk.Button):
                    btn.config(text=_('lki.btn.close'), style="success.TButton", command=self.destroy)