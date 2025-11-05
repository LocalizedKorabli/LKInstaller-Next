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
import tkinter as tk
from tkinter import ttk
from typing import Optional

import utils


class BaseTab(ttk.Frame):
    """
    一个通用的选项卡基类，提供了创建动态换行占位符标签的功能。
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._placeholder_label: Optional[ttk.Label] = None

        # (新增) 绑定 Configure 事件以动态更新 wraplength
        self.bind("<Configure>", self._on_tab_configure)

    def _create_placeholder_label(self, text: str) -> ttk.Label:
        """
        创建一个居中的、动态换行的标签。
        这个标签会自动调整其 wraplength 以适应窗口大小。
        (已修改：此方法不再自动 pack 标签)
        """
        self._placeholder_label = ttk.Label(
            self,
            text=text,
            wraplength=1,  # 初始值，将被 _on_tab_configure 更新
            justify='center'
        )
        return self._placeholder_label

    def _on_tab_configure(self, event):
        """当选项卡框架的大小改变时，动态更新占位符的 wraplength。"""

        # 仅当此选项卡调用了 _create_placeholder_label 时才执行
        if not self._placeholder_label:
            return

        try:
            # event.width 是 AdvancedTab 的内容区域宽度 (已减去其自身的 padding)

            # 我们只需要减去 placeholder 自己的水平 padding
            # (padx=20, 左右各 20)
            # 总计 = 40
            base_padding = 40
            scaled_padding = utils.scale_dpi(self, base_padding)

            new_wraplength = event.width - scaled_padding

            if new_wraplength < 1:
                new_wraplength = 1

            self._placeholder_label.config(wraplength=new_wraplength)

        except (tk.TclError, AttributeError):
            pass  # 窗口可能正在销毁中或尚未完全初始化
