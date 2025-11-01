import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Dict, Optional
import os
import xml.etree.ElementTree as Et
import threading
import re
import subprocess
import webbrowser

try:
    from tktooltip import ToolTip
except ImportError:
    print("Warning: tktooltip not found. Tooltips will be disabled.")
    ToolTip = None

import settings
import instance_manager
from localizer import _
from game_instance import GameInstance
from ui.dialogs import CustomAskStringDialog
from instance_detector import find_instances_for_auto_import, get_instance_type_from_path
from installation_manager import InstallationManager, InstallationTask  # <-- (新增)
from localization_sources import global_source_manager


class GameTab(ttk.Frame):
    """
    “游戏”选项卡 UI。
    """

    def __init__(self, master, icons, type_id_to_name, on_instance_select_callback):
        super().__init__(master, padding='10 10 10 10')

        self.app_master = master.master
        self.l10n_id_to_name, _ = global_source_manager.get_display_maps()
        self.icons = icons
        self.type_id_to_name = type_id_to_name
        self.on_instance_select_callback = on_instance_select_callback

        # (新增)
        self.installation_manager = InstallationManager(self.app_master)

        self.instance_manager = instance_manager.global_instance_manager
        self.game_instances: Dict[str, any] = {}
        self.selected_instance_id: Optional[str] = None
        self.selected_client_widget: Optional[ttk.Frame] = None

        self.loaded_game_instances: Dict[str, GameInstance] = {}

        self.client_check_vars: List[tk.BooleanVar] = []
        self.select_all_var = tk.BooleanVar()

        self._create_game_tab_widgets()

        self._load_and_display_instances()
        self._build_client_list_ui()

    # (已修改：连接安装按钮)
    def _create_game_tab_widgets(self):
        """创建“游戏”选项卡中的所有小部件"""

        top_frame = ttk.Frame(self, padding=(5, 0))
        top_frame.pack(fill='x', side='top', pady=(0, 10))

        top_buttons_frame = ttk.Frame(top_frame)
        top_buttons_frame.pack(side='right', anchor='e')
        self.check_all_btn = ttk.Checkbutton(top_frame, variable=self.select_all_var, command=self._on_select_all)
        self.check_all_btn.pack(side='left', padx=(0, 10), anchor='center')
        title_label = ttk.Label(top_frame, text=_('lki.game.detected_clients'), style="Client.TLabel")
        title_label.pack(side='left', anchor='w')

        self.btn_import = ttk.Button(top_buttons_frame, image=self.icons.import_icon, style="Toolbutton",
                                     command=self._open_import_instance_window)
        self.btn_import.pack(side='left', padx=(0, 2))
        self.btn_rename = ttk.Button(top_buttons_frame, image=self.icons.rename, style="Toolbutton",
                                     command=self._open_edit_instance_window, state='disabled')
        self.btn_rename.pack(side='left', padx=2)
        self.btn_remove = ttk.Button(top_buttons_frame, image=self.icons.remove, style="Toolbutton",
                                     command=self._open_delete_instance_window, state='disabled')
        self.btn_remove.pack(side='left', padx=2)
        self.btn_auto_import = ttk.Button(top_buttons_frame, image=self.icons.auto_import_icon, style="Toolbutton",
                                          command=self._on_auto_import)
        self.btn_auto_import.pack(side='left', padx=(2, 0))

        hint_label = ttk.Label(self, text=_('lki.game.install_hint'), style="Hint.TLabel", anchor='center',
                               wraplength=400)
        hint_label.pack(fill='x', side='bottom', pady=(5, 0))

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill='x', side='bottom', pady=(10, 0))

        # (已修改：连接到新命令)
        self.btn_install_selected = ttk.Button(bottom_frame, text=_('lki.game.btn.install_selected'),
                                               command=self._on_install_clicked)
        self.btn_install_selected.pack(fill='x', expand=True)

        instance_actions_frame = ttk.Frame(self)
        instance_actions_frame.pack(fill='x', side='bottom', pady=(5, 0))

        bottom_buttons_frame = ttk.Frame(instance_actions_frame)
        bottom_buttons_frame.pack(side='right', anchor='e')

        self.btn_move_up = ttk.Button(bottom_buttons_frame, image=self.icons.up, style="Toolbutton",
                                      command=self._move_instance_up, state='disabled')
        self.btn_move_up.pack(side='left', padx=(0, 2))

        self.btn_move_down = ttk.Button(bottom_buttons_frame, image=self.icons.down, style="Toolbutton",
                                        command=self._move_instance_down, state='disabled')
        self.btn_move_down.pack(side='left', padx=2)

        self.btn_open_folder = ttk.Button(bottom_buttons_frame, image=self.icons.folder, style="Toolbutton",
                                          command=self._open_instance_folder, state='disabled')
        self.btn_open_folder.pack(side='left', padx=2)

        list_container = ttk.Frame(self)
        list_container.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(list_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.client_list_frame = ttk.Frame(self.canvas)
        self.client_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.client_list_window = self.canvas.create_window((0, 0), window=self.client_list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.client_list_frame)

        if ToolTip:
            ToolTip(self.btn_import, _('lki.tooltip.add_instance'))
            ToolTip(self.btn_rename, _('lki.tooltip.edit_instance'))
            ToolTip(self.btn_remove, _('lki.tooltip.remove_instance'))
            ToolTip(self.btn_auto_import, _('lki.tooltip.detect_instances'))
            ToolTip(self.btn_move_up, _('lki.tooltip.move_up'))
            ToolTip(self.btn_move_down, _('lki.tooltip.move_down'))
            ToolTip(self.btn_open_folder, _('lki.tooltip.open_folder'))

    def _load_and_display_instances(self):
        """从管理器加载实例数据。"""
        self.game_instances = self.instance_manager.get_all()

    def _refresh_client_list(self):
        """清除、重新加载并重新构建客户端列表 UI。"""
        for widget in self.client_list_frame.winfo_children():
            widget.destroy()

        self.client_check_vars = []
        self.select_all_var.set(False)
        self.check_all_btn.state(['!alternate'])

        self.game_instances = self.instance_manager.get_all()

        self._build_client_list_ui()

    def clear_selection_and_refresh(self):
        """由 App 调用，在外部事件（如更改类型）后刷新列表"""
        self.selected_instance_id = None
        self.selected_client_widget = None
        self.loaded_game_instances.clear()
        self._refresh_client_list()
        self.on_instance_select_callback(None)

    def _build_client_list_ui(self):
        """
        使用 self.game_instances 中的数据填充客户端列表 UI。
        """
        self.loaded_game_instances.clear()
        loaded_instances: List[GameInstance] = []

        for instance_id, data in self.game_instances.items():
            try:
                instance = GameInstance(
                    instance_id=instance_id,
                    path=Path(data['path']),
                    name=data['name'],
                    type=data['type']
                )
                loaded_instances.append(instance)
                self.loaded_game_instances[instance_id] = instance
            except Exception as e:
                print(f"Error loading game instance {data['path']}: {e}")

        frame_to_select: Optional[ttk.Frame] = None
        id_to_select: Optional[str] = self.selected_instance_id

        for instance in loaded_instances:
            item_frame = self._add_client_entry(instance)
            if instance.instance_id == id_to_select:
                frame_to_select = item_frame

        if frame_to_select and id_to_select:
            self._on_client_select(frame_to_select, id_to_select)

    def get_selected_game_instance(self) -> Optional[GameInstance]:
        if not self.selected_instance_id:
            return None
        return self.loaded_game_instances.get(self.selected_instance_id)

    def _add_client_entry(self, instance: GameInstance) -> ttk.Frame:
        """向可滚动框架中添加一个客户端条目"""
        item_frame = ttk.Frame(self.client_list_frame, padding=(5, 5), style="TFrame")
        item_frame.pack(fill='x', expand=True)

        check_var = tk.BooleanVar()
        checkbutton = ttk.Checkbutton(item_frame, variable=check_var, command=self._update_select_all_state)
        checkbutton.pack(side='left', padx=(0, 10), anchor='center')

        item_frame.check_var = check_var
        self.client_check_vars.append(check_var)

        text_frame = ttk.Frame(item_frame, style="TFrame", cursor="hand2")
        text_frame.pack(side='left', fill='x', expand=True)

        name_label_text = f"{_('lki.game.name_label')} {instance.name}"
        name_label = ttk.Label(text_frame, text=name_label_text, style="Client.TLabel", cursor="hand2")
        name_label.pack(anchor='w', fill='x')

        path_label_text = f"{_('lki.game.path_label')} {str(instance.path)}"
        path_label = ttk.Label(text_frame, text=path_label_text, style="Path.TLabel", wraplength=500, cursor="hand2")
        path_label.pack(anchor='w', fill='x')

        type_key = f"lki.game.client_type.{instance.type}"
        type_text = _(type_key)
        type_info_text = f"{_('lki.game.type_label')} {type_text}"
        type_info_label = ttk.Label(text_frame, text=type_info_text, style="Path.TLabel", cursor="hand2")
        type_info_label.pack(anchor='w', fill='x')

        versions_to_display = instance.versions[:2]

        def on_click(event, frame=item_frame, id=instance.instance_id):
            self._on_client_select(frame, id)

        text_frame.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        path_label.bind("<Button-1>", on_click)
        type_info_label.bind("<Button-1>", on_click)

        self._bind_mousewheel(item_frame)
        self._bind_mousewheel(checkbutton)
        self._bind_mousewheel(text_frame)
        self._bind_mousewheel(name_label)
        self._bind_mousewheel(path_label)
        self._bind_mousewheel(type_info_label)

        if not versions_to_display:
            status_text = _('lki.game.version_not_found')
            status_label = ttk.Label(text_frame, text=status_text, style="Path.TLabel", cursor="hand2")
            status_label.pack(anchor='w', fill='x')
            status_label.bind("<Button-1>", on_click)
            self._bind_mousewheel(status_label)
        else:
            for game_version in versions_to_display:
                ver_str = game_version.exe_version or _('lki.game.version_unknown')
                status_text = f"{_('lki.game.version_label')} {ver_str}"

                if game_version.l10n_info:
                    l10n_ver_full = game_version.l10n_info.version
                    l10n_ver_sub = game_version.l10n_info.l10n_sub_version
                    l10n_lang_code = game_version.l10n_info.lang_code

                    # (使用完整语言名称)
                    l10n_lang_name = self.l10n_id_to_name.get(l10n_lang_code, l10n_lang_code)
                    lang_str = f"{l10n_lang_name} " if l10n_lang_code else ""

                    if l10n_ver_full == "INACTIVE":
                        l10n_details = f"{_('lki.game.l10n_status.inactive')}"
                    elif game_version.verify_files():
                        display_ver = l10n_ver_sub if l10n_ver_sub else l10n_ver_full
                        l10n_details = f"{lang_str}{display_ver} - {_('lki.game.l10n_status.ok')}"
                    else:
                        display_ver = l10n_ver_sub if l10n_ver_sub else l10n_ver_full
                        l10n_details = f"{lang_str}{display_ver} - {_('lki.game.l10n_status.corrupted')}"

                    status_text += f" | {l10n_details}"  # (移除了破折号)
                else:
                    status_text += f"{_('lki.game.l10n_status.not_installed')}"

                status_label = ttk.Label(text_frame, text=status_text, style="Path.TLabel", cursor="hand2")
                status_label.pack(anchor='w', fill='x')
                status_label.bind("<Button-1>", on_click)
                self._bind_mousewheel(status_label)

        item_frame.type_label = name_label
        item_frame.path_label = path_label
        item_frame.text_frame = text_frame

        separator = ttk.Separator(self.client_list_frame, orient='horizontal')
        separator.pack(fill='x', expand=True, padx=5, pady=2)

        return item_frame

    def _on_client_select(self, selected_frame, selected_id):
        """处理客户端条目的点击（选择）事件"""

        if self.selected_client_widget and self.selected_client_widget != selected_frame:
            try:
                self.selected_client_widget.text_frame.config(style="TFrame")
                for child in self.selected_client_widget.text_frame.winfo_children():
                    if isinstance(child, ttk.Label):
                        if child == self.selected_client_widget.type_label:
                            child.config(style="Client.TLabel")
                        else:
                            child.config(style="Path.TLabel")
            except tk.TclError:
                print("Warning: Failed to de-select destroyed widget. Resetting selection.")
                self.selected_client_widget = None

        selected_frame.text_frame.config(style="Selected.TFrame")
        for child in selected_frame.text_frame.winfo_children():
            if isinstance(child, ttk.Label):
                if child == selected_frame.type_label:
                    child.config(style="Selected.Client.TLabel")
                else:
                    child.config(style="Selected.Path.TLabel")

        self.selected_client_widget = selected_frame
        self.selected_instance_id = selected_id

        print(f"Selected instance ID: {self.selected_instance_id}")

        self.btn_rename.config(state='normal')
        self.btn_remove.config(state='normal')
        self.btn_open_folder.config(state='normal')

        keys = list(self.game_instances.keys())
        try:
            index = keys.index(selected_id)
        except ValueError:
            index = -1

        self.btn_move_up.config(state='normal' if index > 0 else 'disabled')
        self.btn_move_down.config(state='normal' if index != -1 and index < (len(keys) - 1) else 'disabled')

        self.on_instance_select_callback(self.get_selected_game_instance())

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.client_list_window, width=canvas_width)

    def _on_select_all(self):
        if 'alternate' in self.check_all_btn.state():
            new_state = True
            self.select_all_var.set(True)
        else:
            new_state = self.select_all_var.get()
        self.check_all_btn.state(['!alternate'])
        for var in self.client_check_vars:
            var.set(new_state)

    def _update_select_all_state(self):
        if not self.client_check_vars:
            return
        states = [var.get() for var in self.client_check_vars]
        if all(states):
            self.select_all_var.set(True)
            self.check_all_btn.state(['!alternate'])
        elif not any(states):
            self.select_all_var.set(False)
            self.check_all_btn.state(['!alternate'])
        else:
            self.select_all_var.set(False)
            self.check_all_btn.state(['alternate'])

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)

    def update_icons(self):
        """当主题更改时更新此选项卡上的图标"""
        self.btn_import.config(image=self.icons.import_icon)
        self.btn_rename.config(image=self.icons.rename)
        self.btn_remove.config(image=self.icons.remove)
        self.btn_auto_import.config(image=self.icons.auto_import_icon)
        self.btn_move_up.config(image=self.icons.up)
        self.btn_move_down.config(image=self.icons.down)
        self.btn_open_folder.config(image=self.icons.folder)

    def _clear_selection_and_refresh(self):
        """内部助手，用于清除选择、刷新列表并通知 App"""
        self.selected_instance_id = None
        self.selected_client_widget = None
        self.loaded_game_instances.clear()
        self._refresh_client_list()
        self.on_instance_select_callback(None)
        self.btn_rename.config(state='disabled')
        self.btn_remove.config(state='disabled')
        self.btn_move_up.config(state='disabled')
        self.btn_move_down.config(state='disabled')
        self.btn_open_folder.config(state='disabled')

    def _on_auto_import(self, is_initial_run=False):
        """Kicks off the instance detection in a new thread."""
        self.btn_auto_import.config(state='disabled')

        if not is_initial_run:
            self._clear_selection_and_refresh()

        threading.Thread(target=self._run_auto_import_thread, args=(is_initial_run,), daemon=True).start()

    def _run_auto_import_thread(self, is_initial_run):
        """在单独的线程中运行以避免冻结 UI。"""
        try:
            found_instances = find_instances_for_auto_import()
            new_count = 0

            if not found_instances and not is_initial_run:
                self.app_master.after(0, messagebox.showinfo,
                                      _('lki.game.detected_clients'),
                                      _('lki.detect.none_found'))
                self.app_master.after(0, self.btn_auto_import.config, {'state': 'normal'})
                return

            current_ui_lang = settings.global_settings.language

            used_live_nums = set()
            used_pt_nums = set()
            for instance in self.instance_manager.get_all().values():
                name = instance.get('name', '')
                if name.startswith('MKLive-'):
                    num_str = name.split('-')[-1]
                    if num_str.isdigit():
                        used_live_nums.add(int(num_str))
                elif name.startswith('MKPT-'):
                    num_str = name.split('-')[-1]
                    if num_str.isdigit():
                        used_pt_nums.add(int(num_str))

            live_counter = 1
            pt_counter = 1

            for path, type_code in found_instances:
                instance_id = self.instance_manager._generate_id(path)
                if instance_id not in self.game_instances:

                    if type_code == 'production':
                        while live_counter in used_live_nums:
                            live_counter += 1
                        name = f"MKLive-{live_counter}"
                        used_live_nums.add(live_counter)
                        live_counter += 1
                    else:
                        while pt_counter in used_pt_nums:
                            pt_counter += 1
                        name = f"MKPT-{pt_counter}"
                        used_pt_nums.add(pt_counter)
                        pt_counter += 1

                    self.instance_manager.add_instance(name, path, type_code, current_ui_lang)
                    new_count += 1

            self.app_master.after(0, self._auto_import_finished, new_count, is_initial_run)

        except Exception as e:
            print(f"Error during instance detection thread: {e}")
            if not is_initial_run:
                self.app_master.after(0, messagebox.showerror,
                                      _('lki.game.detected_clients'),
                                      f"An error occurred: {e}")
            self.app_master.after(0, self.btn_auto_import.config, {'state': 'normal'})

    def _auto_import_finished(self, new_count: int, is_initial_run: bool):
        """在检测线程完成后由主线程调用。"""
        self.btn_auto_import.config(state='normal')

        if not is_initial_run:
            if new_count > 0:
                messagebox.showinfo(
                    _('lki.game.detected_clients'),
                    _('lki.detect.found_new') % new_count
                )
            else:
                messagebox.showinfo(
                    _('lki.game.detected_clients'),
                    _('lki.detect.no_new')
                )

        self._clear_selection_and_refresh()

    # --- (新增：安装逻辑) ---
    def _on_install_clicked(self):
        """收集勾选的任务并启动安装管理器。"""
        tasks_to_run: List[InstallationTask] = []

        # 1. 收集勾选的实例
        checked_instance_ids = []
        for i, check_var in enumerate(self.client_check_vars):
            if check_var.get():
                try:
                    # (这是一个脆弱的假设，但它是目前最简单的方法)
                    instance_id = list(self.game_instances.keys())[i]
                    checked_instance_ids.append(instance_id)
                except IndexError:
                    pass  # (不应发生)

        if not checked_instance_ids:
            messagebox.showwarning(_('lki.game.btn.install_selected'), _('lki.install.error.no_instances_selected'))
            return

        # 2. 为每个实例创建任务
        for instance_id in checked_instance_ids:
            instance = self.loaded_game_instances.get(instance_id)
            instance_data = self.instance_manager.get_instance(instance_id)

            if not instance or not instance_data:
                messagebox.showerror("Error", f"Could not find data for instance {instance_id}")
                continue

            if not instance.versions:
                messagebox.showwarning(_('lki.game.btn.install_selected'),
                                       _('lki.install.error.no_version_for_instance') % instance.name)
                continue

            active_preset_id = instance_data.get('active_preset_id', 'default')
            preset_data = instance_data.get('presets', {}).get(active_preset_id)

            if not preset_data:
                messagebox.showerror("Error", f"Could not find preset {active_preset_id} for instance {instance.name}")
                continue

            # (为预设添加一个可显示的名称)
            preset_data['name'] = _(preset_data.get('name_key')) if preset_data.get('is_default') else preset_data.get(
                'name')

            tasks_to_run.append(InstallationTask(instance, preset_data, self.app_master))

        # 3. 启动管理器
        if tasks_to_run:
            self.installation_manager.start_installation(tasks_to_run, self._on_installation_complete)

    def _on_installation_complete(self):
        """
        由 InstallationManager 在所有任务完成后调用的回调。
        刷新游戏列表以显示新的安装状态。
        """
        print("Installation complete. Refreshing game list...")
        self._clear_selection_and_refresh()

    # --- (回调) ---
    def _open_import_instance_window(self):
        """打开“导入实例”窗口"""
        window = ImportInstanceWindow(self.app_master, self.type_id_to_name, self._on_import_instance_save)

    def _on_import_instance_save(self, name: str, path: str, type_code: str):
        """“导入实例”窗口的保存回调"""
        current_ui_lang = settings.global_settings.language
        new_id = self.instance_manager.add_instance(name, path, type_code, current_ui_lang)

        messagebox.showinfo(
            _('lki.add_instance.title'),
            _('lki.add_instance.success') % name,
            parent=self.app_master
        )
        self._clear_selection_and_refresh()

    def _open_edit_instance_window(self):
        """打开“编辑实例”窗口"""
        if not self.selected_instance_id:
            return

        instance_data = self.instance_manager.get_instance(self.selected_instance_id)
        if not instance_data:
            return

        current_name = instance_data.get('name')
        current_preset_id = instance_data.get('active_preset_id', 'default')
        current_type = instance_data.get('type', 'production')

        presets_dict = instance_data.get('presets', {})
        preset_id_to_display_name = {}
        for preset_id, data in presets_dict.items():
            if data.get('is_default'):
                display_name = _(data["name_key"])
            else:
                display_name = data.get("name", f"Preset {preset_id}")
            preset_id_to_display_name[preset_id] = display_name

        window = EditInstanceWindow(
            self.app_master,
            self.selected_instance_id,
            current_name,
            current_type,
            current_preset_id,
            self.type_id_to_name,
            preset_id_to_display_name,
            self._on_edit_instance_save
        )

    def _on_edit_instance_save(self, instance_id: str, new_name: str, new_type_code: str, new_preset_id: str):
        """“编辑实例”窗口的保存回调"""
        self.instance_manager.update_instance_data(instance_id, {
            'name': new_name,
            'type': new_type_code,
            'active_preset_id': new_preset_id
        })
        self._clear_selection_and_refresh()

    def _open_delete_instance_window(self):
        """打开“删除实例”窗口"""
        if not self.selected_instance_id:
            return

        instance_data = self.instance_manager.get_instance(self.selected_instance_id)
        if not instance_data:
            return

        instance_name = instance_data.get('name')
        window = DeleteInstanceWindow(
            self.app_master,
            self.selected_instance_id,
            instance_name,
            self.icons,
            self._on_delete_instance_confirm
        )

    def _on_delete_instance_confirm(self, instance_id: str, instance_name: str):
        """“移除实例”窗口的回调"""
        self.instance_manager.delete_instance(instance_id)

        messagebox.showinfo(
            _('lki.delete_instance.title'),
            _('lki.delete_instance.success') % instance_name,
            parent=self.app_master
        )
        self._clear_selection_and_refresh()

    def _open_instance_folder(self):
        """打开所选实例的根文件夹"""
        if not self.selected_instance_id:
            return
        instance_data = self.instance_manager.get_instance(self.selected_instance_id)
        if not instance_data:
            return

        path = instance_data.get('path')
        if not path:
            return

        try:
            os.startfile(path)
        except AttributeError:
            try:
                subprocess.run(['explorer', os.path.normpath(path)])
            except Exception as e:
                print(f"Error opening folder: {e}")
                webbrowser.open(f'file:///{path}')

    def _move_instance_up(self):
        """将所选实例上移"""
        if not self.selected_instance_id:
            return
        self.instance_manager.move_instance_up(self.selected_instance_id)
        self._refresh_client_list()

    def _move_instance_down(self):
        """将所选实例下移"""
        if not self.selected_instance_id:
            return
        self.instance_manager.move_instance_down(self.selected_instance_id)
        self._refresh_client_list()


