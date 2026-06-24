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
import platform
import tkinter as tk
import sys
from pathlib import Path

from core import dirs
from core import settings
from instance import instance_manager
from installation.installation_manager import InstallationManager, InstallationTask
from instance.game_instance import GameInstance
from core.localizer import global_translator, _, _best_fonts
from core.logger import setup_logger, log

def run_auto_execute(root, arg, run_client):
    """
    在简洁模式下运行安装程序。
    """
    log(f"Auto-execute mode triggered with arg: {arg}, run_client: {run_client}")

    try:
        instance_id, preset_id = arg.split(':', 1)
    except ValueError:
        log(f"Error: Invalid --auto-execute-preset argument. Expected format: 'instance_id:preset_id'")
        sys.exit(1)

    instance_data = instance_manager.global_instance_manager.get_instance(instance_id)
    if not instance_data:
        log(f"Error: Could not find instance with ID: {instance_id}")
        sys.exit(1)

    preset_data = instance_data.get('presets', {}).get(preset_id)
    if not preset_data:
        log(f"Error: Could not find preset '{preset_id}' for instance '{instance_data.get('name')}'")
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
        log(f"Error initializing game instance {instance_data['name']}: {e}")
        sys.exit(1)

    # 为预设添加一个可显示的名称
    if preset_data.get('is_default'):
        preset_data['name'] = _(preset_data.get('name_key', 'lki.preset.default.name'))
    else:
        preset_data['name'] = preset_data.get('name', preset_id)

    task = InstallationTask(instance, preset_data, root)

    def _on_auto_install_complete():
        log("Auto-install complete.")
        if run_client:
            log("Launching client...")
            success, exe_name = instance.launch_game()
            if not success:
                log(f"Error: Failed to launch game at {instance.path}")

        log("Exiting.")
        root.after(500, root.quit)

    # 启动安装
    manager = InstallationManager(root)
    def deferred_start_installation():
        log("Mainloop is running. Starting installation...")
        try:
            manager.start_installation([task], _on_auto_install_complete)
        except Exception as e:
            log(f"CRITICAL ERROR during installation start: {e}")
            import traceback
            traceback.print_exc()
            root.quit()

    root.after(100, deferred_start_installation)

    log("Starting mainloop, waiting for deferred start...")
    root.mainloop()


def run_auto_execute_all(root, run_client):
    """
    为所有已配置的实例（使用其已选中的预设）运行自动更新。
    """
    log(f"Auto-execute-all mode triggered, run_client={run_client}")

    all_instances = instance_manager.global_instance_manager.get_all()
    if not all_instances:
        log("Error: No instances configured, nothing to update.")
        sys.exit(1)

    tasks = []
    first_instance = None  # 记住第一个合法实例，用于 runclient

    for instance_id, instance_data in all_instances.items():
        preset_id = instance_data.get('active_preset_id', 'default')
        preset_data = instance_data.get('presets', {}).get(preset_id)
        if not preset_data:
            log(f"Warning: Instance '{instance_data.get('name', instance_id)}' has no active preset '{preset_id}', skipping.")
            continue

        try:
            instance = GameInstance(
                instance_id=instance_id,
                path=Path(instance_data['path']),
                name=instance_data['name'],
                type=instance_data['type']
            )
        except Exception as e:
            log(f"Error initializing game instance {instance_data.get('name', instance_id)}: {e}")
            continue

        if first_instance is None:
            first_instance = instance

        # 为预设添加可显示的名称
        if preset_data.get('is_default'):
            preset_data['name'] = _(preset_data.get('name_key', 'lki.preset.default.name'))
        else:
            preset_data['name'] = preset_data.get('name', preset_id)

        tasks.append(InstallationTask(instance, preset_data, root))
        log(f"Queued task: {instance_data['name']} -> {preset_data['name']}")

    if not tasks:
        log("Error: No valid instances/presets to update.")
        sys.exit(1)

    log(f"Starting batch update for {len(tasks)} instance(s)...")

    def _on_all_complete():
        log("Batch auto-install complete.")
        if run_client and first_instance:
            log("Launching client (first instance)...")
            success, exe_name = first_instance.launch_game()
            if not success:
                log(f"Error: Failed to launch game at {first_instance.path}")

        log("Exiting.")
        root.after(500, root.quit)

    manager = InstallationManager(root)

    def deferred_start_all():
        log("Mainloop is running. Starting batch installation...")
        try:
            manager.start_installation(tasks, _on_all_complete)
        except Exception as e:
            log(f"CRITICAL ERROR during batch installation: {e}")
            import traceback
            traceback.print_exc()
            root.quit()

    root.after(100, deferred_start_all)

    log("Starting mainloop, waiting for deferred batch start...")
    root.mainloop()


if __name__ == '__main__':
    setup_logger()
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
        log(f"Warning: Could not set DPI awareness: {e}")

    global_translator.load_language(settings.global_settings.language)
    from core.utils import register_app_paths_alias
    register_app_paths_alias()
    from ui.app import LocalizationInstallerApp
    root = tk.Tk()

    auto_execute_arg = None
    auto_execute_all = False
    run_client_flag = False

    args = sys.argv[1:]

    if '--auto-execute-all' in args:
        auto_execute_all = True

    if '--auto-execute-preset' in args:
        if auto_execute_all:
            log("Warning: Both --auto-execute-all and --auto-execute-preset specified. Using --auto-execute-all.")
        else:
            try:
                idx = args.index('--auto-execute-preset')
                if idx + 1 < len(args):
                    auto_execute_arg = args[idx + 1]
                else:
                    log("Error: --auto-execute-preset flag found but no argument provided.")
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
                log(f"HiDPI detected. Scaling factor: {scaling_factor}")
                root.tk.call('tk', 'scaling', scaling_factor)
    except Exception as e:
        log(f"Warning: Could not set Tk scaling: {e}")
        scaling_factor = 1.0  # 重置

    try:
        theme = settings.global_settings.get('theme', 'light')
    except Exception as e:
        log(f"Could not load settings, defaulting theme. Error: {e}")
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

    root.call('source', dirs.base_path.joinpath('resources/theme/azure/azure.tcl'))
    root.call('set_theme', theme, font_family)

    root.iconbitmap(default=dirs.base_path.joinpath('resources/logo/logo64.ico'))

    if auto_execute_arg:
        # --- 简洁模式（单实例） ---
        root.withdraw()  # 隐藏根窗口
        run_auto_execute(root, auto_execute_arg, run_client_flag)
    elif auto_execute_all:
        # --- 简洁模式（全部实例） ---
        root.withdraw()
        run_auto_execute_all(root, run_client_flag)
    else:
        # --- GUI模式 ---
        root.withdraw()
        root.overridedirect(True)
        root.deiconify()
        app = LocalizationInstallerApp(root, initial_theme=theme, font_family=font_family, scaling_factor=scaling_factor)
        root.mainloop()

    try:
        settings.global_settings.save()
        instance_manager.global_instance_manager.save()
    except Exception:  # (捕捉更广泛的异常，因为 settings 可能未完全加载)
        log("Settings module not fully loaded or failed, skipping save.")

# pyinstaller -w lki.py --add-data "resources\*;resources" -i resources\logo\logo.ico --version-file=assets\version_file.txt --clean --uac-admin
# Windows 7 Users: Install KB3063858 & KB2999226