import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

import settings
import utils
from localizer import _, get_available_languages
from settings import GlobalSettings
import instance_manager

from ui_manager import IconManager
from ui_windows import ProxyConfigWindow, PresetManagerWindow
from localization_sources import global_source_manager
from game_instance import GameInstance, GameVersion


class LocalizationInstallerApp:
    def __init__(self, master, initial_theme):
        self.master = master
        master.title(_('lki.app.title'))

        self.instance_manager = instance_manager.global_instance_manager
        self.game_instances = self.instance_manager.get_all()
        self.selected_instance_id = None
        self.selected_client_widget = None

        self.client_check_vars = []
        self.select_all_var = tk.BooleanVar()

        self.icons = IconManager()
        self.icons.set_active_theme(initial_theme)

        self.theme_var = tk.StringVar(value=settings.global_settings.get('theme', 'light'))

        self.available_ui_langs = get_available_languages()
        self.ui_lang_name_to_code = {v: k for k, v in self.available_ui_langs.items()}
        current_locale = settings.global_settings.language
        self.current_lang_name = self.available_ui_langs.get(current_locale,
                                                             self.available_ui_langs.get('en', 'English'))

        self.proxy_status_text = self._get_proxy_status_text()

        self.instance_type_keys = ['production', 'pts']
        self.type_id_to_name = {
            code: _(f"lki.game.client_type.{code}") for code in self.instance_type_keys
        }
        self.type_name_to_id = {name: code for code, name in self.type_id_to_name.items()}

        self.preset_id_to_display_name = {}
        self.display_name_to_preset_id = {}

        self._setup_styles()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        self.tab_game = ttk.Frame(self.notebook, padding='10 10 10 10')
        self.tab_advanced = ttk.Frame(self.notebook, padding='10 10 10 10')
        self.tab_settings = ttk.Frame(self.notebook, padding='10 10 10 10')
        self.tab_about = ttk.Frame(self.notebook, padding='10 10 10 10')

        self.notebook.add(self.tab_game, text=_('lki.tab.game'))
        self.notebook.add(self.tab_advanced, text=_('lki.tab.advanced'))
        self.notebook.add(self.tab_settings, text=_('lki.tab.settings'))
        self.notebook.add(self.tab_about, text=_('lki.tab.about'))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._create_game_tab_widgets()

        self.advanced_tab_placeholder = ttk.Label(
            self.tab_advanced,
            text=_('lki.advanced.please_select'),
            wraplength=320
        )
        self.advanced_tab_placeholder.pack(pady=20, padx=20, fill='x')

        self.advanced_tab_frame = ttk.Frame(self.tab_advanced, padding=10)

        self._create_settings_tab_widgets()

        self.label_about = ttk.Label(self.tab_about, text='About tab')
        self.label_about.pack(pady=20, padx=20)

    def _build_preset_maps(self):
        """从 *当前选定的实例* 加载预设并构建查找字典"""
        if not self.selected_instance_id:
            self.preset_id_to_display_name = {}
            self.display_name_to_preset_id = {}
            return

        instance = self.instance_manager.get_instance(self.selected_instance_id)
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

    def _setup_styles(self):
        """定义自定义字体和样式"""
        self.style = ttk.Style()
        self.select_bg = "#0078d4"
        self.select_fg = "white"
        self.style.configure("Client.TLabel", font=("TkDefaultFont", 12, "bold"))
        self.style.configure("Path.TLabel", font=("TkDefaultFont", 9))
        self.style.configure("Selected.TFrame", background=self.select_bg)
        self.style.configure("Selected.Client.TLabel", font=("TkDefaultFont", 12, "bold"), background=self.select_bg,
                             foreground=self.select_fg)
        self.style.configure("Selected.Path.TLabel", font=("TkDefaultFont", 9), background=self.select_bg,
                             foreground=self.select_fg)

    def _create_settings_tab_widgets(self):
        """创建“设置”选项卡中的所有小部件"""

        self.tab_settings.columnconfigure(1, weight=1)

        # --- 1. 语言设置 ---
        lang_label = ttk.Label(self.tab_settings, text=_('lki.settings.language'))
        lang_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        lang_frame = ttk.Frame(self.tab_settings)
        lang_frame.grid(row=0, column=1, sticky='we', pady=10)

        self.lang_combobox = ttk.Combobox(lang_frame, values=list(self.available_ui_langs.values()), state='readonly')
        self.lang_combobox.set(self.current_lang_name)
        self.lang_combobox.pack(side='left', fill='x', expand=True)

        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_language_select)

        self.lang_restart_label = ttk.Label(self.tab_settings, text="", foreground='gray')
        self.lang_restart_label.grid(row=1, column=1, sticky='w', padx=5, pady=(0, 10))

        # --- 2. 主题设置 (拆分为多行) ---
        theme_label = ttk.Label(self.tab_settings, text=_('lki.settings.theme'))
        theme_label.grid(row=2, column=0, sticky='e', padx=(0, 10), pady=(10, 0))

        rb_light = ttk.Radiobutton(self.tab_settings, text=_('lki.settings.theme.light'), variable=self.theme_var,
                                   value='light', command=self._on_theme_select)
        rb_light.grid(row=2, column=1, sticky='w', pady=(10, 0))

        rb_dark = ttk.Radiobutton(self.tab_settings, text=_('lki.settings.theme.dark'), variable=self.theme_var,
                                  value='dark', command=self._on_theme_select)
        rb_dark.grid(row=3, column=1, sticky='w', pady=(0, 10))

        # --- 3. 代理设置 ---
        proxy_label = ttk.Label(self.tab_settings, text=_('lki.settings.proxy'))
        proxy_label.grid(row=4, column=0, sticky='e', padx=(0, 10), pady=10)

        proxy_frame = ttk.Frame(self.tab_settings)
        proxy_frame.grid(row=4, column=1, sticky='we', pady=10)
        proxy_frame.columnconfigure(0, weight=1)

        self.proxy_status_label = ttk.Label(proxy_frame, text=self.proxy_status_text)
        self.proxy_status_label.grid(row=0, column=0, sticky='w', padx=5)

        self.proxy_config_btn = ttk.Button(proxy_frame, text=_('lki.btn.configure'), command=self._open_proxy_window)
        self.proxy_config_btn.grid(row=0, column=1, sticky='e')

    def _create_game_tab_widgets(self):
        """创建“游戏”选项卡中的所有小部件"""
        top_frame = ttk.Frame(self.tab_game, padding=(5, 0))
        top_frame.pack(fill='x', side='top', pady=(0, 10))
        buttons_frame = ttk.Frame(top_frame)
        buttons_frame.pack(side='right', anchor='e')
        self.check_all_btn = ttk.Checkbutton(top_frame, variable=self.select_all_var, command=self._on_select_all)
        self.check_all_btn.pack(side='left', padx=(0, 10), anchor='center')
        title_label = ttk.Label(top_frame, text=_('lki.game.detected_clients'), style="Client.TLabel")
        title_label.pack(side='left', anchor='w')

        self.btn_add = ttk.Button(buttons_frame, image=self.icons.add, style="Toolbutton")
        self.btn_add.pack(side='left', padx=(0, 2))
        self.btn_rename = ttk.Button(buttons_frame, image=self.icons.rename, style="Toolbutton")
        self.btn_rename.pack(side='left', padx=2)
        self.btn_remove = ttk.Button(buttons_frame, image=self.icons.remove, style="Toolbutton")
        self.btn_remove.pack(side='left', padx=2)
        self.btn_detect = ttk.Button(buttons_frame, image=self.icons.detect, style="Toolbutton")
        self.btn_detect.pack(side='left', padx=(2, 0))

        list_container = ttk.Frame(self.tab_game)
        list_container.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(list_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.client_list_frame = ttk.Frame(self.canvas)
        self.client_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.client_list_window = self.canvas.create_window((0, 0), window=self.client_list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill='both', expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.client_list_frame)

        bottom_frame = ttk.Frame(self.tab_game)
        bottom_frame.pack(fill='x', side='bottom', pady=(10, 0))
        self.btn_install_selected = ttk.Button(bottom_frame, text=_('lki.game.btn.install_selected'))
        self.btn_install_selected.pack(fill='x', expand=True)

        self._load_and_display_instances()

    def _on_language_select(self, event=None):
        selected_name = self.lang_combobox.get()
        selected_code = self.ui_lang_name_to_code.get(selected_name)

        if selected_code and selected_code != settings.global_settings.language:
            settings.global_settings.language = selected_code
            self.lang_restart_label.config(text=_('lki.settings.language.restart_required'))
            messagebox.showinfo(
                _('lki.app.title'),
                _('lki.settings.language.restart_required')
            )

    def _on_theme_select(self):
        selected_theme = self.theme_var.get()
        settings.global_settings.set('theme', selected_theme)

        self.master.call('set_theme', selected_theme)

        self.icons.set_active_theme(selected_theme)
        self._update_all_icons()

    def _update_all_icons(self):
        self.btn_add.config(image=self.icons.add)
        self.btn_rename.config(image=self.icons.rename)
        self.btn_remove.config(image=self.icons.remove)
        self.btn_detect.config(image=self.icons.detect)
        if hasattr(self, 'manage_preset_btn'):
            self.manage_preset_btn.config(image=self.icons.manage)

    def _get_proxy_status_text(self):
        proxy_mode = settings.global_settings.get('proxy.mode', 'disabled')
        key_map = {
            'disabled': 'lki.settings.proxy.disabled',
            'system': 'lki.settings.proxy.system',
            'manual': 'lki.settings.proxy.manual',
        }
        return _(key_map.get(proxy_mode, 'lki.settings.proxy.disabled'))

    def _open_proxy_window(self):
        window = ProxyConfigWindow(self.master, self._on_proxy_config_saved)

    def _on_proxy_config_saved(self):
        self.proxy_status_label.config(text=self._get_proxy_status_text())

    def _load_and_display_instances(self):
        """从管理器加载实例并显示它们"""

        if not self.game_instances:
            print("instances.json 为空，正在从 dummy_clients 填充...")
            dummy_clients = [
                ('production', "C:/Games/Korabli"),
                ('pts', "D:/Games/WoWS_Public_Test"),
                ('production', "E:/SteamLibrary/steamapps/common/World of Warships"),
            ]

            current_ui_lang = settings.global_settings.language

            for type_code, path in dummy_clients:
                name = _(f"lki.game.client_type.{type_code}")
                self.instance_manager.add_instance(name, path, type_code, current_ui_lang)

            self.game_instances = self.instance_manager.get_all()

        loaded_instances: List[GameInstance] = []
        for instance_id, data in self.game_instances.items():
            try:
                instance = GameInstance(
                    instance_id=instance_id,
                    path=Path(data['path']),
                    name=data['name'],
                    type=data['type']
                )
                loaded_instances.append(instance)
            except Exception as e:
                print(f"Error loading game instance {data['path']}: {e}")

        loaded_instances.sort(key=lambda inst: inst.name)

        for instance in loaded_instances:
            self._add_client_entry(instance)

    # --- (已修改：显示两个版本并使用翻译键) ---
    def _add_client_entry(self, instance: GameInstance):
        """向可滚动框架中添加一个客户端条目"""

        item_frame = ttk.Frame(self.client_list_frame, padding=(5, 5), style="TFrame")
        item_frame.pack(fill='x', expand=True)

        check_var = tk.BooleanVar()
        checkbutton = ttk.Checkbutton(item_frame, variable=check_var, command=self._update_select_all_state)
        checkbutton.pack(side='left', padx=(0, 10), anchor='center')

        item_frame.check_var = check_var
        self.client_check_vars.append(check_var)

        text_frame = ttk.Frame(item_frame, style="TFrame")
        text_frame.pack(side='left', fill='x', expand=True)

        # 1. 实例类型 (e.g., "Mir Korabley Live")
        type_key = f"lki.game.client_type.{instance.type}"
        type_text = _(type_key)

        type_label = ttk.Label(text_frame, text=type_text, style="Client.TLabel")
        type_label.pack(anchor='w', fill='x')

        # 2. 实例路径
        path_label = ttk.Label(text_frame, text=str(instance.path), style="Path.TLabel", wraplength=500)
        path_label.pack(anchor='w', fill='x')

        # 3. 游戏版本和本地化状态
        # (已修改) 显示最多两个版本
        versions_to_display = instance.versions[:2]  # Get the top two versions

        def on_click(event, frame=item_frame, id=instance.instance_id):
            self._on_client_select(frame, id)

        # (已修改) 绑定所有标签
        text_frame.bind("<Button-1>", on_click)
        type_label.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)

        self._bind_mousewheel(item_frame)
        self._bind_mousewheel(checkbutton)
        self._bind_mousewheel(text_frame)
        self._bind_mousewheel(type_label)
        self._bind_mousewheel(path_label)

        if not versions_to_display:
            status_text = _('lki.game.version_not_found')
            status_label = ttk.Label(text_frame, text=status_text, style="Path.TLabel")
            status_label.pack(anchor='w', fill='x')
            status_label.bind("<Button-1>", on_click)
            self._bind_mousewheel(status_label)
        else:
            for game_version in versions_to_display:
                ver_str = game_version.exe_version or _('lki.game.version_unknown')
                status_text = f"{_('lki.game.version_label')} {ver_str} ({_('lki.game.folder_label')} {game_version.bin_folder_name})"

                if game_version.l10n_info:
                    l10n_ver = game_version.l10n_info.version
                    if game_version.verify_files(instance.path):
                        l10n_status = _('lki.game.l10n_status.ok')
                    else:
                        l10n_status = _('lki.game.l10n_status.corrupted')
                    status_text += f" ({_('lki.game.l10n_label')} {l10n_ver} - {l10n_status})"
                else:
                    status_text += f" ({_('lki.game.l10n_status.not_installed')})"

                status_label = ttk.Label(text_frame, text=status_text, style="Path.TLabel")
                status_label.pack(anchor='w', fill='x')
                status_label.bind("<Button-1>", on_click)
                self._bind_mousewheel(status_label)

        item_frame.type_label = type_label
        item_frame.path_label = path_label
        item_frame.text_frame = text_frame

        separator = ttk.Separator(self.client_list_frame, orient='horizontal')
        separator.pack(fill='x', expand=True, padx=5, pady=2)

    # --- (已修改：通用高亮) ---
    def _on_client_select(self, selected_frame, selected_id):
        """处理客户端条目的点击（选择）事件"""

        if self.selected_client_widget and self.selected_client_widget != selected_frame:
            self.selected_client_widget.text_frame.config(style="TFrame")
            # 循环所有子标签
            for child in self.selected_client_widget.text_frame.winfo_children():
                if isinstance(child, ttk.Label):
                    if child == self.selected_client_widget.type_label:
                        child.config(style="Client.TLabel")
                    else:
                        child.config(style="Path.TLabel")  # 路径和状态标签

        selected_frame.text_frame.config(style="Selected.TFrame")
        # 循环所有子标签
        for child in selected_frame.text_frame.winfo_children():
            if isinstance(child, ttk.Label):
                if child == selected_frame.type_label:
                    child.config(style="Selected.Client.TLabel")
                else:
                    child.config(style="Selected.Path.TLabel")  # 路径和状态标签

        self.selected_client_widget = selected_frame
        self.selected_instance_id = selected_id

        print(f"Selected instance ID: {self.selected_instance_id}")

        self._update_advanced_tab()

    def _on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1:
            self._build_preset_maps()
            self._update_advanced_tab()

    def _update_advanced_tab(self):
        """根据当前选择显示占位符或实例设置"""

        for widget in self.advanced_tab_frame.winfo_children():
            widget.destroy()

        if self.selected_instance_id:
            self._build_preset_maps()
            self.advanced_tab_placeholder.pack_forget()
            self._build_advanced_widgets()
            self.advanced_tab_frame.pack(fill='both', expand=True, anchor='n')
        else:
            self.advanced_tab_frame.pack_forget()
            self.advanced_tab_placeholder.pack(pady=20, padx=20, fill='x')

    def _build_advanced_widgets(self):
        """在 advanced_tab_frame 中创建实际的控件"""

        instance_data = self.instance_manager.get_instance(self.selected_instance_id)
        if not instance_data:
            return

        self.advanced_tab_frame.columnconfigure(1, weight=1)

        # --- Row 0: 实例名称 ---
        type_key = f"lki.game.client_type.{instance_data.get('type', 'production')}"
        name = _(type_key)
        name_label = ttk.Label(self.advanced_tab_frame, text=name, style="Client.TLabel")
        name_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 20))

        # --- Row 1: Instance Type (调换位置) ---
        type_label = ttk.Label(self.advanced_tab_frame, text=_('lki.advanced.instance_type_label'))
        type_label.grid(row=1, column=0, sticky='e', padx=(0, 10), pady=10)

        type_frame = ttk.Frame(self.advanced_tab_frame)
        type_frame.grid(row=1, column=1, sticky='we', pady=10)
        type_frame.columnconfigure(0, weight=1)

        self.type_combobox = ttk.Combobox(type_frame, values=list(self.type_id_to_name.values()), state='readonly')
        self.type_combobox.grid(row=0, column=0, sticky='we')

        current_type_code = instance_data.get('type', 'production')
        current_type_name = self.type_id_to_name.get(current_type_code, _('lki.game.client_type.production'))
        self.type_combobox.set(current_type_name)

        self.type_combobox.bind("<<ComboboxSelected>>", self._on_instance_type_select)

        # --- Row 2: Preset (调换位置) ---
        preset_label = ttk.Label(self.advanced_tab_frame, text=_('lki.advanced.preset_label'))
        preset_label.grid(row=2, column=0, sticky='e', padx=(0, 10), pady=10)

        preset_frame = ttk.Frame(self.advanced_tab_frame)
        preset_frame.grid(row=2, column=1, sticky='we', pady=10)
        preset_frame.columnconfigure(0, weight=1)

        self.preset_combobox = ttk.Combobox(preset_frame, values=list(self.preset_id_to_display_name.values()),
                                            state='readonly')
        self.preset_combobox.grid(row=0, column=0, sticky='we')

        self._update_preset_combobox()

        self.preset_combobox.bind("<<ComboboxSelected>>", self._on_preset_select)

        self.manage_preset_btn = ttk.Button(
            preset_frame,
            image=self.icons.manage,
            style="Toolbutton",
            command=self._open_preset_manager
        )
        self.manage_preset_btn.grid(row=0, column=1, sticky='e', padx=(5, 0))

    def _update_preset_combobox(self):
        """（重新）填充预设下拉框并设置当前值"""
        self.preset_combobox.config(values=list(self.preset_id_to_display_name.values()))

        instance = self.instance_manager.get_instance(self.selected_instance_id)
        current_preset_id = instance.get('active_preset_id', 'default')
        current_preset_name = self.preset_id_to_display_name.get(current_preset_id, _('lki.preset.default.name'))
        self.preset_combobox.set(current_preset_name)

    def _on_preset_select(self, event=None):
        """当“高级”选项卡中的预设被更改时调用"""
        selected_name = self.preset_combobox.get()
        selected_id = self.display_name_to_preset_id.get(selected_name, 'default')

        if selected_id and self.selected_instance_id:
            print(f"Updating instance {self.selected_instance_id} active preset to {selected_id}")
            self.instance_manager.update_instance_data(
                self.selected_instance_id,
                {'active_preset_id': selected_id}
            )

    def _on_instance_type_select(self, event=None):
        """当实例类型下拉框被更改时调用"""
        selected_name = self.type_combobox.get()
        selected_code = self.type_name_to_id.get(selected_name)

        if not selected_code or not self.selected_instance_id:
            return

        instance = self.instance_manager.get_instance(self.selected_instance_id)
        current_code = instance.get('type', 'production')

        if selected_code == current_code:
            return

        confirm_text = _('lki.advanced.confirm_type_change') % (selected_name)
        if messagebox.askyesno(_('lki.app.title'), confirm_text, parent=self.advanced_tab_frame):
            print(f"Updating instance {self.selected_instance_id} type to {selected_code}")
            self.instance_manager.update_instance_data(
                self.selected_instance_id,
                {'type': selected_code}
            )
        else:
            current_name = self.type_id_to_name.get(current_code)
            self.type_combobox.set(current_name)

    def _open_preset_manager(self):
        """打开预设管理器窗口"""
        if not self.selected_instance_id:
            return

        window = PresetManagerWindow(self.master, self.selected_instance_id, self._on_preset_manager_close)

    def _on_preset_manager_close(self):
        """当预设管理器关闭时，由其调用的回调函数"""
        print("Preset manager closed. Refreshing preset combobox.")
        self._build_preset_maps()
        self._update_preset_combobox()

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.client_list_window, width=canvas_width)

    def _on_select_all(self):
        if 'alternate' in self.check_all_btn.state():
            new_state = True
            self.select_all_var.set(True)
        else:
            new_state = self.select_all_var.get()
        self.check_all_btn.state(['!alternate'])
        for var in self.client_check_vars:
            var.set(new_state)

    def _update_select_all_state(self):
        if not self.client_check_vars:
            return
        states = [var.get() for var in self.client_check_vars]
        if all(states):
            self.select_all_var.set(True)
            self.check_all_btn.state(['!alternate'])
        elif not any(states):
            self.select_all_var.set(False)
            self.check_all_btn.state(['!alternate'])
        else:
            self.select_all_var.set(False)
            self.check_all_btn.state(['alternate'])

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)