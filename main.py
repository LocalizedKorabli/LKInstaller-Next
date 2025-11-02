import os
import sys
import tkinter as tk
import settings
import utils
import instance_manager
import localization_sources  # <-- 确保在 app 之前加载

import ctypes
import platform

# (新增) --- 步骤 1: 设置 HiDPI 感知 ---
try:
    if platform.system() == "Windows":
        # Win 8.1+ API
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except AttributeError:
    try:
        # Win Vista/7 API
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"Warning: Could not set DPI awareness: {e}")

from localizer import global_translator
global_translator.load_language(settings.global_settings.language)
# (已修改：导入新的 app 位置)
from app import LocalizationInstallerApp

if __name__ == '__main__':
    root = tk.Tk()

    # (新增) --- 步骤 2: 计算缩放因子 ---
    scaling_factor = 1.0
    try:
        if platform.system() == "Windows":
            dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
            scaling_factor = dpi / 96.0  # 96 DPI = 100% 缩放

            if scaling_factor > 1.0:
                print(f"HiDPI detected. Scaling factor: {scaling_factor}")
                # (新增) 步骤 3: 立即应用Tkinter缩放
                root.tk.call('tk', 'scaling', scaling_factor)
    except Exception as e:
        print(f"Warning: Could not set Tk scaling: {e}")
        scaling_factor = 1.0  # 重置
    # --- (新增结束) ---

    try:
        theme = settings.global_settings.get('theme', 'light')
    except Exception as e:
        print(f"Could not load settings, defaulting theme. Error: {e}")
        theme = 'light'

    root.call('source', utils.base_path.joinpath('resources/theme/azure/azure.tcl'))
    root.call('set_theme', theme)

    app = LocalizationInstallerApp(root, initial_theme=theme, scaling_factor=scaling_factor)
    root.mainloop()

    try:
        settings.global_settings.save()
        instance_manager.global_instance_manager.save()
    except Exception: # (捕捉更广泛的异常，因为 settings 可能未完全加载)
        print("Settings module not fully loaded or failed, skipping save.")