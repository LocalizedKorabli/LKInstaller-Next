import threading
import tkinter as tk
from tkinter import ttk, PhotoImage
from typing import Optional

import constants
import utils
from localizer import _
from ui.tabs.tab_base import BaseTab
from ui.windows.window_action import ActionProgressWindow


class AboutTab(BaseTab):
    def __init__(self, master):
        super().__init__(master, padding='10 10 10 10')
        self.app_master = master.master
        self.logo_image = None
        self.update_window: Optional[ActionProgressWindow] = None  # (新增)
        self.update_thread: Optional[threading.Thread] = None

        self._create_about_widgets()

    def _create_about_widgets(self):
        content_frame = ttk.Frame(self)
        content_frame.pack(expand=True, fill='both', anchor='n')

        # Logo
        logo_path = utils.base_path.joinpath('resources/imgs/lki.png')

        try:
            if logo_path.is_file():
                self.logo_image = PhotoImage(file=logo_path)
                logo_label = ttk.Label(content_frame, image=self.logo_image)
            else:
                logo_label = ttk.Label(content_frame, text="[Logo Placeholder - resources/imgs/lki.png not found]")

            logo_label.pack(pady=(0, 10))
        except Exception as e:
            print(f"Error loading logo image: {e}")
            logo_label = ttk.Label(content_frame, text="[Logo Loading Error]")
            logo_label.pack(pady=(0, 10))

        # App Name
        title_text = _('lki.app.title')

        title_label = ttk.Label(content_frame, text=title_text)
        title_label.pack(pady=(0, 20))

        # Version & Update
        version_center_frame = ttk.Frame(content_frame)
        # 将这个 Frame 居中打包
        version_center_frame.pack(pady=(10, 0))

        # 2a. 版本显示标签
        version_display_text = f"{_('lki.version.label')}: {constants.APP_VERSION}"
        version_label = ttk.Label(version_center_frame, text=version_display_text)
        # 将标签靠左打包在内部 Frame 中
        version_label.pack(side='left', anchor='w')

        # 2b. 检查更新按钮
        check_update_btn = ttk.Button(version_center_frame, text=_('lki.version.check_update'),
                                      command=self._check_for_updates)
        # 将按钮靠右打包在内部 Frame 中，并添加少量间隔
        check_update_btn.pack(side='left', padx=(20, 0))

    def _check_for_updates(self):
        """(修改) 在新线程中启动更新检查。"""
        print("Checking for updates...")

        # (新增) 防止打开多个更新窗口
        if self.update_window and self.update_window.winfo_exists():
            self.update_window.focus_force()
            return

        # (修改) 使用 ActionProgressWindow
        self.update_window = ActionProgressWindow(
            self.app_master,
            [_('lki.update.title')],  # 任务名称即为标题
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

    def _on_update_cancel(self):  # (新增)
        """当更新窗口的取消按钮被按下时调用。"""
        print("Update check/download cancelled by user.")
        # 工作线程 (utils.update_worker) 会检查 window.is_cancelled()，
        # 该状态由窗口自己的 _on_close() 方法设置。
        # 此处我们不需要做额外操作，但必须提供这个回调函数。
        pass
