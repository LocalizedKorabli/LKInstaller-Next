import tkinter as tk
from tkinter import ttk, PhotoImage
from localizer import _
from ui.tabs.tab_base import BaseTab
import constants
import utils


class AboutTab(BaseTab):
    """
    “关于”选项卡 UI。
    """

    def __init__(self, master):
        super().__init__(master, padding='10 10 10 10')
        self.logo_image = None

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
        """检查更新的占位方法"""
        print("Checking for updates...")
        tk.messagebox.showinfo(_('lki.app.title'), "Check for updates feature not yet implemented.", parent=self)
