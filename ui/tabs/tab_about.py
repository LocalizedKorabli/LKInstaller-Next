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
import threading
import webbrowser  # (新增) 用于打开网页
from tkinter import ttk, PhotoImage
from typing import Optional
from tktooltip import ToolTip

import dirs
import constants
import utils
from localizer import _
from logger import log
from ui.tabs.tab_base import BaseTab
from ui.ui_manager import get_icon_manager  # (新增) 用于获取图标
from ui.windows.window_action import ActionProgressWindow


class AboutTab(BaseTab):
    def __init__(self, master):
        super().__init__(master, padding='10 10 10 10')
        self.app_master = master.master
        self.logo_image = None
        self.update_window: Optional[ActionProgressWindow] = None
        self.update_thread: Optional[threading.Thread] = None
        self.icons = get_icon_manager()

        self._create_about_widgets()

    def _create_about_widgets(self):
        content_frame = ttk.Frame(self)
        # 使用 anchor='n' 确保内容在垂直拉伸时靠上对齐，避免分散
        content_frame.pack(expand=True, fill='both', anchor='n')

        # 1. Logo
        logo_path = dirs.base_path.joinpath('resources/imgs/lki.png')

        try:
            if logo_path.is_file():
                self.logo_image = PhotoImage(file=logo_path)
                logo_label = ttk.Label(content_frame, image=self.logo_image)
            else:
                logo_label = ttk.Label(content_frame, text="[Logo Placeholder - resources/imgs/lki.png not found]")

            # 增加一点顶部边距
            logo_label.pack(pady=(30, 10))
        except Exception as e:
            log(f"Error loading logo image: {e}")
            logo_label = ttk.Label(content_frame, text="[Logo Loading Error]")
            logo_label.pack(pady=(30, 10))

        # 2. App Name
        title_text = _('lki.app.title')
        title_label = ttk.Label(content_frame, text=title_text)
        title_label.pack(pady=(0, 15))

        # --- (新增) 3. 社交图标栏 ---
        social_frame = ttk.Frame(content_frame)
        social_frame.pack(pady=(0, 20))

        self.btn_social_github = ttk.Button(
            social_frame,
            image=self.icons.github,
            command=lambda: webbrowser.open('https://github.com/LocalizedKorabli'),
            style="Toolbutton",
            cursor="hand2"
        )
        self.btn_social_qq = ttk.Button(
            social_frame,
            image=self.icons.qq,
            command=lambda: webbrowser.open('https://qm.qq.com/q/SUoZAcV442'),
            style="Toolbutton",
            cursor="hand2"
        )
        self.btn_social_discord = ttk.Button(
            social_frame,
            image=self.icons.discord,
            command=lambda: webbrowser.open('https://discord.gg/3d9k2mkWy4'),
            style="Toolbutton",
            cursor="hand2"
        )
        self.btn_social_github.pack(side='left', padx=8)
        self.btn_social_qq.pack(side='left', padx=8)
        self.btn_social_discord.pack(side='left', padx=8)
        ToolTip(self.btn_social_github, msg=_('lki.about.contacts.github'))
        ToolTip(self.btn_social_qq, msg=_('lki.about.contacts.qq'))
        ToolTip(self.btn_social_discord, msg=_('lki.about.contacts.discord'))

        # 4. Version & Update
        version_center_frame = ttk.Frame(content_frame)
        version_center_frame.pack(pady=(0, 10))

        # 4a. 版本显示标签
        version_display_text = f"{_('lki.version.label')}: {constants.APP_VERSION}"
        version_label = ttk.Label(version_center_frame, text=version_display_text)
        version_label.pack(side='left', anchor='w')

        # 4b. 检查更新按钮
        check_update_btn = ttk.Button(version_center_frame, text=_('lki.version.check_update'),
                                      command=self._check_for_updates)
        check_update_btn.pack(side='left', padx=(20, 0))

        # (新增) 5. 底部版权信息
        copyright_text = "Copyright © 2025 LocalizedKorabli"
        copyright_label = ttk.Label(content_frame, text=copyright_text, foreground='gray')
        # 使用 side='bottom' 将其推到最下方（虽然在 anchor='n' 的 frame 里效果不明显，但结构更清晰）
        copyright_label.pack(side='bottom', pady=(20, 20))

    def _check_for_updates(self):
        """(修改) 在新线程中启动更新检查。"""
        log("Checking for updates...")

        # (新增) 防止打开多个更新窗口
        if self.update_window and self.update_window.winfo_exists():
            self.update_window.focus_force()
            return

        # (修改) 使用 ActionProgressWindow
        self.update_window = ActionProgressWindow(
            self.app_master,
            {_('lki.update.title'): None},  # 任务名称即为标题
            cancel_callback=self._on_update_cancel,  # (修改) 传入回调
            title=_('lki.update.title'),
            starting_text=_('lki.update.status.checking'),
            pending_text=_('lki.update.status.checking')
        )

        # (修改) 启动工作线程
        self.update_thread = threading.Thread(
            target=utils.update_worker,
            args=(self.update_window, self.app_master),  # 传入窗口和根 tk
            daemon=True
        )
        self.update_thread.start()

    def _on_update_cancel(self):
        """当更新窗口的取消按钮被按下时调用。"""
        log("Update check/download cancelled by user.")
        pass

    def update_icons(self):
        """当主题更改时更新此选项卡上的图标"""
        self.btn_social_github.config(image=self.icons.github)
        self.btn_social_qq.config(image=self.icons.qq)
        self.btn_social_discord.config(image=self.icons.discord)