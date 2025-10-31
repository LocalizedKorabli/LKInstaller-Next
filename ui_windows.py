import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import webbrowser
from pathlib import Path
import xml.etree.ElementTree as Et
from typing import Optional

# (已移除 simpledialog)

import settings
from localizer import _
import instance_manager
from localization_sources import global_source_manager
from utils import determine_default_l10n_lang

from tktooltip import ToolTip

# --- (CustomAskStringDialog 保持不变) ---
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


# --- (AddInstanceWindow - 已修改) ---
class AddInstanceWindow(tk.Toplevel):
    """一个用于添加新游戏实例的弹出窗口。"""

    def __init__(self, parent, type_map, on_save_callback):
        super().__init__(parent)
        self.title(_('lki.add_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.type_map = type_map
        self.type_name_to_id = {v: k for k, v in self.type_map.items()}
        self.on_save_callback = on_save_callback

        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.type_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # 1. 名称
        ttk.Label(main_frame, text=_('lki.add_instance.name')).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky='we', pady=5)
        name_entry.focus_set()

        # 2. 路径
        ttk.Label(main_frame, text=_('lki.add_instance.path')).grid(row=1, column=0, sticky='e', padx=(0, 10), pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=1, sticky='we', pady=5)
        path_frame.columnconfigure(0, weight=1)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=0, sticky='we')
        browse_btn = ttk.Button(path_frame, text=_('lki.add_instance.btn.browse'), command=self._on_browse)
        browse_btn.grid(row=0, column=1, sticky='w', padx=(5, 0))

        # 3. 类型
        ttk.Label(main_frame, text=_('lki.add_instance.type')).grid(row=2, column=0, sticky='e', padx=(0, 10), pady=5)
        # (已修改：初始状态为 disabled)
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=list(self.type_map.values()),
                                       state='disabled')
        self.type_combo.grid(row=2, column=1, sticky='we', pady=5)

        # 4. 状态标签 (新增)
        self.status_label = ttk.Label(main_frame, text="", wraplength=300)
        self.status_label.grid(row=3, column=1, sticky='we', pady=(0, 5), padx=5)

        # 5. 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=4, column=0, columnspan=2, sticky='e')
        self.save_btn = ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save, state='disabled')
        self.save_btn.pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        # 6. 绑定 (新增)
        self.name_var.trace_add('write', self._check_button_state)
        self.path_var.trace_add('write', self._on_path_changed)

    def _on_browse(self):
        directory = filedialog.askdirectory(parent=self)
        if directory:
            self.path_var.set(os.path.normpath(directory))

    def _validate_base_path(self, p: Path) -> bool:
        """仅验证基本结构（目录、exe、bin）"""
        try:
            if not p.is_dir():
                return False
            # (基于 installer_gui.py, Korabli.exe 不是必须的)
            if not (p / 'Korabli.exe').is_file() and not (p / 'WorldOfWarships.exe').is_file():
                return False

            if not (p / 'bin').is_dir():
                return False

            return True
        except Exception:
            return False

    def _detect_instance_type(self, p: Path) -> Optional[str]:
        """根据路径检测实例类型"""
        # 逻辑 1: 检查 steam_api64.dll
        if (p / 'steam_api64.dll').is_file():
            return 'production'  # Steam 客户端始终是正式服

        # 逻辑 2: 检查 game_info.xml
        xml_path = p / 'game_info.xml'
        if xml_path.is_file():
            try:
                tree = Et.parse(xml_path)
                game_id_elem = tree.find('.//game/id')
                if game_id_elem is not None:
                    game_id = game_id_elem.text
                    if game_id == 'MK.RU.PRODUCTION':
                        return 'production'
                    if game_id == 'MK.RPT.PRODUCTION':
                        return 'pts'
            except Exception as e:
                print(f"Error parsing game_info.xml: {e}")
                return None  # XML 解析失败，视为无法判断

        return None  # 既不是 Steam 也找不到有效的 XML

    # (已修改：确保 Combobox 始终为 disabled)
    def _on_path_changed(self, *args):
        """当路径文本框变化时调用"""
        path_str = self.path_var.get().strip()

        if not path_str:
            self.status_label.config(text="")
            self.type_var.set("")
            self.type_combo.config(state='disabled')  # <-- 保持 disabled
            self._check_button_state()
            return

        self.status_label.config(text=_('lki.add_instance.status.checking'), foreground='gray')
        self.master.update_idletasks()  # 强制刷新UI以显示“正在检测”

        p = Path(path_str)

        # 1. 验证基本结构
        if not self._validate_base_path(p):
            self.type_var.set("")
            self.status_label.config(text=_('lki.add_instance.error.invalid_path'), foreground='red')
            self.type_combo.config(state='disabled')  # <-- 保持 disabled
            self._check_button_state()
            return

        # 2. 检测类型
        detected_type_code = self._detect_instance_type(p)

        if detected_type_code:
            type_name = self.type_map.get(detected_type_code)
            self.type_var.set(type_name)
            self.status_label.config(text=_('lki.add_instance.status.detected') % type_name, foreground='green')
            self.type_combo.config(state='disabled')  # <-- 自动检测成功，保持 disabled
        else:
            self.type_var.set("")
            # (使用您在 zh_CN.json 中提供的详细错误)
            self.status_label.config(text=_('lki.add_instance.error.invalid_path'), foreground='red')
            self.type_combo.config(state='disabled')  # <-- 无法检测，保持 disabled

        self._check_button_state()

    def _check_button_state(self, *args):
        """检查名称和类型是否都有效，以启用保存按钮"""
        name_ok = self.name_var.get().strip()
        type_ok = self.type_var.get()  # 如果检测失败，这里会是 ""

        if name_ok and type_ok:
            self.save_btn.config(state='normal')
        else:
            self.save_btn.config(state='disabled')

    def _on_save(self):
        # 按钮状态已确保所有字段有效
        name = self.name_var.get().strip()
        path_str = self.path_var.get().strip()
        type_name = self.type_var.get()

        type_code = self.type_name_to_id.get(type_name)

        self.on_save_callback(name, path_str, type_code)
        self.destroy()


