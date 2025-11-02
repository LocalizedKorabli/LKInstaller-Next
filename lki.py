import ctypes
import platform
import tkinter as tk
import sys  # (新增)
from pathlib import Path  # (新增)

import settings
import utils
from instance import instance_manager
from installation.installation_manager import InstallationManager, InstallationTask  # (新增)
from instance.game_instance import GameInstance  # (新增)
from localizer import global_translator, _  # (新增 _)

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

global_translator.load_language(settings.global_settings.language)
# (已修改：导入新的 app 位置)
from app import LocalizationInstallerApp


# --- (新增) Function to handle auto-execution ---
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

    # (为预设添加一个可显示的名称)
    if preset_data.get('is_default'):
        preset_data['name'] = _(preset_data.get('name_key', 'lki.preset.default.name'))
    else:
        preset_data['name'] = preset_data.get('name', preset_id)

    task = InstallationTask(instance, preset_data, root)

    # 定义完成回调
    def _on_auto_install_complete():
        print("Auto-install complete.")
        if run_client:
            print("Launching client...")
            success, exe_name = instance.launch_game()
            if not success:
                print(f"Error: Failed to launch game at {instance.path}")

        # 退出应用
        print("Exiting.")
        # (稍作延迟以确保 Popen 有时间启动)
        root.after(500, root.quit)

    # 启动安装
    manager = InstallationManager(root)
    def deferred_start_installation():
        """这个函数将在 mainloop 启动后被调用。"""
        print("Mainloop is running. Starting installation...")
        try:
            # 在这里启动安装
            manager.start_installation([task], _on_auto_install_complete)
        except Exception as e:
            # 确保我们能捕获到安装过程中的任何启动错误
            print(f"CRITICAL ERROR during installation start: {e}")
            import traceback
            traceback.print_exc()
            root.quit()

    # 安排安装任务在 mainloop 启动后 (例如 100 毫秒后) 再开始
    # 这给了 Tkinter 足够的时间来准备就绪
    root.after(100, deferred_start_installation)

    # 现在，我们立即启动 mainloop
    # 它会等待 100ms，然后执行 deferred_start_installation
    print("Starting mainloop, waiting for deferred start...")
    root.mainloop()


if __name__ == '__main__':
    root = tk.Tk()

    # --- (新增) 参数解析逻辑 ---
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
            pass  # 标志不存在

    if '--runclient' in args:
        run_client_flag = True
    # --- (新增结束) ---

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

    # (新增) 条件执行
    if auto_execute_arg:
        # --- 简洁模式 ---
        root.withdraw()  # 隐藏主根窗口
        run_auto_execute(root, auto_execute_arg, run_client_flag)
    else:
        # --- GUI模式 ---
        app = LocalizationInstallerApp(root, initial_theme=theme, scaling_factor=scaling_factor)
        root.iconbitmap(utils.base_path.joinpath('resources/logo/logo.ico'))
        root.mainloop()

    try:
        settings.global_settings.save()
        instance_manager.global_instance_manager.save()
    except Exception:  # (捕捉更广泛的异常，因为 settings 可能未完全加载)
        print("Settings module not fully loaded or failed, skipping save.")

# pyinstaller -w lki.py --add-data "resources\*;resources" -i resources\logo\logo.ico --version-file=assets\version_file.txt --clean --uac-admin