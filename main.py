import tkinter as tk
import settings
import utils
import instance_manager
import localization_sources  # <-- 确保在 app 之前加载

from app import LocalizationInstallerApp

if __name__ == '__main__':
    root = tk.Tk()

    try:
        theme = settings.global_settings.get('theme', 'light')
    except Exception as e:
        print(f"Could not load settings, defaulting theme. Error: {e}")
        theme = 'light'

    root.call('source', utils.base_path.joinpath('azure/azure.tcl'))
    root.call('set_theme', theme)

    app = LocalizationInstallerApp(root, initial_theme=theme)
    root.mainloop()

    try:
        settings.global_settings.save()
        instance_manager.global_instance_manager.save()
    except AttributeError:
        print("Settings module not fully implemented, skipping save.")