import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import settings
from localizer import _
import instance_manager
from localization_sources import global_source_manager
from utils import determine_default_l10n_lang


class ProxyConfigWindow(tk.Toplevel):
    # (已修改：使用 lki.btn.* 键)
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

        # (已修改)
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

    def __init__(self, parent, instance_id, on_close_callback):
        super().__init__(parent)
        self.parent = parent
        self.instance_id = instance_id
        self.on_close_callback = on_close_callback

        self.title(_('lki.preset.manager.title'))
        self.transient(parent)
        self.grab_set()

        self.instance_manager = instance_manager.global_instance_manager
        self.instance_data = self.instance_manager.get_instance(self.instance_id)
        self.active_preset_id = self.instance_data.get('active_preset_id', 'default')

        self.l10n_id_to_name, self.l10n_name_to_id = global_source_manager.get_display_maps()

        # --- (新增：下载线路映射表) ---
        self.route_id_to_name = {
            'gitee': _('l10n.route.gitee'),
            'gitlab': _('l10n.route.gitlab'),
            'github': _('l10n.route.github')
        }
        self.route_name_to_id = {v: k for k, v in self.route_id_to_name.items()}
        # --- (新增结束) ---

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

        # --- (新增：下载线路) ---
        ttk.Label(self.details_frame, text=_('lki.preset.manager.route')).grid(row=1, column=0, sticky='e',
                                                                               padx=(0, 10), pady=5)
        self.route_combobox = ttk.Combobox(self.details_frame, state='readonly')
        self.route_combobox.grid(row=1, column=1, sticky='we', pady=5)
        # --- (新增结束) ---

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0)) # (行号已更改)

        # (已修改)
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
        select_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 0)) # (行号已更改)
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

        # 1. 设置语言
        lang_code = preset_data.get('lang_code', 'en')
        lang_name = self.l10n_id_to_name.get(lang_code, self.l10n_id_to_name.get('en'))
        self.lang_combobox.set(lang_name)

        # 2. (新增) 更新下载线路下拉框
        self._update_route_combobox(lang_code)

        # 3. (新增) 设置下载线路
        route_id = preset_data.get('download_route', 'gitee')
        route_name = self.route_id_to_name.get(route_id, _('l10n.route.gitee'))
        self.route_combobox.set(route_name)

        # 4. 启用/禁用按钮
        is_default = preset_data.get('is_default', False)
        btn_state = 'disabled' if is_default else 'normal'

        self.btn_rename.config(state=btn_state)
        self.btn_delete.config(state=btn_state)

    def _on_lang_select_changed(self, event=None):
        """当语言下拉框更改时，动态更新下载线路下拉框"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)

        self._update_route_combobox(lang_code)

    def _update_route_combobox(self, lang_code: str):
        """根据 lang_code 填充 route_combobox"""
        if not lang_code:
            self.route_combobox.config(values=[])
            self.route_combobox.set('')
            return

        available_route_ids = global_source_manager.get_routes_for_source(lang_code)
        # 转换为显示名称
        display_names = [self.route_id_to_name.get(id, id) for id in available_route_ids if id in self.route_id_to_name]
        self.route_combobox.config(values=display_names)

        # 尝试设置 'Gitee' (翻译后的) 为默认
        gitee_name = _('l10n.route.gitee')
        if gitee_name in display_names:
            self.route_combobox.set(gitee_name)
        elif display_names:
            self.route_combobox.set(display_names[0])
        else:
            self.route_combobox.set('')

    def _new_preset(self):
        new_name = simpledialog.askstring(_('lki.btn.new'), _('lki.preset.manager.enter_name'), parent=self)
        if not new_name or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name in self.name_to_id:
            messagebox.showwarning(_('lki.btn.new'), _('lki.preset.error.name_exists'), parent=self)
            return

        current_ui_lang = settings.global_settings.language
        default_lang_code = determine_default_l10n_lang(current_ui_lang)
        default_route = 'gitee' # 新预设的默认路由

        self.active_preset_id = self.instance_manager.add_preset(self.instance_id, new_name, default_lang_code,
                                                                 default_route)
        self._populate_listbox_and_select()

    def _save_as_preset(self):
        new_name = simpledialog.askstring(_('lki.btn.save_as'), _('lki.preset.manager.enter_name'), parent=self)
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

        self.active_preset_id = self.instance_manager.add_preset(self.instance_id, new_name, current_lang_code,
                                                                 current_route_id)
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

        self.instance_manager.update_preset_data(self.instance_id, preset_id, {
            "lang_code": new_lang_code,
            "download_route": new_route_id
        })
        messagebox.showinfo(_('lki.btn.save_changes'), _('lki.preset.manager.saved'), parent=self) # (已修改)

    def _rename_preset(self):
        preset_id = self._get_selected_listbox_id()
        if not preset_id or self.presets[preset_id].get('is_default'):
            return

        current_name = self.id_to_name[preset_id]
        new_name = simpledialog.askstring(_('lki.btn.rename'), _('lki.preset.manager.enter_name'),
                                          initialvalue=current_name, parent=self)

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