# --- (EditInstanceWindow 保持不变) ---
class EditInstanceWindow(tk.Toplevel):
    """一个用于编辑实例名称和活动预设的弹出窗口。"""

    def __init__(self, parent, instance_id, current_name, current_preset_id, preset_map, on_save_callback):
        super().__init__(parent)
        self.title(_('lki.edit_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.instance_id = instance_id
        self.preset_id_to_name = preset_map
        self.preset_name_to_id = {v: k for k, v in self.preset_id_to_name.items()}
        self.on_save_callback = on_save_callback

        self.name_var = tk.StringVar(value=current_name)
        self.preset_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # 1. 名称
        ttk.Label(main_frame, text=_('lki.edit_instance.name')).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky='we', pady=5)
        name_entry.focus_set()

        # 2. 活动预设
        ttk.Label(main_frame, text=_('lki.edit_instance.active_preset')).grid(row=1, column=0, sticky='e', padx=(0, 10),
                                                                              pady=5)
        preset_combo = ttk.Combobox(main_frame, textvariable=self.preset_var,
                                    values=list(self.preset_id_to_name.values()), state='readonly')
        preset_combo.grid(row=1, column=1, sticky='we', pady=5)

        current_preset_name = self.preset_id_to_name.get(current_preset_id, "")
        if current_preset_name:
            preset_combo.set(current_preset_name)

        # 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=2, column=0, columnspan=2, sticky='e')
        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

    def _on_save(self):
        new_name = self.name_var.get().strip()
        new_preset_name = self.preset_var.get()

        if not new_name or not new_preset_name:
            return

        new_preset_id = self.preset_name_to_id.get(new_preset_name)
        if not new_preset_id:
            return

        self.on_save_callback(self.instance_id, new_name, new_preset_id)
        self.destroy()


# --- (DeleteInstanceWindow 保持不变) ---
class DeleteInstanceWindow(tk.Toplevel):
    """一个要求输入名称以确认删除的弹出窗口。"""

    def __init__(self, parent, instance_id, instance_name, icons, on_delete_callback):
        super().__init__(parent)
        self.title(_('lki.delete_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.instance_id = instance_id
        self.instance_name = instance_name
        self.icons = icons
        self.on_delete_callback = on_delete_callback

        self.confirm_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)

        prompt_label = ttk.Label(main_frame, text=_('lki.delete_instance.prompt'), wraplength=350)
        prompt_label.grid(row=0, column=0, sticky='w', pady=(0, 10))

        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=1, column=0, sticky='we', pady=5)

        name_label = ttk.Label(name_frame, text=self.instance_name, style="Client.TLabel")
        name_label.pack(side='left', anchor='w')

        copy_btn = ttk.Button(name_frame, image=self.icons.copy, style="Toolbutton", command=self._copy_name)
        copy_btn.pack(side='left', padx=(5, 0))

        confirm_label = ttk.Label(main_frame, text=_('lki.delete_instance.confirm_label'))
        confirm_label.grid(row=2, column=0, sticky='w', pady=(10, 5))

        self.confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var)
        self.confirm_entry.grid(row=3, column=0, sticky='we')
        self.confirm_entry.focus_set()

        # 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=4, column=0, sticky='e', pady=(10, 0))

        self.delete_btn = ttk.Button(button_frame, text=_('lki.btn.remove_instance'), command=self._on_delete,
                                     style="danger.TButton")
        self.delete_btn.pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        self.delete_btn.config(state='disabled')
        self.confirm_var.trace_add('write', self._validate_name)
        self.confirm_entry.bind("<Return>", self._on_delete)

    def _validate_name(self, *args):
        entered_name = self.confirm_var.get()
        if entered_name == self.instance_name:
            self.delete_btn.config(state='normal')
        else:
            self.delete_btn.config(state='disabled')

    def _copy_name(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.instance_name)
        except Exception as e:
            print(f"Clipboard error: {e}")

    def _on_delete(self, event=None):
        if self.delete_btn.cget('state') == 'disabled':
            return

        entered_name = self.confirm_var.get()
        if entered_name == self.instance_name:
            self.on_delete_callback(self.instance_id, self.instance_name)
            self.destroy()
        else:
            messagebox.showerror(_('lki.delete_instance.title'), _('lki.delete_instance.error.mismatch'), parent=self)


