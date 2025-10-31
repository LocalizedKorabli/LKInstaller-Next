import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

import settings
from localizer import _, get_available_languages
from ui_manager import IconManager

# --- (新导入) ---
from ui.tab_game import GameTab
from ui.tab_advanced import AdvancedTab
from ui.tab_settings import SettingsTab
from ui.tab_about import AboutTab


# --- (新导入结束) ---


class LocalizationInstallerApp:
    def __init__(self, master, initial_theme):
        self.master = master
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

        # --- (已修改：实例化选项卡) ---
        self.tab_game = GameTab(self.notebook, self.icons, self.type_id_to_name, self._on_instance_select)

        # (已修改：移除了 _on_instance_type_changed 回调)
        self.tab_advanced = AdvancedTab(self.notebook, self.icons, self.type_id_to_name)

        self.tab_settings = SettingsTab(self.notebook, self.icons, self._on_theme_select,
                                        self._on_language_select)

        self.tab_about = AboutTab(self.notebook)

        self.notebook.add(self.tab_game, text=_('lki.tab.game'))
        self.notebook.add(self.tab_advanced, text=_('lki.tab.advanced'))
        self.notebook.add(self.tab_settings, text=_('lki.tab.settings'))
        self.notebook.add(self.tab_about, text=_('lki.tab.about'))

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        # --- (修改结束) ---

        # --- (初始检测逻辑现在位于 tab_game.py 的 __init__ 中) ---

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

    # --- (新/修改：回调和协调器) ---

    def _on_language_select(self):
        """由 SettingsTab 调用的回调。"""
        messagebox.showinfo(
            _('lki.app.title'),
            _('lki.settings.language.restart_required')
        )

    def _on_theme_select(self, selected_theme: str):
        """由 SettingsTab 调用的回调。"""
        self.master.call('set_theme', selected_theme)
        self.icons.set_active_theme(selected_theme)
        self._update_all_icons()

    def _update_all_icons(self):
        """通知所有选项卡更新其图标"""
        self.tab_game.update_icons()
        self.tab_advanced.update_icons()
        self.tab_settings.update_icons()
        # self.tab_about.update_icons() ...

    def _on_instance_select(self, instance_id: Optional[str]):
        """
        由 GameTab 调用的回调。
        通知 AdvancedTab 更新其内容。
        """
        self.tab_advanced.update_content(instance_id)

    # --- (已移除：_on_instance_type_changed) ---

    def _on_tab_changed(self, event):
        """
        当用户点击 Notebook 选项卡时。
        确保 AdvancedTab 的内容在变为可见时是最新的。
        """
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1:
            # （GameTab 维护自己的状态，所以我们可以直接从它那里获取）
            current_id = self.tab_game.selected_instance_id
            self.tab_advanced.update_content(current_id)