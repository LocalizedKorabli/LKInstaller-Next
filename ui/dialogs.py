import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Dict
from localizer import _

try:
    from tktooltip import ToolTip
except ImportError:
    print("Warning: tktooltip not found. Tooltips will be disabled.")
    ToolTip = None


class CustomAskStringDialog(tk.Toplevel):
    """
    一个自定义的、支持 ttkbootstrap 主题的 askstring() 弹窗。
    """

    def __init__(self, parent, title, prompt, initialvalue=""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.result = None

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text=prompt, wraplength=300).pack(fill='x', pady=(0, 10))

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

        self.update_idletasks()

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


# --- (新增：全局路由排序窗口) ---
class RoutePriorityWindow(tk.Toplevel):
    """一个用于排序全局下载线路优先级的弹出窗口。"""

    def __init__(self, parent, icons,
                 current_routes_ids: List[str],
                 all_routes_masterlist: List[str],
                 on_save_callback: Callable):

        super().__init__(parent)
        self.title(_('lki.routes.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.icons = icons
        self.on_save_callback = on_save_callback

        # 准备显示名称
        self.route_id_to_name = {
            'gitee': _('l10n.route.gitee'),
            'gitlab': _('l10n.route.gitlab'),
            'github': _('l10n.route.github')
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

        ttk.Label(route_frame, text=_('lki.routes.hint'), style="Hint.TLabel", wraplength=200) \
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