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
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from core import settings
from core import utils
from instance import instance_manager
from instance.game_instance import GameInstance
from core.localizer import _, global_translator
from core.logger import log
from ui.tabs.tab_about import AboutTab
from ui.tabs.tab_advanced import AdvancedTab
from ui.tabs.tab_game import GameTab
from ui.tabs.tab_settings import SettingsTab
from ui.ui_manager import get_icon_manager


class LocalizationInstallerApp:
    def __init__(self, master, initial_theme, font_family: str, scaling_factor=1.0):  # (scaling_factor is passed in)
        self.master = master
        self.master.scaling_factor = scaling_factor  # (新增) 附加到根窗口
        self.font_family = font_family
        # (修改) 步骤 4: 缩放窗口大小
        base_width = 350
        try:
            base_height = int(_('lki.app.data.height'))
        except ValueError:
            base_height = 497
        # (修改) 使用新的 scale_dpi 函数
        scaled_width = utils.scale_dpi(self.master, base_width)
        scaled_height = utils.scale_dpi(self.master, base_height)
        # master.geometry(f'{scaled_width}x{scaled_height}')
        master.geometry(f'{max(int(base_width * 1.5), scaled_width)}x{max(int(base_height * 1.5), scaled_height)}')

        master.title(_('lki.app.title'))

        self.icons = get_icon_manager()
        self.icons.set_active_theme(initial_theme)

        self.instance_type_keys = ['production', 'pts']
        self.type_id_to_name: Dict[str, str] = {
            code: _(f"lki.game.client_type.{code}") for code in self.instance_type_keys
        }

        self._setup_styles(initial_theme == 'dark', font_family)

        # ── 自定义顶栏 ──
        self._drag_data = {'x': 0, 'y': 0, 'maximized': False, 'normal_geom': None}
        self.top_bar = ttk.Frame(master, style='TopBar.TFrame')
        self.top_bar.pack(fill='x', side='top', before=None)
        # 顶栏拖拽
        self.top_bar.bind('<Button-1>', self._start_move)
        self.top_bar.bind('<B1-Motion>', self._on_move)
        self.top_bar.bind('<Double-Button-1>', self._toggle_maximize)
        # 应用标题（左侧）
        self._title_label = ttk.Label(self.top_bar, text=_('lki.app.title'),
                                      style='TopBar.TLabel', anchor='w')
        self._title_label.pack(side='left', padx=10)
        self._title_label.bind('<Button-1>', self._start_move)
        self._title_label.bind('<B1-Motion>', self._on_move)
        self._title_label.bind('<Double-Button-1>', self._toggle_maximize)
        # 主题切换（右侧）
        theme_combo_frame = ttk.Frame(self.top_bar)
        theme_combo_frame.pack(side='right', padx=(0, 2))
        self._theme_combo = ttk.Combobox(theme_combo_frame, state='readonly', width=10)
        self._theme_combo['values'] = [_('lki.settings.theme.light'), _('lki.settings.theme.dark')]
        self._theme_combo.set(_('lki.settings.theme.light') if initial_theme == 'light' else _('lki.settings.theme.dark'))
        self._theme_combo.bind('<<ComboboxSelected>>', self._on_topbar_theme_changed)
        self._theme_combo.pack(side='left')
        # 窗口按钮
        self._btn_min = ttk.Button(theme_combo_frame, text='─', width=3,
                                   command=self._iconify_window)
        self._btn_min.pack(side='left', padx=(4, 1))
        self._btn_max = ttk.Button(theme_combo_frame, text='□', width=3,
                                   command=self._toggle_maximize)
        self._btn_max.pack(side='left', padx=1)
        self._btn_close = ttk.Button(theme_combo_frame, text='✕', width=3,
                                     command=self._close_window)
        self._btn_close.pack(side='left', padx=(1, 0))

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=(0, 10), padx=10, expand=True, fill='both')

        self.tab_game = GameTab(self.notebook, self.icons, self.type_id_to_name, self._on_instance_select)

        self.tab_advanced = AdvancedTab(self.notebook, self.icons, self.type_id_to_name)

        self.tab_settings = SettingsTab(self.notebook, self.icons, None,
                                        self._on_language_select, self.reload_app)

        self.tab_about = AboutTab(self.notebook)

        self.notebook.add(self.tab_game, text=_('lki.tab.game'))
        self.notebook.add(self.tab_advanced, text=_('lki.tab.advanced'))
        self.notebook.add(self.tab_settings, text=_('lki.tab.settings'))
        self.notebook.add(self.tab_about, text=_('lki.tab.about'))

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._center_main_window()

        self.master.after(100, self.run_initial_detection)

    def _setup_styles(self, is_dark: bool, font_family: str):
        """定义自定义字体和样式"""
        self.style = ttk.Style()
        self.select_bg = "#66bdff" if is_dark else "#0078d4"
        self.select_fg = "white"
        #self.style.configure("Client.TLabel", font=("TkDefaultFont", 12, "bold"))
        #self.style.configure("Path.TLabel", font=("TkDefaultFont", 9))
        self.style.configure("Selected.TFrame", background=self.select_bg)
        #self.style.configure("Selected.Client.TLabel", font=("TkDefaultFont", 12, "bold"), background=self.select_bg, foreground=self.select_fg)
        self.style.configure("Selected.Client.TLabel", background=self.select_bg, foreground=self.select_fg)
        #self.style.configure("Selected.Path.TLabel", font=("TkDefaultFont", 9), background=self.select_bg, foreground=self.select_fg)
        self.style.configure("Selected.Path.TLabel", background=self.select_bg, foreground=self.select_fg)
        #self.style.configure("Hint.TLabel", font=("TkDefaultFont", 9), foreground='gray')
        self.style.configure("Hint.TLabel", foreground='gray')
        self.style.configure("danger.TButton", foreground="#ff7777" if is_dark else "red", background="#d13438")

        self.style.configure("Link.TButton", foreground=self.select_bg, borderwidth=0, padding=0)
        self.style.map("Link.TButton",
                       foreground=[('active', self.select_bg), ('disabled', 'gray')],
                       underline=[('active', 1)])

        # 顶栏样式
        self.style.configure("TopBar.TFrame", background="#2b2b2b" if is_dark else "#e0e0e0")
        self.style.configure("TopBar.TLabel", background="#2b2b2b" if is_dark else "#e0e0e0",
                             foreground="white" if is_dark else "black", font=(font_family, 10))

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
                log("Warning: Window size not fully calculated, centering may be inaccurate.")

            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            self.master.geometry(f"+{x}+{y}")
        except tk.TclError as e:
            log(f"Error centering main window: {e}")

    def run_initial_detection(self):
        """在启动时*仅一次*触发自动检测。"""
        if not settings.global_settings.get('ever_launched', False):
            log("Running *first time* instance import...")

            self.tab_game._on_auto_import(is_initial_run=True)

            settings.global_settings.set('ever_launched', True)

    def _on_language_select(self):
        """由 SettingsTab 调用的回调。"""
        messagebox.showinfo(
            _('lki.app.title'),
            _('lki.settings.language.reload_required')
        )

    def _on_theme_select(self, selected_theme: str):
        """由 SettingsTab 调用的回调。"""
        self.master.call('set_theme', selected_theme, self.font_family)

        self._setup_styles(selected_theme == 'dark', self.font_family)

        self.icons.set_active_theme(selected_theme)
        self._update_all_icons()

    def _update_all_icons(self):
        """通知所有选项卡更新其图标"""
        self.tab_game.update_icons()
        self.tab_advanced.update_icons()
        self.tab_settings.update_icons()
        self.tab_about.update_icons()

    # ── 自定义顶栏：窗口控制 ──
    def _start_move(self, event):
        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root

    def _on_move(self, event):
        if self._drag_data.get('maximized'):
            return
        dx = event.x_root - self._drag_data['x']
        dy = event.y_root - self._drag_data['y']
        self.master.geometry(f'+{self.master.winfo_x() + dx}+{self.master.winfo_y() + dy}')
        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root

    def _toggle_maximize(self, event=None):
        if self._drag_data['maximized']:
            # 还原
            if self._drag_data['normal_geom']:
                self.master.geometry(self._drag_data['normal_geom'])
            self._drag_data['maximized'] = False
            self._btn_max.config(text='□')
        else:
            # 最大化：保存当前几何信息
            self._drag_data['normal_geom'] = self.master.geometry()
            screen_w = self.master.winfo_screenwidth()
            screen_h = self.master.winfo_screenheight()
            # 确保窗口覆盖整个屏幕（不包含任务栏区域）
            self.master.geometry(f'{screen_w}x{screen_h}+0+0')
            self._drag_data['maximized'] = True
            self._btn_max.config(text='❐')

    def _iconify_window(self):
        self.master.iconify()

    def _close_window(self):
        self.master.quit()

    def _on_topbar_theme_changed(self, event=None):
        selected = self._theme_combo.get()
        theme_map = {_('lki.settings.theme.light'): 'light', _('lki.settings.theme.dark'): 'dark'}
        theme = theme_map.get(selected, 'light')
        settings.global_settings.set('theme', theme)
        self._on_theme_select(theme)

    def _on_instance_select(self, instance: Optional[GameInstance]):
        """
        由 GameTab 调用的回调。
        通知 AdvancedTab 更新其内容。
        """
        self.tab_advanced.update_content(instance)

    def _on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1:
            current_instance = self.tab_game.get_selected_game_instance()
            self.tab_advanced.update_content(current_instance)

    def reload_app(self):
        log(_('lki.reload.status.reloading_ui'))

        try:
            settings.global_settings.save()
            instance_manager.global_instance_manager.save()

            global_translator.load_language(settings.global_settings.language)

            for widget in self.master.winfo_children():
                widget.destroy()

            current_theme = settings.global_settings.get('theme', 'light')
            self.master.call('set_theme', current_theme, self.font_family)

            root = self.master
            font_family = self.font_family
            scaling_factor = self.master.scaling_factor

            def _rebuild():
                LocalizationInstallerApp(root, initial_theme=current_theme,
                                         font_family=font_family,
                                         scaling_factor=scaling_factor)

            root.after(50, _rebuild)

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_message = _('lki.reload.error.failed_to_reload') % e
            messagebox.showerror(_('lki.reload.title'), error_message)
            sys.exit(1)