# --- (从 ui_windows.py 移来的类) ---

class ImportInstanceWindow(tk.Toplevel):
    """一个用于导入新游戏实例的弹出窗口。"""

    def __init__(self, parent, type_map, on_save_callback):
        super().__init__(parent)
        self.title(_('lki.add_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.type_map = type_map
        self.type_name_to_id = {v: k for k, v in self.type_map.items()}
        self.on_save_callback = on_save_callback

        self.name_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.type_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # 1. 名称
        ttk.Label(main_frame, text=_('lki.add_instance.name')).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky='we', pady=5)
        name_entry.focus_set()

        # 2. 路径
        ttk.Label(main_frame, text=_('lki.add_instance.path')).grid(row=1, column=0, sticky='e', padx=(0, 10), pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=1, sticky='we', pady=5)
        path_frame.columnconfigure(0, weight=1)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=0, sticky='we')
        browse_btn = ttk.Button(path_frame, text=_('lki.add_instance.btn.browse'), command=self._on_browse)
        browse_btn.grid(row=0, column=1, sticky='w', padx=(5, 0))

        # 3. 类型
        ttk.Label(main_frame, text=_('lki.add_instance.type')).grid(row=2, column=0, sticky='e', padx=(0, 10), pady=5)
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=list(self.type_map.values()),
                                       state='disabled')
        self.type_combo.grid(row=2, column=1, sticky='we', pady=5)

        # 4. 状态标签
        self.status_label = ttk.Label(main_frame, text="", wraplength=300)
        self.status_label.grid(row=3, column=1, sticky='we', pady=(0, 5), padx=5)

        # 5. 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=4, column=0, columnspan=2, sticky='e')
        self.save_btn = ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save, state='disabled')
        self.save_btn.pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        # 6. 绑定
        self.name_var.trace_add('write', self._check_button_state)
        self.path_var.trace_add('write', self._on_path_changed)

    def _on_browse(self):
        directory = filedialog.askdirectory(parent=self)
        if directory:
            self.path_var.set(os.path.normpath(directory))

    def _on_path_changed(self, *args):
        """当路径文本框变化时调用"""
        path_str = self.path_var.get().strip()

        if not path_str:
            self.status_label.config(text="")
            self.type_var.set("")
            self.type_combo.config(state='disabled')
            self._check_button_state()
            return

        self.status_label.config(text=_('lki.add_instance.status.checking'), foreground='gray')
        self.master.update_idletasks()

        p = Path(path_str)

        type_code = get_instance_type_from_path(p)

        if type_code:
            type_name = self.type_map.get(type_code)
            self.type_var.set(type_name)
            self.status_label.config(text=_('lki.add_instance.status.detected') % type_name, foreground='green')
            self.type_combo.config(state='disabled')
        else:
            self.type_var.set("")
            self.status_label.config(text=_('lki.add_instance.error.invalid_path'), foreground='red')
            self.type_combo.config(state='disabled')

        self._check_button_state()

    def _check_button_state(self, *args):
        """检查名称和类型是否都有效，以启用保存按钮"""
        name_ok = self.name_var.get().strip()
        type_ok = self.type_var.get()

        if name_ok and type_ok:
            self.save_btn.config(state='normal')
        else:
            self.save_btn.config(state='disabled')

    def _on_save(self):
        name = self.name_var.get().strip()
        path_str = self.path_var.get().strip()
        type_name = self.type_var.get()

        instance_id = instance_manager.global_instance_manager._generate_id(path_str)
        if instance_id in instance_manager.global_instance_manager.instances:
            messagebox.showerror(_('lki.add_instance.title'), _('lki.add_instance.error.path_exists'), parent=self)
            return

        type_code = self.type_name_to_id.get(type_name)

        self.on_save_callback(name, path_str, type_code)
        self.destroy()


