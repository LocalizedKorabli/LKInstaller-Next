import tkinter as tk
from tkinter import PhotoImage
import utils


class IconManager:
    """
    加载并管理浅色和深色主题的所有图标。
    (使用 tk.PhotoImage)
    """

    def __init__(self):
        self.icons = {
            'light': {},
            'dark': {}
        }

        self._load_icon_set('light')
        self._load_icon_set('dark')

        self.add = None
        self.rename = None
        self.remove = None
        self.detect = None
        self.manage = None
        self.folder = None
        self.download = None
        self.copy = None  # <-- (新增)

    def _load_icon_set(self, theme_name):
        """加载特定主题的图标集"""
        # (已修改)
        icon_names = ['add', 'rename', 'remove', 'detect', 'manage', 'folder', 'download', 'copy']  # <-- (新增 'copy')
        for name in icon_names:
            path = utils.base_path.joinpath(f'resources/icons/{theme_name}/{name}.png')
            try:
                self.icons[theme_name][name] = PhotoImage(file=path)
            except Exception as e:
                print(f"FATAL: 无法加载图标: {path}\n{e}")
                self.icons[theme_name][name] = None

    def set_active_theme(self, theme_name):
        """
        将活动图标集（例如 self.add）设置为 'light' 或 'dark'。
        """
        if theme_name not in ['light', 'dark']:
            print(f"Warning: 未知的图标主题 '{theme_name}'。默认为 'light'。")
            theme_name = 'light'

        self.add = self.icons[theme_name]['add']
        self.rename = self.icons[theme_name]['rename']
        self.remove = self.icons[theme_name]['remove']
        self.detect = self.icons[theme_name]['detect']
        self.manage = self.icons[theme_name]['manage']
        self.folder = self.icons[theme_name]['folder']
        self.download = self.icons[theme_name]['download']
        self.copy = self.icons[theme_name]['copy']  # <-- (新增)