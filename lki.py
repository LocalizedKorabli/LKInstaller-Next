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
import os
import platform
import tkinter as tk
import sys
from pathlib import Path

import settings
import utils
from instance import instance_manager
from installation.installation_manager import InstallationManager, InstallationTask
from instance.game_instance import GameInstance
from localizer import global_translator, _
from logger import setup_logger

# HiDPI Awareness
try:
    import ctypes
    if platform.system() == "Windows":
        ver = float(platform.version().split('.')[0])
        # Windows 8.1+ (version >= 6.3)
        if ver >= 6.3:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        else:
            # Windows Vista / 7 / 8
            ctypes.windll.user32.SetProcessDPIAware()
except Exception as e:
    print(f"Warning: Could not set DPI awareness: {e}")

global_translator.load_language(settings.global_settings.language)
from app import LocalizationInstallerApp


def run_auto_execute(root, arg, run_client):
    """
    在简洁模式下运行安装程序。
    """
    print(f"Auto-execute mode triggered with arg: {arg}, run_client: {run_client}")

    try:
        instance_id, preset_id = arg.split(':', 1)
    except ValueError:
        print(f"Error: Invalid --auto-execute-preset argument. Expected format: 'instance_id:preset_id'")
        sys.exit(1)

    instance_data = instance_manager.global_instance_manager.get_instance(instance_id)
    if not instance_data:
        print(f"Error: Could not find instance with ID: {instance_id}")
        sys.exit(1)

    preset_data = instance_data.get('presets', {}).get(preset_id)
    if not preset_data:
        print(f"Error: Could not find preset '{preset_id}' for instance '{instance_data.get('name')}'")
        sys.exit(1)

    # 创建必要的对象
    try:
        instance = GameInstance(
            instance_id=instance_id,
            path=Path(instance_data['path']),
            name=instance_data['name'],
            type=instance_data['type']
        )
    except Exception as e:
        print(f"Error initializing game instance {instance_data['name']}: {e}")
        sys.exit(1)

    # 为预设添加一个可显示的名称
    if preset_data.get('is_default'):
        preset_data['name'] = _(preset_data.get('name_key', 'lki.preset.default.name'))
    else:
        preset_data['name'] = preset_data.get('name', preset_id)

    task = InstallationTask(instance, preset_data, root)

    def _on_auto_install_complete():
        print("Auto-install complete.")
        if run_client:
            print("Launching client...")
            success, exe_name = instance.launch_game()
            if not success:
                print(f"Error: Failed to launch game at {instance.path}")

        print("Exiting.")
        root.after(500, root.quit)

    # 启动安装
    manager = InstallationManager(root)
    def deferred_start_installation():
        print("Mainloop is running. Starting installation...")
        try:
            manager.start_installation([task], _on_auto_install_complete)
        except Exception as e:
            print(f"CRITICAL ERROR during installation start: {e}")
            import traceback
            traceback.print_exc()
            root.quit()

    root.after(100, deferred_start_installation)

    print("Starting mainloop, waiting for deferred start...")
    root.mainloop()


if __name__ == '__main__':
    setup_logger()
    root = tk.Tk()

    auto_execute_arg = None
    run_client_flag = False

    args = sys.argv[1:]
    if '--auto-execute-preset' in args:
        try:
            idx = args.index('--auto-execute-preset')
            if idx + 1 < len(args):
                auto_execute_arg = args[idx + 1]
            else:
                print("Error: --auto-execute-preset flag found but no argument provided.")
                sys.exit(1)
        except ValueError:
            pass

    if '--runclient' in args:
        run_client_flag = True

    scaling_factor = 1.0
    try:
        if platform.system() == "Windows":
            dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
            scaling_factor = dpi / 96.0  # 96 DPI = 100% 缩放
            if scaling_factor > 1.0:
                print(f"HiDPI detected. Scaling factor: {scaling_factor}")
                root.tk.call('tk', 'scaling', scaling_factor)
    except Exception as e:
        print(f"Warning: Could not set Tk scaling: {e}")
        scaling_factor = 1.0  # 重置

    try:
        theme = settings.global_settings.get('theme', 'light')
    except Exception as e:
        print(f"Could not load settings, defaulting theme. Error: {e}")
        theme = 'light'

    font_family = "Microsoft YaHei"

    try:
        if platform.system() == "Windows":
            # Windows 11 Build Number >= 22000
            build_number = int(platform.version().split('.')[-1])
            if build_number >= 22000:
                font_family = "Segoe UI"
    except (ValueError, IndexError):
        pass

    root.call('source', utils.base_path.joinpath('resources/theme/azure/azure.tcl'))
    root.call('set_theme', theme, font_family)

    root.iconbitmap(default=utils.base_path.joinpath('resources/logo/logo64.ico'))

    if auto_execute_arg:
        # --- 简洁模式 ---
        root.withdraw()  # 隐藏根窗口
        run_auto_execute(root, auto_execute_arg, run_client_flag)
    else:
        # --- GUI模式 ---
        app = LocalizationInstallerApp(root, initial_theme=theme, font_family=font_family, scaling_factor=scaling_factor)
        root.mainloop()

    try:
        settings.global_settings.save()
        instance_manager.global_instance_manager.save()
    except Exception:  # (捕捉更广泛的异常，因为 settings 可能未完全加载)
        print("Settings module not fully loaded or failed, skipping save.")

# pyinstaller -w lki.py --add-data "resources\*;resources" -i resources\logo\logo.ico --version-file=assets\version_file.txt --clean --uac-admin
# Windows 7 Users: Install KB3063858