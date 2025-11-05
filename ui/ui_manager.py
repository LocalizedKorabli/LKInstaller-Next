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
from typing import Optional

import dirs
from logger import log


class IconManager:
    def __init__(self):
        self.icons = {
            'light': {},
            'dark': {}
        }

        self._load_icon_set('light')
        self._load_icon_set('dark')

        self.import_icon = None  # <-- (重命名自 self.add)
        self.rename = None
        self.remove = None
        self.auto_import_icon = None  # <-- (重命名自 self.detect)
        self.manage = None
        self.folder = None
        self.download = None
        self.copy = None
        self.refresh = None
        self.play = None
        self.up = None
        self.down = None

    def _load_icon_set(self, theme_name):
        """加载特定主题的图标集"""
        from tkinter import PhotoImage
        icon_names = ['import', 'rename', 'remove', 'detect', 'manage', 'folder', 'download', 'copy', 'up', 'down',
                      'refresh', 'play']

        for name in icon_names:
            path = dirs.base_path.joinpath(f'resources/icons/{theme_name}/{name}.png')
            try:
                self.icons[theme_name][name] = PhotoImage(file=path)
            except Exception as e:
                log(f"FATAL: 无法加载图标: {path}\n{e}")
                self.icons[theme_name][name] = None

    def set_active_theme(self, theme_name):
        """
        将活动图标集（例如 self.add）设置为 'light' 或 'dark'。
        """
        if theme_name not in ['light', 'dark']:
            log(f"Warning: 未知的图标主题 '{theme_name}'。默认为 'light'。")
            theme_name = 'light'

        self.import_icon = self.icons[theme_name]['import']
        self.rename = self.icons[theme_name]['rename']
        self.remove = self.icons[theme_name]['remove']
        self.auto_import_icon = self.icons[theme_name]['detect']
        self.manage = self.icons[theme_name]['manage']
        self.folder = self.icons[theme_name]['folder']
        self.download = self.icons[theme_name]['download']
        self.copy = self.icons[theme_name]['copy']
        self.refresh = self.icons[theme_name]['refresh']
        self.play = self.icons[theme_name]['play']
        self.up = self.icons[theme_name]['up']
        self.down = self.icons[theme_name]['down']

global_icon_manager: Optional[IconManager] = None

def get_icon_manager() -> IconManager:
    global global_icon_manager
    if global_icon_manager is None:
        global_icon_manager = IconManager()
    return global_icon_manager