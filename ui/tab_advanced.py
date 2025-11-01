import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import webbrowser
from typing import Optional, List

import settings  # <-- (新增导入)
import instance_manager
from localizer import _
from localization_sources import global_source_manager
from utils import determine_default_l10n_lang
from ui.dialogs import CustomAskStringDialog, BaseDialog
from game_instance import GameInstance, GameVersion

try:
    from tktooltip import ToolTip
except ImportError:
    print("Warning: tktooltip not found. Tooltips will be disabled.")
    ToolTip = None


class AdvancedTab(ttk.Frame):
    """
    “高级”选项卡 UI。
    """

    def __init__(self, master, icons, type_id_to_name):
        super().__init__(master, padding='10 10 10 10')

        self.app_master = master.master
        self.icons = icons

        self.instance_manager = instance_manager.global_instance_manager
        self.current_instance: Optional[GameInstance] = None
        self.preset_id_to_display_name = {}
        self.display_name_to_preset_id = {}

        self.l10n_id_to_name, self.l10n_name_to_id = global_source_manager.get_display_maps()
        self.route_id_to_name = {
            'gitee': _('l10n.route.gitee'),
            'gitlab': _('l10n.route.gitlab'),
            'github': _('l10n.route.github'),
            'cloudflare': _('l10n.route.cloudflare')  # <-- (新增)
        }

        # 占位符
        self.advanced_tab_placeholder = ttk.Label(
            self,
            text=_('lki.advanced.please_select'),
            wraplength=320,
            justify='center'
        )
        self.advanced_tab_placeholder.pack(pady=20, padx=20, fill='x')

        # 实际内容的框架
        self.advanced_tab_frame = ttk.Frame(self, padding=10)

    def update_content(self, instance: Optional[GameInstance]):
        """
        由主 APP 调用，以使用所选实例的数据更新此选项卡。
        如果 instance 为 None，则显示占位符。
        """
        self.current_instance = instance

        for widget in self.advanced_tab_frame.winfo_children():
            widget.destroy()

        if self.current_instance:
            self._build_preset_maps()
            self.advanced_tab_placeholder.pack_forget()
            self._build_advanced_widgets()
            self.advanced_tab_frame.pack(fill='both', expand=True, anchor='n')
        else:
            self.advanced_tab_frame.pack_forget()
            self.advanced_tab_placeholder.pack(pady=20, padx=20, fill='x')

    def _build_preset_maps(self):
        """从 *当前选定的实例* 加载预设并构建查找字典"""
        if not self.current_instance:
            self.preset_id_to_display_name = {}
            self.display_name_to_preset_id = {}
            return

        instance = self.instance_manager.get_instance(self.current_instance.instance_id)
        if not instance:
            return

        presets_dict = instance.get('presets', {})

        self.preset_id_to_display_name = {}
        self.display_name_to_preset_id = {}

        for preset_id, data in presets_dict.items():
            if data.get('is_default'):
                display_name = _(data["name_key"])
            else:
                display_name = data.get("name", f"Preset {preset_id}")

            self.preset_id_to_display_name[preset_id] = display_name
            self.display_name_to_preset_id[display_name] = preset_id

    def _build_advanced_widgets(self):
        """在 advanced_tab_frame 中创建实际的控件"""

        instance_data = self.instance_manager.get_instance(self.current_instance.instance_id)
        if not instance_data:
            return

        # --- (1. 实例信息框) ---
        instance_details_frame = ttk.LabelFrame(self.advanced_tab_frame,
                                                text=_('lki.advanced.instance_details'),
                                                padding=(10, 5))
        instance_details_frame.pack(fill='x', expand=True)

        name_text = f"{_('lki.game.name_label')} {self.current_instance.name}"
        name_label = ttk.Label(instance_details_frame, text=name_text, style="Client.TLabel")
        name_label.pack(anchor='w', pady=(0, 5))

        type_key = f"lki.game.client_type.{self.current_instance.type}"
        type_text = f"{_('lki.game.type_label')} {_(type_key)}"
        type_label = ttk.Label(instance_details_frame, text=type_text, style="Path.TLabel")
        type_label.pack(anchor='w')

        path_text = f"{_('lki.game.path_label')} {self.current_instance.path}"
        path_label = ttk.Label(instance_details_frame, text=path_text, style="Path.TLabel", wraplength=500)
        path_label.pack(anchor='w')

        version_main_label = ttk.Label(instance_details_frame, text=f"{_('lki.game.version_label')}",
                                       style="Path.TLabel")
        version_main_label.pack(anchor='w', pady=(5, 0))

        versions_to_display = self.current_instance.versions[:2]

        if not versions_to_display:
            status_text = _('lki.game.version_not_found')
            status_label = ttk.Label(instance_details_frame, text=status_text, style="Path.TLabel")
            status_label.pack(anchor='w', padx=(10, 0))
        else:
            for game_version in versions_to_display:
                ver_str = game_version.exe_version or _('lki.game.version_unknown')
                version_text = f"{ver_str}"

                if game_version.l10n_info:
                    l10n_ver_full = game_version.l10n_info.version
                    l10n_ver_sub = game_version.l10n_info.l10n_sub_version
                    l10n_lang_code = game_version.l10n_info.lang_code

                    # (使用完整语言名称)
                    l10n_lang_name = self.l10n_id_to_name.get(l10n_lang_code, l10n_lang_code)
                    lang_str = f"{l10n_lang_name} " if l10n_lang_code else ""

                    if l10n_ver_full == "INACTIVE":
                        l10n_details = f"({_('lki.game.l10n_status.inactive')})"
                    elif game_version.verify_files():
                        display_ver = l10n_ver_sub if l10n_ver_sub else l10n_ver_full
                        l10n_details = f"({lang_str}{display_ver} - {_('lki.game.l10n_status.ok')})"
                    else:
                        display_ver = l10n_ver_sub if l10n_ver_sub else l10n_ver_full
                        l10n_details = f"({lang_str}{display_ver} - {_('lki.game.l10n_status.corrupted')})"

                    l10n_text = f" {l10n_details}"  # (移除了破折号)
                else:
                    l10n_text = f" ({_('lki.game.l10n_status.not_installed')})"

                full_version_string = version_text + l10n_text
                version_label = ttk.Label(instance_details_frame, text=full_version_string, style="Path.TLabel")
                version_label.pack(anchor='w', padx=(10, 0))

        # --- (2. 预设配置框) ---
        preset_config_frame = ttk.LabelFrame(self.advanced_tab_frame,
                                             text=_('lki.advanced.preset_details'),
                                             padding=(10, 5))
        preset_config_frame.pack(fill='x', expand=True, pady=(5, 0))
        preset_config_frame.columnconfigure(1, weight=1)

        # --- (2a. 预设选择行) ---
        preset_label = ttk.Label(preset_config_frame, text=_('lki.advanced.preset_label'))
        preset_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=(0, 10))

        self.preset_combobox = ttk.Combobox(preset_config_frame, values=list(self.preset_id_to_display_name.values()),
                                            state='readonly')
        self.preset_combobox.grid(row=0, column=1, sticky='we', pady=(0, 10))
        self.preset_combobox.bind("<<ComboboxSelected>>", self._on_preset_select)

        self.manage_preset_btn = ttk.Button(
            preset_config_frame,
            image=self.icons.manage,
            style="Toolbutton",
            command=self._open_preset_manager
        )
        self.manage_preset_btn.grid(row=0, column=2, sticky='e', padx=(5, 0), pady=(0, 10))

        # --- (2b. 分隔符) ---
        ttk.Separator(preset_config_frame).grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)

        # --- (2c. 预设详情) ---
        self.preset_lang_label = ttk.Label(preset_config_frame, text="Language:")
        self.preset_lang_label.grid(row=2, column=0, columnspan=3, sticky='w', padx=5)

        self.preset_route_label = ttk.Label(preset_config_frame, text="Route:")
        self.preset_route_label.grid(row=3, column=0, columnspan=3, sticky='w', padx=5)

        self.preset_ee_label = ttk.Label(preset_config_frame, text="EE Pack:")
        self.preset_ee_label.grid(row=4, column=0, columnspan=3, sticky='w', padx=5)

        self.preset_mods_label = ttk.Label(preset_config_frame, text="Mods:")
        self.preset_mods_label.grid(row=5, column=0, columnspan=3, sticky='w', padx=5)

        self.preset_fonts_label = ttk.Label(preset_config_frame, text="Fonts:")  # <-- (新增)
        self.preset_fonts_label.grid(row=6, column=0, columnspan=3, sticky='w', padx=5)  # <-- (新增)

        # --- (3. 初始填充) ---
        self._update_preset_combobox()
        self._update_preset_details_display()

    def _update_preset_combobox(self):
        """（重新）填充预设下拉框并设置当前值"""
        self.preset_combobox.config(values=list(self.preset_id_to_display_name.values()))

        instance = self.instance_manager.get_instance(self.current_instance.instance_id)
        current_preset_id = instance.get('active_preset_id', 'default')
        current_preset_name = self.preset_id_to_display_name.get(current_preset_id, _('lki.preset.default.name'))
        self.preset_combobox.set(current_preset_name)

    def _on_preset_select(self, event=None):
        """当“高级”选项卡中的预设被更改时调用"""
        selected_name = self.preset_combobox.get()
        selected_id = self.display_name_to_preset_id.get(selected_name, 'default')

        if selected_id and self.current_instance:
            print(f"Updating instance {self.current_instance.instance_id} active preset to {selected_id}")
            self.instance_manager.update_instance_data(
                self.current_instance.instance_id,
                {'active_preset_id': selected_id}
            )

            self._update_preset_details_display()

    # (已修改：从 global_settings 获取路由)
    def _update_preset_details_display(self):
        """更新预设详情框架中的标签文本"""
        if not self.current_instance:
            return

        instance_data = self.instance_manager.get_instance(self.current_instance.instance_id)
        if not instance_data:
            return

        active_preset_id = instance_data.get('active_preset_id', 'default')
        preset_data = instance_data.get('presets', {}).get(active_preset_id)

        if not preset_data:
            return

        lang_code = preset_data.get('lang_code', 'en')
        lang_name = self.l10n_id_to_name.get(lang_code, lang_code)
        self.preset_lang_label.config(text=f"{_('lki.preset.manager.language')} {lang_name}")

        # (已修改：从 global_settings 获取路由)
        route_ids = settings.global_settings.get('download_routes_priority', ['gitee'])
        route_names = [self.route_id_to_name.get(rid, rid) for rid in route_ids]
        route_str = ", ".join(route_names)
        self.preset_route_label.config(text=f"{_('lki.preset.manager.route')} {route_str}")

        use_ee = preset_data.get('use_ee', True)
        ee_text = _('lki.generic.yes') if use_ee else _('lki.generic.no')
        self.preset_ee_label.config(text=f"{_('lki.preset.manager.use_ee')}: {ee_text}")

        use_mods = preset_data.get('use_mods', True)
        mods_text = _('lki.generic.yes') if use_mods else _('lki.generic.no')
        self.preset_mods_label.config(text=f"{_('lki.preset.manager.use_mods')}: {mods_text}")

        use_fonts = preset_data.get('use_fonts', True)  # <-- (新增)
        fonts_text = _('lki.generic.yes') if use_fonts else _('lki.generic.no')  # <-- (新增)
        self.preset_fonts_label.config(text=f"{_('lki.preset.manager.use_fonts')}: {fonts_text}")  # <-- (新增)

    def _open_preset_manager(self):
        """打开预设管理器窗口"""
        if not self.current_instance:
            return

        window = PresetManagerWindow(self.app_master, self, self.current_instance.instance_id,
                                     self._on_preset_manager_close)

    def _on_preset_manager_close(self):
        """当预设管理器关闭时，由其调用的回调函数"""
        print("Preset manager closed. Refreshing preset combobox.")
        self._build_preset_maps()
        self._update_preset_combobox()
        self._update_preset_details_display()

    def update_icons(self):
        """当主题更改时更新此选项卡上的图标"""
        if hasattr(self, 'manage_preset_btn'):
            self.manage_preset_btn.config(image=self.icons.manage)


