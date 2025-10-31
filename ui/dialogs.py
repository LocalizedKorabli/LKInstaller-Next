import tkinter as tk
from tkinter import ttk
from localizer import _


class CustomAskStringDialog(tk.Toplevel):
    """
    一个自定义的、支持 ttkbootstrap 主题的 askstring() 弹窗。
    """

    def __init__(self, parent, title, prompt, initialvalue=""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)  # 保持在父窗口之上
        self.grab_set()  # 模态

        self.result = None  # 用于存储结果

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text=prompt, wraplength=300).pack(fill='x', pady=(0, 10))

        self.entry = ttk.Entry(main_frame)
        self.entry.insert(0, initialvalue)
        self.entry.pack(fill='x', expand=True)
        self.entry.focus_set()  # 立即聚焦

        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill='x', expand=True, side='bottom')

        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self._on_cancel).pack(side='right', padx=5)

        self.entry.bind("<Return>", self._on_save)  # 允许按 Enter 键
        self.bind("<Escape>", self._on_cancel)  # 允许按 Esc 键

        self.update_idletasks()

        # (将窗口居中于父窗口)
        parent.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        self_w = self.winfo_width()
        self_h = self.winfo_height()
        x = parent_x + (parent_w - self_w) // 2
        y = parent_y + (parent_h - self_h) // 2
        self.geometry(f"+{x}+{y}")
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