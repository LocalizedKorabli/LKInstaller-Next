import tkinter as tk
from tkinter import ttk, messagebox

import settings
from localizer import _, get_available_languages


class SettingsTab(ttk.Frame):
    """
    “设置”选项卡 UI。
    """

    def __init__(self, master, icons, on_theme_change_callback, on_language_change_callback):
        super().__init__(master, padding='10 10 10 10')

        self.icons = icons
        self.on_theme_change_callback = on_theme_change_callback
        self.on_language_change_callback = on_language_change_callback

        self.theme_var = tk.StringVar(value=settings.global_settings.get('theme', 'light'))

        self.available_ui_langs = get_available_languages()
        self.ui_lang_name_to_code = {v: k for k, v in self.available_ui_langs.items()}
        current_locale = settings.global_settings.language
        self.current_lang_name = self.available_ui_langs.get(current_locale,
                                                             self.available_ui_langs.get('en', 'English'))

        self.proxy_status_text = self._get_proxy_status_text()

        self._create_settings_tab_widgets()

    def _create_settings_tab_widgets(self):
        """创建“设置”选项卡中的所有小部件"""

        self.columnconfigure(1, weight=1)

        lang_label = ttk.Label(self, text=_('lki.settings.language'))
        lang_label.grid(row=0, column=0, sticky='e', padx=(0, 10), pady=10)

        lang_frame = ttk.Frame(self)
        lang_frame.grid(row=0, column=1, sticky='we', pady=10)

        self.lang_combobox = ttk.Combobox(lang_frame, values=list(self.available_ui_langs.values()), state='readonly')
        self.lang_combobox.set(self.current_lang_name)
        self.lang_combobox.pack(side='left', fill='x', expand=True)

        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_language_select)

        self.lang_restart_label = ttk.Label(self, text="", foreground='gray')
        self.lang_restart_label.grid(row=1, column=1, sticky='w', padx=5, pady=(0, 10))

        theme_label = ttk.Label(self, text=_('lki.settings.theme'))
        theme_label.grid(row=2, column=0, sticky='e', padx=(0, 10), pady=(10, 0))

        rb_light = ttk.Radiobutton(self, text=_('lki.settings.theme.light'), variable=self.theme_var,
                                   value='light', command=self._on_theme_select)
        rb_light.grid(row=2, column=1, sticky='w', pady=(10, 0))

        rb_dark = ttk.Radiobutton(self, text=_('lki.settings.theme.dark'), variable=self.theme_var,
                                  value='dark', command=self._on_theme_select)
        rb_dark.grid(row=3, column=1, sticky='w', pady=(0, 10))

        proxy_label = ttk.Label(self, text=_('lki.settings.proxy'))
        proxy_label.grid(row=4, column=0, sticky='e', padx=(0, 10), pady=10)

        proxy_frame = ttk.Frame(self)
        proxy_frame.grid(row=4, column=1, sticky='we', pady=10)
        proxy_frame.columnconfigure(0, weight=1)

        self.proxy_status_label = ttk.Label(proxy_frame, text=self.proxy_status_text)
        self.proxy_status_label.grid(row=0, column=0, sticky='w', padx=5)

        self.proxy_config_btn = ttk.Button(proxy_frame, text=_('lki.btn.configure'), command=self._open_proxy_window)
        self.proxy_config_btn.grid(row=0, column=1, sticky='e')

    def _on_language_select(self, event=None):
        selected_name = self.lang_combobox.get()
        selected_code = self.ui_lang_name_to_code.get(selected_name)

        if selected_code and selected_code != settings.global_settings.language:
            settings.global_settings.language = selected_code
            self.lang_restart_label.config(text=_('lki.settings.language.restart_required'))
            self.on_language_change_callback()

    def _on_theme_select(self):
        selected_theme = self.theme_var.get()
        settings.global_settings.set('theme', selected_theme)
        self.on_theme_change_callback(selected_theme)

    def _get_proxy_status_text(self):
        proxy_mode = settings.global_settings.get('proxy.mode', 'disabled')
        key_map = {
            'disabled': 'lki.settings.proxy.disabled',
            'system': 'lki.settings.proxy.system',
            'manual': 'lki.settings.proxy.manual',
        }
        return _(key_map.get(proxy_mode, 'lki.settings.proxy.disabled'))

    def _open_proxy_window(self):
        # self.master.master 是 Notebook 的父级，即 tk.Tk()
        window = ProxyConfigWindow(self.master.master, self._on_proxy_config_saved)

    def _on_proxy_config_saved(self):
        self.proxy_status_label.config(text=self._get_proxy_status_text())

    def update_icons(self):
        """当主题更改时更新此选项卡上的图标（如果需要）"""
        # self.proxy_config_btn 上的图标？目前没有
        pass


class ProxyConfigWindow(tk.Toplevel):
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