# --- (PresetManagerWindow 已重构：移除了路由排序) ---
class PresetManagerWindow(BaseDialog):
    """一个用于管理（CRUD）预设的弹出窗口。"""

    def __init__(self, parent_tk, parent_app: AdvancedTab, instance_id, on_close_callback):
        super().__init__(parent_tk)
        self.parent_app = parent_app
        self.instance_id = instance_id
        self.on_close_callback = on_close_callback

        self.icons = self.parent_app.icons

        self.title(_('lki.preset.manager.title'))

        self.instance_manager = instance_manager.global_instance_manager
        self.instance_data = self.instance_manager.get_instance(self.instance_id)
        self.active_preset_id = self.instance_data.get('active_preset_id', 'default')

        self.l10n_id_to_name, self.l10n_name_to_id = global_source_manager.get_display_maps()

        self.use_ee_var = tk.BooleanVar()
        self.use_mods_var = tk.BooleanVar()
        self.use_fonts_var = tk.BooleanVar()  # <-- (新增)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=0, column=0, sticky='ns', padx=(0, 10))

        self.preset_listbox = tk.Listbox(list_frame, exportselection=False, height=10)
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

        # --- (路由 UI 已移除) ---

        self.cb_use_ee = ttk.Checkbutton(self.details_frame, text=_('lki.preset.manager.use_ee'),
                                         variable=self.use_ee_var)
        self.cb_use_ee.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 0))  # (row 已修改)

        mods_frame = ttk.Frame(self.details_frame)
        mods_frame.grid(row=3, column=0, columnspan=2, sticky='we', pady=5)  # (row 已修改)

        self.cb_use_mods = ttk.Checkbutton(mods_frame, text=_('lki.preset.manager.use_mods'),
                                           variable=self.use_mods_var)
        self.cb_use_mods.pack(side='left')

        self.btn_open_mods_dir = ttk.Button(mods_frame, image=self.icons.folder, style="Toolbutton",
                                            command=self._open_mods_folder)
        self.btn_open_mods_dir.pack(side='left', padx=(5, 0))

        self.btn_download_mods = ttk.Button(mods_frame, image=self.icons.download, style="Toolbutton",
                                            command=self._open_mods_download)
        self.btn_download_mods.pack(side='left', padx=5)

        if ToolTip:
            ToolTip(self.btn_open_mods_dir, _('lki.preset.manager.tooltip_open_mods_dir'))
            ToolTip(self.btn_download_mods, _('lki.preset.manager.tooltip_download_mods'))

        self.cb_use_fonts = ttk.Checkbutton(self.details_frame, text=_('lki.preset.manager.use_fonts'),  # <-- (新增)
                                            variable=self.use_fonts_var)
        self.cb_use_fonts.grid(row=4, column=0, columnspan=2, sticky='w', pady=(5, 0))  # <-- (新增)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))

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
        select_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))
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

        is_default = preset_data.get('is_default', False)
        btn_state = 'disabled' if is_default else 'normal'

        lang_code = preset_data.get('lang_code', 'en')
        lang_name = self.l10n_id_to_name.get(lang_code, self.l10n_id_to_name.get('en'))
        self.lang_combobox.set(lang_name)

        # (已修改：语言在默认预设中可编辑)
        self.lang_combobox.config(state='readonly')

        use_ee = preset_data.get('use_ee', True)
        use_mods = preset_data.get('use_mods', True)
        use_fonts = preset_data.get('use_fonts', True)  # <-- (新增)
        self.use_ee_var.set(use_ee)
        self.use_mods_var.set(use_mods)
        self.use_fonts_var.set(use_fonts)  # <-- (新增)

        self.cb_use_ee.config(state='normal')
        self.cb_use_mods.config(state='normal')
        self.cb_use_fonts.config(state='normal')  # <-- (新增)

        self.btn_rename.config(state=btn_state)
        self.btn_delete.config(state=btn_state)

        self._update_download_mods_btn_state(lang_code)

    def _on_lang_select_changed(self, event=None):
        """当语言下拉框更改时，动态更新下载线路下拉框"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)
        self._update_download_mods_btn_state(lang_code)

    # --- (路由相关方法已移除) ---

    def _update_download_mods_btn_state(self, lang_code: str):
        """根据 lang_code 启用/禁用 mods 下载按钮"""
        if global_source_manager.get_mods_url(lang_code):
            self.btn_download_mods.config(state='normal')
        else:
            self.btn_download_mods.config(state='disabled')

    def _new_preset(self):
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
        default_use_ee = True
        default_use_mods = True
        default_use_fonts = True  # <-- (新增)

        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, default_lang_code, default_use_ee, default_use_mods, default_use_fonts
        )
        self._populate_listbox_and_select()

    def _save_as_preset(self):
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
        current_use_ee = self.use_ee_var.get()
        current_use_mods = self.use_mods_var.get()
        current_use_fonts = self.use_fonts_var.get()  # <-- (新增)

        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, current_lang_code, current_use_ee, current_use_mods, current_use_fonts
        )
        self._populate_listbox_and_select()

    def _save_preset(self):
        """保存对当前所选预设的更改"""
        preset_id = self._get_selected_listbox_id()
        if not preset_id:
            return

        preset_data = self.presets.get(preset_id)
        if not preset_data:
            return

        is_default = preset_data.get('is_default', False)

        new_lang_name = self.lang_combobox.get()
        new_lang_code = self.l10n_name_to_id.get(new_lang_name)
        new_use_ee = self.use_ee_var.get()
        new_use_mods = self.use_mods_var.get()
        new_use_fonts = self.use_fonts_var.get()  # <-- (新增)

        data_to_save = {
            "lang_code": new_lang_code,
            "use_ee": new_use_ee,
            "use_mods": new_use_mods,
            "use_fonts": new_use_fonts  # <-- (新增)
        }

        if not is_default:
            data_to_save["name"] = preset_data.get('name')

        self.instance_manager.update_preset_data(self.instance_id, preset_id, data_to_save)
        messagebox.showinfo(_('lki.btn.save_changes'), _('lki.preset.manager.saved'), parent=self)

        self.parent_app.update_content(self.parent_app.current_instance)

    def _rename_preset(self):
        preset_id = self._get_selected_listbox_id()
        if not preset_id or self.presets[preset_id].get('is_default'):
            return

        current_name = self.id_to_name[preset_id]
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
        """打开当前定语言的 mods 下载链接"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)
        if not lang_code:
            return

        mods_url = global_source_manager.get_mods_url(lang_code)
        if mods_url:
            webbrowser.open(mods_url)