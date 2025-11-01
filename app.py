import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

import instance_manager
import settings
from game_instance import GameInstance
from localizer import _
from ui.tab_about import AboutTab
from ui.tab_advanced import AdvancedTab
from ui.tab_game import GameTab
from ui.tab_settings import SettingsTab
from ui_manager import IconManager


class LocalizationInstallerApp:
    def __init__(self, master, initial_theme):
        self.master = master
        master.geometry('450x616') # 616 just enough to accommodate 3 instances.
        master.title(_('lki.app.title'))

        self.icons = IconManager()
        self.icons.set_active_theme(initial_theme)

        self.instance_type_keys = ['production', 'pts']
        self.type_id_to_name: Dict[str, str] = {
            code: _(f"lki.game.client_type.{code}") for code in self.instance_type_keys
        }

        self._setup_styles()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        self.tab_game = GameTab(self.notebook, self.icons, self.type_id_to_name, self._on_instance_select)

        self.tab_advanced = AdvancedTab(self.notebook, self.icons, self.type_id_to_name)

        self.tab_settings = SettingsTab(self.notebook, self.icons, self._on_theme_select,
                                        self._on_language_select, self.restart_app)

        self.tab_about = AboutTab(self.notebook)

        self.notebook.add(self.tab_game, text=_('lki.tab.game'))
        self.notebook.add(self.tab_advanced, text=_('lki.tab.advanced'))
        self.notebook.add(self.tab_settings, text=_('lki.tab.settings'))
        self.notebook.add(self.tab_about, text=_('lki.tab.about'))

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._center_main_window()

        self.master.after(100, self.run_initial_detection)

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
        self.style.configure("Hint.TLabel", font=("TkDefaultFont", 9), foreground='gray')
        self.style.configure("danger.TButton", foreground="white", background="#d13438")

        self.style.configure("Link.TButton", foreground=self.select_bg, borderwidth=0, padding=0)
        self.style.map("Link.TButton",
                       foreground=[('active', self.select_bg), ('disabled', 'gray')],
                       underline=[('active', 1)])

        # (新增：安装进度条样式)
        self.style.configure("success.TProgressbar", background="#0078d4")
        self.style.configure("danger.TProgressbar", background="#d13438")

    def _center_main_window(self):
        """计算并将主窗口居中到屏幕上。"""
        try:
            self.master.update_idletasks()  # 强制 Tkinter 计算窗口的实际大小

            screen_width = self.master.winfo_screenwidth()
            screen_height = self.master.winfo_screenheight()

            window_width = self.master.winfo_width()
            window_height = self.master.winfo_height()

            # (如果大小仍为1, 可能是 update_idletasks() 不够, 但我们先尝试)
            if window_width < 100 or window_height < 100:
                print("Warning: Window size not fully calculated, centering may be inaccurate.")

            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            self.master.geometry(f"+{x}+{y}")
        except tk.TclError as e:
            print(f"Error centering main window: {e}")

    def run_initial_detection(self):
        """在启动时*仅一次*触发自动检测。"""
        if not settings.global_settings.get('ever_launched', False):
            print("Running *first time* instance import...")

            self.tab_game._on_auto_import(is_initial_run=True)

            settings.global_settings.set('ever_launched', True)
        else:
            print("Skipping initial instance import (not first launch).")

    def _on_language_select(self):
        """由 SettingsTab 调用的回调。"""
        messagebox.showinfo(
            _('lki.app.title'),
            _('lki.settings.language.restart_required')
        )

    def _on_theme_select(self, selected_theme: str):
        """由 SettingsTab 调用的回调。"""
        self.master.call('set_theme', selected_theme)

        self._setup_styles()

        self.icons.set_active_theme(selected_theme)
        self._update_all_icons()

    def _update_all_icons(self):
        """通知所有选项卡更新其图标"""
        self.tab_game.update_icons()
        self.tab_advanced.update_icons()
        self.tab_settings.update_icons()

    def _on_instance_select(self, instance: Optional[GameInstance]):
        """
        由 GameTab 调用的回调。
        通知 AdvancedTab 更新其内容。
        """
        self.tab_advanced.update_content(instance)

    def _on_tab_changed(self, event):
        """
        当用户点击 Notebook 选项卡时。
        确保 AdvancedTab 的内容在变为可见时是最新的。
        """
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1:
            current_instance = self.tab_game.get_selected_game_instance()
            self.tab_advanced.update_content(current_instance)

    def restart_app(self):
        """保存所有内容并重启应用程序。"""
        print("Restarting application...")

        try:
            settings.global_settings.save()
            instance_manager.global_instance_manager.save()
        except Exception as e:
            print(f"Error saving settings on restart: {e}")

        try:
            os.execl(sys.executable, *([sys.executable] + sys.argv))
        except Exception as e:
            print(f"Failed to restart: {e}")
            messagebox.showerror(_('lki.restart.title'), f"Failed to restart: {e}")