class EditInstanceWindow(tk.Toplevel):
    """一个用于编辑实例名称、类型和活动预设的弹出窗口。"""

    def __init__(self, parent, instance_id, current_name, current_type, current_preset_id,
                 type_map, preset_map, on_save_callback):
        super().__init__(parent)
        self.title(_('lki.edit_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.instance_id = instance_id
        self.current_type_code = current_type
        self.type_map = type_map
        self.type_name_to_id = {v: k for k, v in self.type_map.items()}
        self.preset_id_to_name = preset_map
        self.preset_name_to_id = {v: k for k, v in self.preset_id_to_name.items()}
        self.on_save_callback = on_save_callback

        self.name_var = tk.StringVar(value=current_name)
        self.type_var = tk.StringVar(value=self.type_map.get(current_type))
        self.preset_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(1, weight=1)

        # 1. 名称
        ttk.Label(main_frame, text=_('lki.edit_instance.name')).grid(row=0, column=0, sticky='e', padx=(0, 10), pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky='we', pady=5)
        name_entry.focus_set()

        # 2. 实例类型
        ttk.Label(main_frame, text=_('lki.add_instance.type')).grid(row=1, column=0, sticky='e', padx=(0, 10), pady=5)
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var,
                                  values=list(self.type_map.values()), state='readonly')
        type_combo.grid(row=1, column=1, sticky='we', pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)

        # 3. 活动预设
        ttk.Label(main_frame, text=_('lki.edit_instance.active_preset')).grid(row=2, column=0, sticky='e', padx=(0, 10),
                                                                              pady=5)
        preset_combo = ttk.Combobox(main_frame, textvariable=self.preset_var,
                                    values=list(self.preset_id_to_name.values()), state='readonly')
        preset_combo.grid(row=2, column=1, sticky='we', pady=5)

        current_preset_name = self.preset_id_to_name.get(current_preset_id, "")
        if current_preset_name:
            preset_combo.set(current_preset_name)

        # 4. 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=3, column=0, columnspan=2, sticky='e')
        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

    def _on_type_changed(self, event=None):
        """当实例类型下拉框被更改时调用。"""
        new_type_name = self.type_var.get()
        new_type_code = self.type_name_to_id.get(new_type_name)

        if not new_type_code or new_type_code == self.current_type_code:
            return

        confirm_text = _('lki.advanced.confirm_type_change') % new_type_name
        if messagebox.askyesno(_('lki.app.title'), confirm_text, parent=self):
            self.current_type_code = new_type_code
        else:
            current_type_name = self.type_map.get(self.current_type_code)
            self.type_var.set(current_type_name)

    def _on_save(self):
        new_name = self.name_var.get().strip()
        new_type_name = self.type_var.get()
        new_preset_name = self.preset_var.get()

        if not new_name or not new_preset_name or not new_type_name:
            return

        new_type_code = self.type_name_to_id.get(new_type_name)
        new_preset_id = self.preset_name_to_id.get(new_preset_name)

        if not new_preset_id or not new_type_code:
            return

        self.on_save_callback(self.instance_id, new_name, new_type_code, new_preset_id)
        self.destroy()


class DeleteInstanceWindow(tk.Toplevel):
    """一个要求输入名称以确认删除的弹出窗口。"""

    def __init__(self, parent, instance_id, instance_name, icons, on_delete_callback):
        super().__init__(parent)
        self.title(_('lki.delete_instance.title'))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.instance_id = instance_id
        self.instance_name = instance_name
        self.icons = icons
        self.on_delete_callback = on_delete_callback

        self.confirm_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)

        prompt_label = ttk.Label(main_frame, text=_('lki.delete_instance.prompt'), wraplength=350)
        prompt_label.grid(row=0, column=0, sticky='w', pady=(0, 10))

        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=1, column=0, sticky='we', pady=5)

        name_label = ttk.Label(name_frame, text=self.instance_name, style="Client.TLabel")
        name_label.pack(side='left', anchor='w')

        copy_btn = ttk.Button(name_frame, image=self.icons.copy, style="Toolbutton", command=self._copy_name)
        copy_btn.pack(side='left', padx=(5, 0))

        confirm_label = ttk.Label(main_frame, text=_('lki.delete_instance.confirm_label'))
        confirm_label.grid(row=2, column=0, sticky='w', pady=(10, 5))

        self.confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var)
        self.confirm_entry.grid(row=3, column=0, sticky='we')
        self.confirm_entry.focus_set()

        # 按钮
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=4, column=0, sticky='e', pady=(10, 0))

        self.delete_btn = ttk.Button(button_frame, text=_('lki.btn.remove_instance'), command=self._on_delete,
                                     style="danger.TButton")
        self.delete_btn.pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        self.delete_btn.config(state='disabled')
        self.confirm_var.trace_add('write', self._validate_name)
        self.confirm_entry.bind("<Return>", self._on_delete)

    def _validate_name(self, *args):
        entered_name = self.confirm_var.get()
        if entered_name == self.instance_name:
            self.delete_btn.config(state='normal')
        else:
            self.delete_btn.config(state='disabled')

    def _copy_name(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.instance_name)
        except Exception as e:
            print(f"Clipboard error: {e}")

    def _on_delete(self, event=None):
        if self.delete_btn.cget('state') == 'disabled':
            return

        entered_name = self.confirm_var.get()
        if entered_name == self.instance_name:
            self.on_delete_callback(self.instance_id, self.instance_name)
            self.destroy()
        else:
            messagebox.showerror(_('lki.delete_instance.title'), _('lki.delete_instance.error.mismatch'), parent=self)