import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import settings
import utils
from localizer import _, get_available_languages
from settings import GlobalSettings
import instance_manager

# --- (新导入) ---
from ui_manager import IconManager
from ui_windows import ProxyConfigWindow, PresetManagerWindow


# ---

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

        self.available_langs = get_available_languages()
        self.lang_name_to_code = {v: k for k, v in self.available_langs.items()}
        current_locale = settings.global_settings.language
        self.current_lang_name = self.available_langs.get(current_locale, self.available_langs.get('en', 'English'))

        self.proxy_status_text = self._get_proxy_status_text()

        self._build_preset_maps()

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
        """从 settings.json 加载预设并构建查找字典"""
        presets_dict = settings.global_settings.get('presets', {})

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

        self.lang_combobox = ttk.Combobox(lang_frame, values=list(self.available_langs.values()), state='readonly')
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

        self.proxy_config_btn = ttk.Button(proxy_frame, text=_('lki.settings.proxy.configure'),
                                           command=self._open_proxy_window)
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
        selected_code = self.lang_name_to_code.get(selected_name)

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

            default_preset_id = "default"

            for type_code, path in dummy_clients:
                name = _(f"lki.game.client_type.{type_code}")
                self.instance_manager.add_instance(name, path, type_code, default_preset_id)

            self.game_instances = self.instance_manager.get_all()

        sorted_instances = sorted(self.game_instances.items(), key=lambda item: item[1]['name'])

        for instance_id, instance_data in sorted_instances:
            self._add_client_entry(instance_id, instance_data)

    def _add_client_entry(self, instance_id, instance_data):
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

        type_key = f"lki.game.client_type.{instance_data.get('type', 'production')}"
        type_text = _(type_key)

        type_label = ttk.Label(text_frame, text=type_text, style="Client.TLabel")
        type_label.pack(anchor='w', fill='x')

        path_label = ttk.Label(text_frame, text=instance_data['path'], style="Path.TLabel", wraplength=500)
        path_label.pack(anchor='w', fill='x')

        item_frame.type_label = type_label
        item_frame.path_label = path_label
        item_frame.text_frame = text_frame

        def on_click(event, frame=item_frame, id=instance_id):
            self._on_client_select(frame, id)

        text_frame.bind("<Button-1>", on_click)
        type_label.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)

        separator = ttk.Separator(self.client_list_frame, orient='horizontal')
        separator.pack(fill='x', expand=True, padx=5, pady=2)

        self._bind_mousewheel(item_frame)
        self._bind_mousewheel(checkbutton)
        self._bind_mousewheel(text_frame)
        self._bind_mousewheel(type_label)
        self._bind_mousewheel(path_label)

    def _on_client_select(self, selected_frame, selected_id):
        """处理客户端条目的点击（选择）事件"""

        if self.selected_client_widget and self.selected_client_widget != selected_frame:
            self.selected_client_widget.text_frame.config(style="TFrame")
            self.selected_client_widget.type_label.config(style="Client.TLabel")
            self.selected_client_widget.path_label.config(style="Path.TLabel")

        selected_frame.text_frame.config(style="Selected.TFrame")
        selected_frame.type_label.config(style="Selected.Client.TLabel")
        selected_frame.path_label.config(style="Selected.Path.TLabel")

        self.selected_client_widget = selected_frame
        self.selected_instance_id = selected_id

        print(f"Selected instance ID: {self.selected_instance_id}")

        self._update_advanced_tab()

    def _on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1:
            self._update_advanced_tab()

    def _update_advanced_tab(self):
        """根据当前选择显示占位符或实例设置"""

        for widget in self.advanced_tab_frame.winfo_children():
            widget.destroy()

        if self.selected_instance_id:
            self.advanced_tab_placeholder.pack_forget()
            self._build_advanced_widgets()
            self.advanced_tab_frame.pack(fill='x', expand=True, anchor='n')
        else:
            self.advanced_tab_frame.pack_forget()
            self.advanced_tab_placeholder.pack(pady=20, padx=20, fill='x')

    def _build_advanced_widgets(self):
        """在 advanced_tab_frame 中创建实际的控件"""

        instance = self.instance_manager.get_instance(self.selected_instance_id)
        if not instance:
            return

        self.advanced_tab_frame.columnconfigure(1, weight=1)

        # 1. 预设标签
        preset_label = ttk.Label(self.advanced_tab_frame, text=_('lki.advanced.preset_label'))
        preset_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        # 2. 预设下拉框
        preset_frame = ttk.Frame(self.advanced_tab_frame)
        preset_frame.grid(row=0, column=1, sticky='we', pady=10)
        preset_frame.columnconfigure(0, weight=1)

        self.preset_combobox = ttk.Combobox(preset_frame, values=list(self.preset_id_to_display_name.values()),
                                            state='readonly')
        self.preset_combobox.grid(row=0, column=0, sticky='we')

        # 3. 设置下拉框的当前值
        self._update_preset_combobox()

        # 4. 绑定保存事件
        self.preset_combobox.bind("<<ComboboxSelected>>", self._on_preset_select)

        # 5. 管理(齿轮)按钮
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
        current_preset_id = instance.get('preset', 'default')
        current_preset_name = self.preset_id_to_display_name.get(current_preset_id, _('lki.preset.default.name'))
        self.preset_combobox.set(current_preset_name)

    def _on_preset_select(self, event=None):
        """当“高级”选项卡中的预设被更改时调用"""
        selected_name = self.preset_combobox.get()
        selected_id = self.display_name_to_preset_id.get(selected_name, 'default')

        if selected_id and self.selected_instance_id:
            print(f"Updating instance {self.selected_instance_id} preset to {selected_id}")
            self.instance_manager.update_instance(
                self.selected_instance_id,
                {'preset': selected_id}
            )

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