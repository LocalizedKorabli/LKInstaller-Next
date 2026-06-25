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
import os
import subprocess
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox
from typing import Optional

from core import settings
from core import utils
from instance import instance_manager
from instance.game_instance import GameInstance
from installation.localization_sources import global_source_manager, get_route_id_to_name, FONT_IDS, FONT_DISPLAY_KEYS
from core.localizer import _
from core.logger import log
from ui.dialogs import CustomAskStringDialog, BaseDialog, AutoUpdateConfigDialog  # (已修改)
from ui.tabs.tab_base import BaseTab
from core.utils import determine_default_l10n_lang

from tktooltip import ToolTip

class AdvancedTab(BaseTab):
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

        self.advanced_tab_placeholder = self._create_placeholder_label(_('lki.advanced.please_select'))
        self.advanced_tab_placeholder.pack(pady=20, padx=20)

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
            self.advanced_tab_placeholder.pack(pady=20, padx=20)

    def _on_tab_configure(self, event):
        """当 'AdvancedTab' 框架的大小改变时，动态更新占位符的 wraplength。"""

        # event.width 是 AdvancedTab 的内容区域宽度 (已减去其自身的 padding)

        # 我们只需要减去 placeholder 自己的水平 padding
        # (padx=20, 左右各 20)
        # 总计 = 40
        base_padding = 40

        scaled_padding = utils.scale_dpi(self, base_padding)

        new_wraplength = event.width - scaled_padding

        if new_wraplength < 1:
            new_wraplength = 1

        try:
            self.advanced_tab_placeholder.config(wraplength=new_wraplength)
        except tk.TclError:
            pass  # 窗口可能正在销毁中

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
        path_label = ttk.Label(instance_details_frame, text=path_text, style="Path.TLabel",
                               wraplength=utils.scale_dpi(self, 500))
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
            # (新增) 获取活动预设，以检查 'use' 标志
            active_preset_id = instance_data.get('active_preset_id', 'default')
            preset_data = instance_data.get('presets', {}).get(active_preset_id, {})

            preset_use_ee = preset_data.get("use_ee", False)
            preset_use_fonts = preset_data.get("use_fonts", False)
            preset_use_mods = preset_data.get("use_mods", False)

            for game_version in versions_to_display:
                # 重新加载 installation_info.json 以反映最近安装的变化
                game_version.load_details()
                ver_str = game_version.exe_version or _('lki.game.version_unknown')
                version_text = f"{ver_str}: "

                # --- (修改：高级选项卡的详细状态) ---
                if game_version.l10n_info:
                    l10n_ver_full = game_version.l10n_info.version

                    if l10n_ver_full == "INACTIVE":
                        l10n_text = f"{_('lki.game.i18n_status.inactive')}"
                    else:
                        # (已修改：现在包含所有 3 个组件)
                        statuses = game_version.get_component_statuses()

                        l10n_sub_ver = game_version.l10n_info.l10n_sub_version
                        l10n_lang_code = game_version.l10n_info.lang_code
                        l10n_lang_name = self.l10n_id_to_name.get(l10n_lang_code, l10n_lang_code)
                        lang_str = f" {l10n_lang_name}" if l10n_lang_name else ""

                        status_map = {
                            "ok": "✔️",
                            "tampered": "❗",
                            "not_installed": "❌",
                            "not_required": "⭕"
                        }

                        status_lines = []

                        # 1. 本地化包 (始终被跟踪)
                        if "i18n" in statuses:
                            sub_ver = l10n_sub_ver if (l10n_sub_ver and statuses["i18n"] == "ok") else ""
                            ver_str = f" {sub_ver}" if statuses["i18n"] == "ok" else ""
                            status_lines.append(
                                f"{_('lki.component.i18n')}: {status_map.get(statuses['i18n'])}{lang_str}{ver_str}")

                        # 2. 体验增强包 (检查预设)
                        if "ee" in statuses:
                            ee_status = statuses['ee']
                            if not preset_use_ee and ee_status == "not_installed":
                                ee_status = "not_required"  # (覆盖)
                            status_lines.append(f"{_('lki.component.ee')}: {status_map.get(ee_status)}")

                        # 3. 字体优化包 (检查预设)
                        if "font" in statuses:
                            font_status = statuses['font']
                            # 解析 True（跟随推荐）→ 实际字体 ID
                            effective_font = preset_use_fonts
                            if effective_font is True:
                                preset_lang = preset_data.get('lang_code', 'en')
                                effective_font = global_source_manager.get_default_font_id(preset_lang)
                            if not effective_font:
                                font_status = "not_required"  # 预设不要求字体，忽略实际文件状态
                            # 显示字体类型和版本
                            font_detail = ""
                            if font_status == "ok" and statuses.get('font_id'):
                                font_display_key = FONT_DISPLAY_KEYS.get(statuses['font_id'])
                                font_name = _(font_display_key) if font_display_key else statuses['font_id']
                                fv = statuses.get('font_version', '')
                                font_detail = f" {font_name}" + (f" v{fv}" if fv else "")
                            status_lines.append(f"{_('lki.component.font')}: {status_map.get(font_status)}{font_detail}")

                        if "mods" in statuses:
                            mods_status = statuses['mods']
                            if not preset_use_mods and mods_status == "not_installed":
                                mods_status = "not_required"  # (覆盖)
                            status_lines.append(f"{_('lki.component.mods')}: {status_map.get(mods_status)}")

                        l10n_text = "\n" + "\n".join(status_lines)
                else:
                    # (l10n_info 为 None，即从未安装过)
                    l10n_text = "\n"

                    status_map_alt = {"not_installed": "❌", "not_required": "⭕"}

                    # 1. 本地化包
                    status_lines = [f"{_('lki.component.i18n')}: {status_map_alt.get('not_installed')}"]

                    # 2. 体验增强包 (根据预设决定显示 ❌ 还是 ⭕)
                    ee_status_key = "not_installed" if preset_use_ee else "not_required"
                    status_lines.append(f"{_('lki.component.ee')}: {status_map_alt.get(ee_status_key)}")

                    # 3. 字体优化包 (根据预设决定显示 ❌ 还是 ⭕)
                    font_status_key = "not_installed" if preset_use_fonts else "not_required"
                    status_lines.append(f"{_('lki.component.font')}: {status_map_alt.get(font_status_key)}")

                    # 4. 本地化修改包 (根据预设决定显示 ❌ 还是 ⭕)
                    mods_status_key = "not_installed" if preset_use_mods else "not_required"
                    status_lines.append(f"{_('lki.component.mods')}: {status_map_alt.get(mods_status_key)}")

                    l10n_text += "\n".join(status_lines)
                    # --- (修改结束) ---

                full_version_string = version_text + l10n_text

                version_label = ttk.Label(instance_details_frame, text=full_version_string, style="Path.TLabel",
                                          justify='left')
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

        self.preset_fonts_label = ttk.Label(preset_config_frame, text="Fonts:")
        self.preset_fonts_label.grid(row=6, column=0, columnspan=3, sticky='w', padx=5)

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
            log(f"Updating instance {self.current_instance.instance_id} active preset to {selected_id}")
            self.instance_manager.update_instance_data(
                self.current_instance.instance_id,
                {'active_preset_id': selected_id}
            )

            self.update_content(self.current_instance)

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
        route_ids = settings.global_settings.get('download_routes_priority', [])
        route_names = [get_route_id_to_name().get(rid, rid) for rid in route_ids]
        route_str = ", ".join(route_names)
        self.preset_route_label.config(text=f"{_('lki.preset.manager.route')} {route_str}")

        use_ee = preset_data.get('use_ee', False)
        ee_text = _('lki.generic.yes') if use_ee else _('lki.generic.no')
        self.preset_ee_label.config(text=f"{_('lki.preset.manager.use_ee')}: {ee_text}")

        use_mods = preset_data.get('use_mods', False)
        mods_text = _('lki.generic.yes') if use_mods else _('lki.generic.no')
        self.preset_mods_label.config(text=f"{_('lki.preset.manager.use_mods')}: {mods_text}")

        use_fonts = preset_data.get('use_fonts', False)
        fonts_text = _('lki.generic.yes') if use_fonts else _('lki.generic.no')
        self.preset_fonts_label.config(text=f"{_('lki.preset.manager.use_fonts')}: {fonts_text}")

    def _open_preset_manager(self):
        """打开预设管理器窗口"""
        if not self.current_instance:
            return

        window = PresetManagerWindow(self.app_master, self, self.current_instance.instance_id,
                                     self._on_preset_manager_close)

    def _on_preset_manager_close(self):
        """当预设管理器关闭时，由其调用的回调函数"""
        log("Preset manager closed. Refreshing preset combobox.")
        self._build_preset_maps()
        self._update_preset_combobox()
        self._update_preset_details_display()
        self.update_content(self.current_instance)

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
        self.use_fonts_var = tk.StringVar(value="")

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
                                          state='readonly', width=22)
        self.lang_combobox.grid(row=0, column=1, sticky='we', pady=5)
        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_lang_select_changed)

        # --- (路由 UI 已移除) ---

        # 选项顺序（从上到下）：
        #   1. [实验性] 安装到独立模组目录
        #   2. 本地化语言
        #   3. 安装字体优化包
        #   4. 加载本地化修改包
        #   5. 安装体验增强包

        # Row 2: [实验性] 安装到独立模组目录
        ttk.Label(self.details_frame, text=_('lki.preset.manager.use_lk_mods')).grid(
            row=2, column=0, sticky='e', padx=(0, 10), pady=3)
        self._lk_mods_combo = ttk.Combobox(self.details_frame, state='readonly')
        self._lk_mods_combo.grid(row=2, column=1, sticky='we', pady=3)
        self._lk_mods_combo.lk_mods_values = [
            (_('lki.generic.yes'), True),
            (_('lki.generic.no'), False),
            (_('lki.generic.follow_global'), None),
        ]
        self._lk_mods_combo['values'] = [v[0] for v in self._lk_mods_combo.lk_mods_values]
        ToolTip(self._lk_mods_combo, _('lki.settings.tooltip_use_lk_mods'))

        # Row 3: 字体优化包
        ttk.Label(self.details_frame, text=_('lki.preset.manager.use_fonts')).grid(
            row=3, column=0, sticky='e', padx=(0, 10), pady=3)
        self._font_combo = ttk.Combobox(self.details_frame, state='readonly')
        self._font_combo.grid(row=3, column=1, sticky='we', pady=3)
        # 初始选项（在 update_content 中会根据语言动态重建）
        self._font_id_map = {"": _('lki.preset.manager.font_opt.none')}
        self._font_combo['values'] = [_('lki.preset.manager.font_opt.none')]
        self._display_to_font_id = {_('lki.preset.manager.font_opt.none'): ""}

        # Row 4: 加载本地化修改包
        mods_frame = ttk.Frame(self.details_frame)
        mods_frame.grid(row=4, column=1, sticky='w', pady=3)

        self.cb_use_mods = ttk.Checkbutton(mods_frame, text=_('lki.preset.manager.use_mods'),
                                           variable=self.use_mods_var)
        self.cb_use_mods.pack(side='left')

        self.btn_open_mods_dir = ttk.Button(mods_frame, image=self.icons.folder, style="Toolbutton",
                                            command=self._open_mods_folder)
        self.btn_open_mods_dir.pack(side='left', padx=(5, 0))

        self.btn_download_mods = ttk.Button(mods_frame, image=self.icons.download, style="Toolbutton",
                                            command=self._open_mods_download)
        self.btn_download_mods.pack(side='left', padx=5)

        self.mods_dir_tooltip = None

        self.mods_dir_tooltip = _('lki.preset.manager.tooltip_open_mods_dir')
        ToolTip(self.btn_open_mods_dir, lambda: self.mods_dir_tooltip)
        ToolTip(self.btn_download_mods, _('lki.preset.manager.tooltip_download_mods'))

        # Row 5: 安装体验增强包
        self.cb_use_ee = ttk.Checkbutton(self.details_frame, text=_('lki.preset.manager.use_ee'),
                                         variable=self.use_ee_var)
        self.cb_use_ee.grid(row=5, column=1, sticky='w', pady=(5, 0))

        # ── 按钮栏（统一 grid 布局，两行等宽对齐）──
        btn_grid = ttk.Frame(main_frame)
        btn_grid.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        for i in range(5):
            btn_grid.columnconfigure(i, weight=1)

        self.btn_new = ttk.Button(btn_grid, text=_('lki.btn.new'), command=self._new_preset)
        self.btn_new.grid(row=0, column=0, sticky='ew', padx=(0, 2))

        self.btn_save_as = ttk.Button(btn_grid, text=_('lki.btn.save_as'), command=self._save_as_preset)
        self.btn_save_as.grid(row=0, column=1, sticky='ew', padx=2)

        self.btn_rename = ttk.Button(btn_grid, text=_('lki.btn.rename'), command=self._rename_preset)
        self.btn_rename.grid(row=0, column=2, sticky='ew', padx=2)

        self.btn_delete = ttk.Button(btn_grid, text=_('lki.btn.delete'), command=self._delete_preset)
        self.btn_delete.grid(row=0, column=3, sticky='ew', padx=2)

        self.btn_save = ttk.Button(btn_grid, text=_('lki.btn.save_changes'), command=self._save_preset)
        self.btn_save.grid(row=0, column=4, sticky='ew', padx=(2, 0))

        # 第二行：操作按钮（2 列等宽）
        action_grid = ttk.Frame(main_frame)
        action_grid.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        action_grid.columnconfigure((0, 1), weight=1)

        self.btn_create_shortcut = ttk.Button(action_grid, text=_('lki.preset.btn.configure_autoupdate'),
                                              command=self._open_auto_update_config)
        self.btn_create_shortcut.grid(row=0, column=0, sticky='ew', padx=(0, 3))

        self.btn_select = ttk.Button(action_grid, text=_('lki.preset.btn.save_select'), command=self._select_and_close)
        self.btn_select.grid(row=0, column=1, sticky='ew', padx=(3, 0))
        # --- (修改结束) ---

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
        if lang_code:
            lang_name = self.l10n_id_to_name.get(lang_code, self.l10n_id_to_name.get('en'))
            self.lang_combobox.set(lang_name)
            # 恢复标准语言列表（去掉占位项）和默认颜色
            self.lang_combobox['values'] = list(self.l10n_id_to_name.values())
            self.lang_combobox.configure(foreground='')
        else:
            # 新预设尚未选择语言
            self.lang_combobox.set('')
            # 在 values 中临时插入占位文本
            all_langs = list(self.l10n_id_to_name.values())
            self.lang_combobox['values'] = [_('lki.preset.manager.select_language')] + all_langs
            self.lang_combobox.set(_('lki.preset.manager.select_language'))
            self.lang_combobox.configure(foreground='red')

        self.lang_combobox.config(state='readonly')

        use_ee = preset_data.get('use_ee', False)
        use_mods = preset_data.get('use_mods', False)
        use_fonts = preset_data.get('use_fonts', "")
        use_lk_mods = preset_data.get('use_lk_mods', None)
        self.use_ee_var.set(use_ee)
        self.use_mods_var.set(use_mods)
        self.use_fonts_var.set(use_fonts)
        # 动态重建字体 Combo（根据当前语言添加推荐项）
        lang_code = preset_data.get('lang_code', 'en')
        if not lang_code:
            # 语言未选择时，推荐字体预设为 True（跟随推荐）
            self.use_fonts_var.set(True)
            lang_code = 'en'  # fallback for font list construction
        recommended_font = global_source_manager.get_default_font_id(lang_code)
        font_options = [_('lki.preset.manager.font_opt.none')]
        font_id_map = {"": _('lki.preset.manager.font_opt.none')}
        if recommended_font:
            rec_display_key = FONT_DISPLAY_KEYS.get(recommended_font)
            rec_text = _(rec_display_key) if rec_display_key else recommended_font
        else:
            rec_text = _('lki.preset.manager.font_opt.none')
        recommended_label = _('lki.preset.manager.font_opt.recommended_prefix') + rec_text
        font_options.append(recommended_label)
        font_id_map[True] = recommended_label  # True 哨兵 → 推荐显示文本
        for fid in FONT_IDS:
            display_key = FONT_DISPLAY_KEYS.get(fid, fid)
            display_text = _(display_key)
            font_options.append(display_text)
            font_id_map[fid] = display_text
        self._font_combo['values'] = font_options
        self._font_id_map = font_id_map
        self._display_to_font_id = {v: k for k, v in font_id_map.items()}
        # 设置字体 Combo 选中项（True 也映射到推荐标签）
        display = font_id_map.get(use_fonts, font_id_map.get("", ""))
        self._font_combo.set(display)
        # 动态重建 Combo（跟随全局文本中包含当前全局状态）
        from core import settings as core_settings
        global_val = core_settings.global_settings.get('use_lk_mods', False)
        global_label = _('lki.generic.yes') if global_val else _('lki.generic.no')
        follow_text = _('lki.generic.follow_global') + '：' + global_label
        self._lk_mods_combo.lk_mods_values = [
            (_('lki.generic.yes'), True),
            (_('lki.generic.no'), False),
            (follow_text, None),
        ]
        self._lk_mods_combo['values'] = [v[0] for v in self._lk_mods_combo.lk_mods_values]
        # 设置 Combo 选中项
        for text, val in self._lk_mods_combo.lk_mods_values:
            if val is use_lk_mods or val == use_lk_mods:
                self._lk_mods_combo.set(text)
                break

        self.cb_use_ee.config(state='normal')
        self.cb_use_mods.config(state='normal')

        self.btn_rename.config(state=btn_state)
        self.btn_delete.config(state=btn_state)

        # (新增) 快捷方式按钮始终启用
        self.btn_create_shortcut.config(state='normal')

        self._update_download_mods_btn_state(lang_code)

        if self.mods_dir_tooltip:
            lang_name = self.l10n_id_to_name.get(lang_code, lang_code)
            tooltip_text = _('lki.preset.manager.tooltip_open_mods_dir_lang') % lang_name
            self.mods_dir_tooltip = _('lki.preset.manager.tooltip_open_mods_dir_lang') % lang_name

    def _on_lang_select_changed(self, event=None):
        """当语言下拉框更改时，动态更新下载线路下拉框和推荐字体。"""
        lang_name = self.lang_combobox.get()
        lang_code = self.l10n_name_to_id.get(lang_name)
        if lang_code:
            self.lang_combobox.configure(foreground='')
        self._update_download_mods_btn_state(lang_code)
        if lang_name in self.l10n_name_to_id:
            self.mods_dir_tooltip = _('lki.preset.manager.tooltip_open_mods_dir_lang') % lang_name
        else:
            self.mods_dir_tooltip = _('lki.preset.manager.tooltip_open_mods_dir')
        # 若当前字体选了"推荐"，刷新推荐标签以匹配新语言
        if self._get_font_value() is True:
            rec_font = global_source_manager.get_default_font_id(lang_code) if lang_code else ""
            rec_text = _(FONT_DISPLAY_KEYS.get(rec_font)) if rec_font else _('lki.preset.manager.font_opt.none')
            new_label = _('lki.preset.manager.font_opt.recommended_prefix') + rec_text
            self._font_id_map[True] = new_label
            self._display_to_font_id[new_label] = True
            vals = list(self._font_combo['values'])
            for i, v in enumerate(vals):
                if v.startswith(_('lki.preset.manager.font_opt.recommended_prefix')):
                    vals[i] = new_label
                    break
            self._font_combo['values'] = vals
            self._font_combo.set(new_label)

    # --- (路由相关方法已移除) ---

    def _get_lk_mods_value(self):
        """从 Combo 读取 use_lk_mods 实际值（True/False/None）。"""
        display = self._lk_mods_combo.get()
        for text, val in self._lk_mods_combo.lk_mods_values:
            if text == display:
                return val
        return None

    def _get_font_value(self):
        """从字体 Combo 读取选中的字体 ID，空字符串表示不安装，True 表示推荐。"""
        display = self._font_combo.get()
        val = self._display_to_font_id.get(display, "")
        return val

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

        # 新建预设：语言为空（未选择），字体跟随推荐
        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, "", True, True, True  # lang_code="" 表示未选择
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
        current_use_fonts = self._get_font_value()

        self.active_preset_id = self.instance_manager.add_preset(
            self.instance_id, new_name, current_lang_code, current_use_ee, current_use_mods, current_use_fonts,
            self._get_lk_mods_value()
        )
        self._populate_listbox_and_select()
        if hasattr(self.parent_app, 'on_preset_saved') and self.parent_app.on_preset_saved:
            self.parent_app.on_preset_saved()

    def _save_preset(self, show_popup=True):
        """保存对当前所选预设的更改。返回 True 表示保存成功。"""
        preset_id = self._get_selected_listbox_id()
        if not preset_id:
            return False

        preset_data = self.presets.get(preset_id)
        if not preset_data:
            return False

        is_default = preset_data.get('is_default', False)

        new_lang_name = self.lang_combobox.get()
        new_lang_code = self.l10n_name_to_id.get(new_lang_name)
        if not new_lang_code:
            messagebox.showwarning(_('lki.btn.save_changes'),
                                   _('lki.preset.manager.error.no_language'), parent=self)
            return False
        new_use_ee = self.use_ee_var.get()
        new_use_mods = self.use_mods_var.get()
        new_use_fonts = self._get_font_value()

        data_to_save = {
            "lang_code": new_lang_code,
            "use_ee": new_use_ee,
            "use_mods": new_use_mods,
            "use_fonts": new_use_fonts,
            "use_lk_mods": self._get_lk_mods_value()
        }

        if not is_default:
            data_to_save["name"] = preset_data.get('name')

        self.instance_manager.update_preset_data(self.instance_id, preset_id, data_to_save)
        if hasattr(self.parent_app, 'on_preset_saved') and self.parent_app.on_preset_saved:
            self.parent_app.on_preset_saved()
        if show_popup:
            messagebox.showinfo(_('lki.btn.save_changes'), _('lki.preset.manager.saved'), parent=self)
            self.parent_app.update_content(self.parent_app.current_instance)
        return True

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
        """将列表框中选中的预设保存并应用到实例，并关闭窗口"""
        if not self._save_preset(show_popup=False):
            return  # 保存失败（如语言未选择）则不关闭
        selected_id = self._get_selected_listbox_id()
        if selected_id:
            self.instance_manager.update_instance_data(self.instance_id, {'active_preset_id': selected_id})

        self.on_close_callback()
        self.destroy()

    def _open_mods_folder(self):
        """打开当前实例的 i18n_mods 文件夹"""
        if not self.instance_data:
            return

        lang_name = self.lang_combobox.get()
        if not lang_name:
            return
        lang_code = self.l10n_name_to_id.get(lang_name, 'en')

        mods_path = os.path.join(self.instance_data['path'], 'lki', 'i18n_mods', lang_code)
        os.makedirs(mods_path, exist_ok=True)

        try:
            subprocess.run(['explorer', os.path.normpath(mods_path)])
        except Exception as e:
            log(f"Error opening mods folder: {e}")
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

    # (新增)
    def _open_auto_update_config(self):
        """打开用于创建自动更新快捷方式的对话框。"""
        preset_id = self._get_selected_listbox_id()
        if not preset_id:
            return  # 如果没有选中的预设，则不执行任何操作

        # 我们必须先保存任何待处理的更改，否则快捷方式将使用旧设置创建。
        self._save_preset(show_popup=False)

        instance_name = self.instance_data.get("name", "Game Instance")

        # 检查 pywin32 是否可用
        try:
            import win32com.client
        except ImportError:
            messagebox.showerror(
                _('lki.autoupdate.title'),
                "创建快捷方式需要 'pywin32' 库。请运行 'pip install pywin32' 并重启本程序。",
                parent=self
            )
            return

        # 打开新对话框，传递它所需的信息
        AutoUpdateConfigDialog(self, self.instance_manager, self.instance_id, instance_name, preset_id, self.id_to_name[preset_id])