# --- (ProxyConfigWindow 和 PresetManagerWindow 保持不变) ---
class ProxyConfigWindow(tk.Toplevel):
    # (此类的代码保持不变)
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback

        self.title(_('lki.proxy.title'))
        self.transient(parent)
        self.grab_set()

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


class PresetManagerWindow(tk.Toplevel):
    """一个用于管理（CRUD）预设的弹出窗口。"""

    # (此类的代码保持不变)
    def __init__(self, parent_tk, app_instance, instance_id, on_close_callback):
        super().__init__(parent_tk)
        self.parent_app = app_instance
        self.instance_id = instance_id
        self.on_close_callback = on_close_callback

        self.icons = self.parent_app.icons

        self.title(_('lki.preset.manager.title'))
        self.transient(parent_tk)
        self.grab_set()

        self.instance_manager = instance_manager.global_instance_manager
        self.instance_data = self.instance_manager.get_instance(self.instance_id)
        self.active_preset_id = self.instance_data.get('active_preset_id', 'default')

        self.l10n_id_to_name, self.l10n_name_to_id = global_source_manager.get_display_maps()

        self.route_id_to_name = {
            'gitee': _('l10n.route.gitee'),
            'gitlab': _('l10n.route.gitlab'),
            'github': _('l10n.route.github')
        }
        self.route_name_to_id = {v: k for k, v in self.route_id_to_name.items()}

        self.use_ee_var = tk.BooleanVar()
        self.use_mods_var = tk.BooleanVar()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        self.preset_listbox = tk.Listbox(list_frame, exportselection=False)
        self.preset_listbox.pack(side='left', fill='y', expand=True)

        list_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.preset_listbox.yview)
        list_scrollbar.pack(side='right', fill='y')
        self.preset_listbox.config(yscrollcommand=list_scrollbar.set)

        self.preset_listbox.bind('<<ListboxSelect>>', self._on_listbox_select)

        self.details_frame = ttk.Frame(main_frame, padding=10)
        self.details_frame.grid(row=0, column=1, sticky='nsew')
        self.details_frame.columnconfigure(1, weight=1)

        ttk.Label(self.details_frame, text=_('lki.preset.manager.language')).grid(row=0, column=0, sticky='e',
                                                                                  padx=(0, 10), pady=5)
        self.lang_combobox = ttk.Combobox(self.details_frame, values=list(self.l10n_id_to_name.values()),
                                          state='readonly')
        self.lang_combobox.grid(row=0, column=1, sticky='we', pady=5)
        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_lang_select_changed)

        ttk.Label(self.details_frame, text=_('lki.preset.manager.route')).grid(row=1, column=0, sticky='e',
                                                                               padx=(0, 10), pady=5)
        self.route_combobox = ttk.Combobox(self.details_frame, state='readonly')
        self.route_combobox.grid(row=1, column=1, sticky='we', pady=5)

        self.cb_use_ee = ttk.Checkbutton(self.details_frame, text=_('lki.preset.manager.use_ee'),
                                         variable=self.use_ee_var)
        self.cb_use_ee.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 0))

        mods_frame = ttk.Frame(self.details_frame)
        mods_frame.grid(row=3, column=0, columnspan=2, sticky='we', pady=5)

        self.cb_use_mods = ttk.Checkbutton(mods_frame, text=_('lki.preset.manager.use_mods'),
                                           variable=self.use_mods_var)
        self.cb_use_mods.pack(side='left')

        self.btn_open_mods_dir = ttk.Button(mods_frame, image=self.icons.folder, style="Toolbutton",
                                            command=self._open_mods_folder)
        self.btn_open_mods_dir.pack(side='left', padx=(5, 0))

        self.btn_download_mods = ttk.Button(mods_frame, image=self.icons.download, style="Toolbutton",
                                            command=self._open_mods_download)
        self.btn_download_mods.pack(side='left', padx=5)

        try:
            ToolTip(self.btn_open_mods_dir, _('lki.preset.manager.tooltip_open_mods_dir'))
            ToolTip(self.btn_download_mods, _('lki.preset.manager.tooltip_download_mods'))
        except ImportError:
            print("tktooltip not found. Skipping tooltips.")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        self.btn_new = ttk.Button(button_frame, text=_('lki.btn.new'), command=self._new_preset)
        self.btn_new.pack(side='left')

        self.btn_save_as = ttk.Button(button_frame, text=_('lki.btn.save_as'), command=self._save_as_preset)
        self.btn_save_as.pack(side='left', padx=5)

        self.btn_rename = ttk.Button(button_frame, text=_('lki.btn.rename'), command=self._rename_preset)
        self.btn_rename.pack(side='left')

        self.btn_delete = ttk.Button(button_frame, text=_('lki.btn.delete'), command=self._delete_preset)
        self.btn_delete.pack(side='left', padx=5)

        self.btn_save = ttk.Button(button_frame, text=_('lki.btn.save_changes'), command=self._save_preset)
        self.btn_save.pack(side='right')

        select_frame = ttk.Frame(main_frame)
        select_frame.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        self.btn_select = ttk.Button(select_frame, text=_('lki.preset.btn.select'), command=self._select_and_close)
        self.btn_select.pack(fill='x', expand=True)

        self._populate_listbox_and_select()

    def _build_preset_maps(self):
        """（重新）构建用于显示和查找的字典"""
        self.presets = self.instance_data.get('presets', {})
        self.id_to_name = {}
        self.name_to_id = {}

        for preset_id, data in self.presets.items():
            if data.get('is_default'):
                display_name = _(data["name_key"])
            else:
                display_name = data.get("name", f"Preset {preset_id}")

            self.id_to_name[preset_id] = display_name
            self.name_to_id[display_name] = preset_id

    def _populate_listbox_and_select(self):
        """填充列表框，并选中当前活动的预设"""
        self._build_preset_maps()
        self.preset_listbox.delete(0, 'end')

        active_index = 0
        sorted_names = sorted(self.name_to_id.keys())

        for i, name in enumerate(sorted_names):
            self.preset_listbox.insert('end', name)
            if self.name_to_id[name] == self.active_preset_id:
                active_index = i

        self.preset_listbox.selection_set(active_index)
        self.preset_listbox.activate(active_index)
        self.preset_listbox.see(active_index)
        self._on_listbox_select()

    def _get_selected_listbox_id(self):
        """从列表框中获取当前所选内容的 preset_id"""
        try:
            selected_name = self.preset_listbox.get(self.preset_listbox.curselection())
            return self.name_to_id.get(selected_name)
        except tk.TclError:
            return None

    def _on_listbox_select(self, event=None):
        """当列表框中的选择更改时，更新右侧的控件"""
        preset_id = self._get_selected_listbox_id()
        if not preset_id:
            return

        preset_data = self.presets.get(preset_id)
        if not preset_data:
            return

        lang_code = preset_data.get('lang_code', 'en')
        lang_name = self.l10n_id_to_name.get(lang_code, self.l10n_id_to_name.get('en'))
        self.lang_combobox.set(lang_name)

        self._update_route_combobox(lang_code)

        route_id = preset_data.get('download_route', 'gitee')
        route_name = self.route_id_to_name.get(route_id, _('l10n.route.gitee'))
        self.route_combobox.set(route_name)

        use_ee = preset_data.get('use_ee', True)
        use_mods = preset_data.get('use_mods', True)
        self.use_ee_var.set(use_ee)
        self.use_mods_var.set(use_mods)

        is_default = preset_data.get('is_default', False)
        btn_state = 'disabled' if is_default else 'normal'

        self.lang_combobox.config(state='readonly')
        self.route_combobox.config(state='readonly')
        self.cb_use_ee.config(state='normal')
        self.cb_use_mods.config(state='normal')

        self.btn_rename.config(state=btn_state)
        self.btn_delete.config(state=btn_state)

        self._update_download_mods_btn_state(lang_code)

    def _on_lang_select_changed(self, event=None):
        """当语言下拉框更改时，动态更新下载线路下拉框"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)

        self._update_route_combobox(lang_code)

        self._update_download_mods_btn_state(lang_code)

    def _update_route_combobox(self, lang_code: str):
        """根据 lang_code 填充 route_combobox"""
        if not lang_code:
            self.route_combobox.config(values=[])
            self.route_combobox.set('')
            return

        available_route_ids = global_source_manager.get_routes_for_source(lang_code)
        display_names = [self.route_id_to_name.get(id, id) for id in available_route_ids if id in self.route_id_to_name]
        self.route_combobox.config(values=display_names)

        current_preset_id = self._get_selected_listbox_id()
        if current_preset_id:
            current_route_id = self.presets[current_preset_id].get('download_route', 'gitee')
            current_route_name = self.route_id_to_name.get(current_route_id)
            if current_route_name in display_names:
                self.route_combobox.set(current_route_name)
                return

        gitee_name = _('l10n.route.gitee')
        if gitee_name in display_names:
            self.route_combobox.set(gitee_name)
        elif display_names:
            self.route_combobox.set(display_names[0])
        else:
            self.route_combobox.set('')

    def _update_download_mods_btn_state(self, lang_code: str):
        """根据 lang_code 启用/禁用 mods 下载按钮"""
        if global_source_manager.get_mods_url(lang_code):
            self.btn_download_mods.config(state='normal')
        else:
            self.btn_download_mods.config(state='disabled')

    def _new_preset(self):
        # (已修改)
        dialog = CustomAskStringDialog(self, _('lki.btn.new'), _('lki.preset.manager.enter_name'))
        new_name = dialog.get_result()

        if not new_name or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name in self.name_to_id:
            messagebox.showwarning(_('lki.btn.new'), _('lki.preset.error.name_exists'), parent=self)
            return

        current_ui_lang = settings.global_settings.language
        default_lang_code = determine_default_l10n_lang(current_ui_lang)
        default_route = 'gitee'
        default_use_ee = True
        default_use_mods = True

        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, default_lang_code, default_route, default_use_ee, default_use_mods
        )
        self._populate_listbox_and_select()

    def _save_as_preset(self):
        # (已修改)
        dialog = CustomAskStringDialog(self, _('lki.btn.save_as'), _('lki.preset.manager.enter_name'))
        new_name = dialog.get_result()

        if not new_name or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name in self.name_to_id:
            messagebox.showwarning(_('lki.btn.save_as'), _('lki.preset.error.name_exists'), parent=self)
            return

        current_lang_name = self.lang_combobox.get()
        current_lang_code = self.l10n_name_to_id.get(current_lang_name, 'en')
        current_route_name = self.route_combobox.get()
        current_route_id = self.route_name_to_id.get(current_route_name, 'gitee')
        current_use_ee = self.use_ee_var.get()
        current_use_mods = self.use_mods_var.get()

        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, current_lang_code, current_route_id, current_use_ee, current_use_mods
        )
        self._populate_listbox_and_select()

    def _save_preset(self):
        """保存对当前所选预设的更改"""
        preset_id = self._get_selected_listbox_id()
        if not preset_id:
            return

        new_lang_name = self.lang_combobox.get()
        new_lang_code = self.l10n_name_to_id.get(new_lang_name)
        new_route_name = self.route_combobox.get()
        new_route_id = self.route_name_to_id.get(new_route_name, 'gitee')
        new_use_ee = self.use_ee_var.get()
        new_use_mods = self.use_mods_var.get()

        self.instance_manager.update_preset_data(self.instance_id, preset_id, {
            "lang_code": new_lang_code,
            "download_route": new_route_id,
            "use_ee": new_use_ee,
            "use_mods": new_use_mods
        })
        messagebox.showinfo(_('lki.btn.save_changes'), _('lki.preset.manager.saved'), parent=self)

    def _rename_preset(self):
        preset_id = self._get_selected_listbox_id()
        if not preset_id or self.presets[preset_id].get('is_default'):
            return

        current_name = self.id_to_name[preset_id]
        # (已修改)
        dialog = CustomAskStringDialog(self,
                                       _('lki.btn.rename'),
                                       _('lki.preset.manager.enter_name'),
                                       initialvalue=current_name)
        new_name = dialog.get_result()

        if not new_name or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name != current_name and new_name in self.name_to_id:
            messagebox.showwarning(_('lki.btn.rename'), _('lki.preset.error.name_exists'), parent=self)
            return

        self.instance_manager.rename_preset(self.instance_id, preset_id, new_name)
        self._populate_listbox_and_select()

    def _delete_preset(self):
        preset_id = self._get_selected_listbox_id()
        if not preset_id or self.presets[preset_id].get('is_default'):
            return

        name = self.id_to_name[preset_id]
        if messagebox.askyesno(_('lki.btn.delete'), _('lki.preset.manager.confirm_delete') + f"\n\n{name}",
                               parent=self):
            self.instance_manager.delete_preset(self.instance_id, preset_id)

            if self.active_preset_id == preset_id:
                self.active_preset_id = 'default'
                self.instance_manager.update_instance_data(self.instance_id, {'active_preset_id': 'default'})

            self._populate_listbox_and_select()

    def _select_and_close(self):
        """将列表框中选中的预设应用到实例，并关闭窗口"""
        selected_id = self._get_selected_listbox_id()
        if selected_id and selected_id != self.active_preset_id:
            self.instance_manager.update_instance_data(self.instance_id, {'active_preset_id': selected_id})

        self.on_close_callback()
        self.destroy()

    def _open_mods_folder(self):
        """打开当前实例的 l10n_mods 文件夹"""
        if not self.instance_data:
            return

        mods_path = os.path.join(self.instance_data['path'], 'lki', 'l10n_mods')
        os.makedirs(mods_path, exist_ok=True)

        try:
            subprocess.run(['explorer', os.path.normpath(mods_path)])
        except Exception as e:
            print(f"Error opening mods folder: {e}")
            webbrowser.open(f'file:///{mods_path}')

    def _open_mods_download(self):
        """打开当前选定语言的 mods 下载链接"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)
        if not lang_code:
            return

        mods_url = global_source_manager.get_mods_url(lang_code)
        if mods_url:
            webbrowser.open(mods_url)