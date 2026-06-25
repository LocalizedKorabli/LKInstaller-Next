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
import os  # (新增)
import sys  # (新增)
import tkinter as tk
from pathlib import Path  # (新增)
from tkinter import ttk, messagebox, filedialog  # (已修改)
from typing import List, Callable, Optional, Dict, Set

from tktooltip import ToolTip

from core import dirs
from core import utils
from core.scheduler import SchedulerBackend, DAYS_OF_WEEK_SHORT, build_autoexec_args
from installation.localization_sources import get_route_id_to_name
from core.localizer import _

TRIGGER_TYPES = [
    ('once', 'lki.autoupdate.schedule.once'),
    ('daily', 'lki.autoupdate.schedule.daily'),
    ('weekly', 'lki.autoupdate.schedule.weekly'),
    ('at_logon', 'lki.autoupdate.schedule.at_logon'),
    ('at_startup', 'lki.autoupdate.schedule.at_startup'),
    ('on_idle', 'lki.autoupdate.schedule.on_idle'),
]

WEEKDAY_LABELS = {
    'mon': 'lki.autoupdate.schedule.mon',
    'tue': 'lki.autoupdate.schedule.tue',
    'wed': 'lki.autoupdate.schedule.wed',
    'thu': 'lki.autoupdate.schedule.thu',
    'fri': 'lki.autoupdate.schedule.fri',
    'sat': 'lki.autoupdate.schedule.sat',
    'sun': 'lki.autoupdate.schedule.sun',
}




class TimePicker(ttk.Frame):
    """一个由两个 Spinbox（时:分）组成的时间选择器组件。"""

    def __init__(self, master, initial: str = "08:00", on_change: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)

        try:
            h, m = initial.strip().split(":")
            h_val, m_val = int(h), int(m)
        except (ValueError, AttributeError):
            h_val, m_val = 8, 0

        self._hour_var = tk.StringVar(value=f"{h_val:02d}")
        self._min_var = tk.StringVar(value=f"{m_val:02d}")
        self._on_change = on_change
        if on_change:
            self._hour_var.trace_add('write', lambda *_: on_change())
            self._min_var.trace_add('write', lambda *_: on_change())

        def _on_hour_focusout(*_):
            raw = self._hour_var.get().strip()
            try:
                val = int(raw)
            except ValueError:
                val = 0
            if val < 0: val = 0
            elif val > 23: val = 23
            self._hour_var.set(f"{val:02d}")

        def _on_min_focusout(*_):
            raw = self._min_var.get().strip()
            try:
                val = int(raw)
            except ValueError:
                val = 0
            if val < 0: val = 0
            elif val > 59: val = 59
            self._min_var.set(f"{val:02d}")

        hour_spin = ttk.Spinbox(
            self, from_=0, to=23, textvariable=self._hour_var,
            width=4, justify='left', wrap=True
        )
        hour_spin.pack(side='left')
        hour_spin.bind('<FocusIn>', lambda e: hour_spin.selection_range(0, 'end'))
        hour_spin.bind('<ButtonRelease-1>', lambda e: hour_spin.selection_range(0, 'end'))
        hour_spin.bind('<FocusOut>', _on_hour_focusout)

        ttk.Label(self, text=":", font=("TkDefaultFont", 11, "bold")).pack(side='left', padx=2)

        min_spin = ttk.Spinbox(
            self, from_=0, to=59, textvariable=self._min_var,
            width=4, justify='left', wrap=True
        )
        min_spin.pack(side='left')
        min_spin.bind('<FocusIn>', lambda e: min_spin.selection_range(0, 'end'))
        min_spin.bind('<ButtonRelease-1>', lambda e: min_spin.selection_range(0, 'end'))
        min_spin.bind('<FocusOut>', _on_min_focusout)

    def get(self) -> str:
        """返回 'HH:MM' 格式的时间字符串。"""
        return f"{self._hour_var.get()}:{self._min_var.get()}"

    def set(self, time_str: str):
        """从 'HH:MM' 字符串设置时间。"""
        try:
            h, m = time_str.strip().split(":")
            self._hour_var.set(f"{int(h):02d}")
            self._min_var.set(f"{int(m):02d}")
        except (ValueError, AttributeError):
            pass




class DatePicker(ttk.Frame):
    """一个使用 tkcalendar.DateEntry 的日期选择组件。"""

    def __init__(self, master, initial: str = "", on_change: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        from tkcalendar import DateEntry
        import datetime
        today = datetime.date.today()
        if initial:
            try:
                parts = initial.split("-")
                dt = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                dt = today
        else:
            dt = today
        self._entry = DateEntry(self, date_pattern='yyyy-mm-dd', width=12,
                                year=dt.year, month=dt.month, day=dt.day)
        self._entry.pack(side='left')
        if on_change:
            self._entry.bind('<<DateEntrySelected>>', lambda e: on_change())
            # 也响应键盘输入
            self._entry.bind('<KeyRelease>', lambda e: on_change())

    def get(self) -> str:
        """返回 'YYYY-MM-DD' 格式的日期字符串。"""
        return self._entry.get()

    def set(self, date_str: str):
        """从 'YYYY-MM-DD' 字符串设置日期。"""
        try:
            import datetime
            parts = date_str.strip().split("-")
            self._entry.set_date(datetime.date(int(parts[0]), int(parts[1]), int(parts[2])))
        except (ValueError, IndexError):
            pass


class BaseDialog(tk.Toplevel):
    """
    一个会自动在屏幕上居中的 Toplevel 弹窗基类。
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()  # 防止在左上角闪烁
        if parent and parent.winfo_exists() and parent.state() == 'normal':
            self.transient(parent)  # 保持在父窗口之上
        self.grab_set()  # 设为模态窗口
        # 我们使用 .after() 来确保窗口大小已被计算
        self.after(50, self._center_on_screen)

    def _center_on_screen(self):
        """将窗口移动到屏幕中央。"""
        try:
            self.update_idletasks()  # 确保 winfo_width/height 是准确的

            # 屏幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # 窗口尺寸
            window_width = self.winfo_width()
            window_height = self.winfo_height()

            # 计算位置
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)

            self.geometry(f"+{x}+{y}")
            self.deiconify()
        except tk.Toplevel:
            pass  # 窗口可能在居中之前被销毁


class CustomAskStringDialog(BaseDialog):  # <-- 继承 BaseDialog
    def __init__(self, parent, title, prompt, initialvalue=""):
        super().__init__(parent)  # <-- 调用 BaseDialog 的 __init__
        self.title(title)

        self.result = None

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text=prompt, wraplength=utils.scale_dpi(self, 300)).pack(fill='x', pady=(0, 10))

        self.entry = ttk.Entry(main_frame)
        self.entry.insert(0, initialvalue)
        self.entry.pack(fill='x', expand=True)
        self.entry.focus_set()

        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill='x', expand=True, side='bottom')

        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self._on_cancel).pack(side='right', padx=5)

        self.entry.bind("<Return>", self._on_save)
        self.bind("<Escape>", self._on_cancel)
        self.resizable(False, False)

    def _on_save(self, event=None):
        self.result = self.entry.get()
        self.destroy()

    def _on_cancel(self, event=None):
        self.result = None
        self.destroy()

    def get_result(self):
        """
        等待窗口关闭并返回结果。
        """
        self.wait_window()
        return self.result


class TriggerConfigDialog(BaseDialog):
    """新建计划任务的配置弹窗：实例/预设/触发条件在一个独立窗口中配置。"""

    def __init__(self, parent, mgr, scheduler, instance_id: str, preset_id: str,
                 initial_task_name: str = ""):
        super().__init__(parent)
        self.title(_('lki.autoupdate.schedule.btn.create'))
        self.resizable(False, False)
        self._mgr = mgr
        self._scheduler = scheduler

        # 实例/预设数据
        all_instances = mgr.get_all()
        self._name_to_iid = {d['name']: iid for iid, d in all_instances.items()}
        instance_names = list(self._name_to_iid.keys())
        instance_name = next((n for n, i in self._name_to_iid.items() if i == instance_id), instance_names[0] if instance_names else '')
        self._instance_var = tk.StringVar(value=instance_name)

        self._preset_name_to_id: dict = {}
        self._preset_var = tk.StringVar()
        self._selected_instance_id = instance_id
        self._selected_preset_id = preset_id

        self._run_client_var = tk.BooleanVar(value=True)

        # 任务名称：编辑时预填旧名称，新建时自动生成
        self._task_name_var = tk.StringVar(value=initial_task_name)
        self._initial_task_name = initial_task_name
        self._user_edited_name = bool(initial_task_name)  # 有初始值说明是编辑模式

        # 触发类型变量
        self._trigger_type_var = tk.StringVar(value='daily')
        self._time_picker: Optional[TimePicker] = None
        self._date_picker: Optional[DatePicker] = None  # 用于 'once' 触发类型
        self._trigger_idle_var = tk.IntVar(value=10)
        self._trigger_days_vars: Dict[str, tk.BooleanVar] = {}

        # ── 布局 ──
        main = ttk.Frame(self, padding=15)
        main.pack(fill='both', expand=True)
        main.columnconfigure(1, weight=1)

        row = 0
        # 实例
        ttk.Label(main, text=_('lki.autoupdate.instance_label')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=3)
        inst_combo = ttk.Combobox(main, textvariable=self._instance_var,
                                   values=instance_names, state='readonly', width=40)
        inst_combo.grid(row=row, column=1, sticky='we', pady=3)
        inst_combo.bind('<<ComboboxSelected>>', self._on_instance_changed)
        row += 1

        # 预设
        ttk.Label(main, text=_('lki.autoupdate.preset_label')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=3)
        self._preset_combo = ttk.Combobox(main, textvariable=self._preset_var,
                                           state='readonly', width=40)
        self._preset_combo.grid(row=row, column=1, sticky='we', pady=3)
        self._preset_combo.bind('<<ComboboxSelected>>', self._on_preset_changed)
        self._populate_presets(self._selected_instance_id, self._selected_preset_id)
        row += 1

        # 任务名称
        ttk.Label(main, text=_('lki.autoupdate.schedule.task_name')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=3)
        name_frame = ttk.Frame(main)
        name_frame.grid(row=row, column=1, sticky='we', pady=3)
        name_frame.columnconfigure(0, weight=1)
        self._prefix_var = tk.StringVar(value=_('lki.autoupdate.schedule.default_name'))
        prefix_entry = ttk.Entry(name_frame, textvariable=self._prefix_var, width=40)
        prefix_entry.grid(row=0, column=0, sticky='we')
        prefix_entry.bind('<Key>', lambda e: setattr(self, '_user_edited_name', True))
        default_btn = ttk.Button(name_frame, text=_('lki.autoupdate.schedule.btn.default'),
                                 command=self._reset_to_default_name, width=6)
        default_btn.grid(row=0, column=1, padx=(5, 0))
        # 显示完整任务名预览
        row += 1
        self._full_name_label = ttk.Label(main, text="", foreground='gray')
        self._full_name_label.grid(row=row, column=0, columnspan=2, sticky='w', padx=(10, 0))
        row += 1

        # 是否启动游戏
        ttk.Checkbutton(main, text=_('lki.autoupdate.run_client'),
                        variable=self._run_client_var).grid(
            row=row, column=0, columnspan=2, sticky='w', pady=(3, 8))
        row += 1

        # Separator
        ttk.Separator(main, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='we', pady=(0, 8))
        row += 1

        # 触发类型 + 参数（同一行）
        ttk.Label(main, text=_('lki.autoupdate.schedule.trigger_type')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=5)
        trigger_row = ttk.Frame(main)
        trigger_row.grid(row=row, column=1, sticky='w', pady=5)

        trigger_combo = ttk.Combobox(trigger_row, state='readonly', width=20)
        trigger_names = [_(key) for _code, key in TRIGGER_TYPES]
        trigger_combo.config(values=trigger_names)
        trigger_combo.set(_('lki.autoupdate.schedule.daily'))
        trigger_combo.pack(side='left')
        trigger_combo.bind('<<ComboboxSelected>>', self._on_trigger_type_changed)
        self._trigger_combo = trigger_combo

        self._trigger_params_frame = ttk.Frame(trigger_row)
        self._trigger_params_frame.pack(side='left', padx=(10, 0))
        self._build_trigger_params('daily')
        self._update_default_task_name()
        row += 1

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky='e', pady=(10, 0))
        ttk.Button(btn_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=(5, 0))
        ttk.Button(btn_frame, text=_('lki.autoupdate.schedule.btn.create'),
                   command=self._on_ok).pack(side='right')

        self.minsize(width=460, height=200)

    # ── 实例/预设切换 ──
    def _on_instance_changed(self, _event=None):
        name = self._instance_var.get()
        iid = self._name_to_iid.get(name)
        if not iid:
            return
        self._selected_instance_id = iid
        instance_data = self._mgr.get_instance(iid)
        active_preset = instance_data.get('active_preset_id', 'default') if instance_data else 'default'
        self._populate_presets(iid, active_preset)

    def _on_preset_changed(self, _event=None):
        display = self._preset_var.get()
        self._selected_preset_id = self._preset_name_to_id.get(display, self._selected_preset_id)

    def _populate_presets(self, instance_id: str, default_preset_id: str):
        instance_data = self._mgr.get_instance(instance_id)
        presets = instance_data.get('presets', {}) if instance_data else {}
        self._preset_name_to_id = {}
        for pid, pdata in presets.items():
            if pdata.get('is_default'):
                display = _(pdata.get('name_key', 'lki.preset.default.name'))
            else:
                display = pdata.get('name', pid)
            self._preset_name_to_id[display] = pid
        names = list(self._preset_name_to_id.keys())
        self._preset_combo.config(values=names)
        default_display = next((n for n, pid in self._preset_name_to_id.items() if pid == default_preset_id),
                                names[0] if names else '')
        self._preset_var.set(default_display)
        self._selected_preset_id = self._preset_name_to_id.get(default_display, default_preset_id)

    # ── 触发参数 ──
    def _build_trigger_params(self, trigger_type: str):
        for w in self._trigger_params_frame.winfo_children():
            w.destroy()
        if trigger_type == 'once':
            date_row = ttk.Frame(self._trigger_params_frame)
            date_row.pack(fill='x')
            ttk.Label(date_row, text=_('lki.autoupdate.schedule.date')).pack(side='left', padx=(0, 5))
            self._date_picker = DatePicker(date_row, on_change=self._update_full_name_label)
            self._date_picker.pack(side='left')
            time_row = ttk.Frame(self._trigger_params_frame)
            time_row.pack(fill='x', pady=(3, 0))
            ttk.Label(time_row, text=_('lki.autoupdate.schedule.time')).pack(side='left', padx=(0, 5))
            self._time_picker = TimePicker(time_row, initial='08:00', on_change=self._update_full_name_label)
            self._time_picker.pack(side='left')
        elif trigger_type == 'daily':
            ttk.Label(self._trigger_params_frame, text=_('lki.autoupdate.schedule.time')).pack(side='left', padx=(0, 5))
            self._time_picker = TimePicker(self._trigger_params_frame, initial='08:00', on_change=self._update_full_name_label)
            self._time_picker.pack(side='left')
        elif trigger_type == 'weekly':
            ttk.Label(self._trigger_params_frame, text=_('lki.autoupdate.schedule.days')).pack(side='left', padx=(0, 5))
            day_frame = ttk.Frame(self._trigger_params_frame)
            day_frame.pack(side='left')
            self._trigger_days_vars.clear()
            for code in DAYS_OF_WEEK_SHORT:
                var = tk.BooleanVar(value=(code in ('mon', 'tue', 'wed', 'thu', 'fri')))
                self._trigger_days_vars[code] = var
                cb = ttk.Checkbutton(day_frame, text=_(WEEKDAY_LABELS[code]), variable=var)
                cb.pack(side='left', padx=2)
            ttk.Label(self._trigger_params_frame, text='  ' + _('lki.autoupdate.schedule.time')).pack(side='left', padx=(5, 5))
            self._time_picker = TimePicker(self._trigger_params_frame, initial='08:00', on_change=self._update_full_name_label)
            self._time_picker.pack(side='left')
        elif trigger_type == 'on_idle':
            ttk.Label(self._trigger_params_frame, text=_('lki.autoupdate.schedule.idle_minutes')).pack(side='left', padx=(0, 5))
            ttk.Spinbox(self._trigger_params_frame, from_=1, to=120,
                        textvariable=self._trigger_idle_var, width=5).pack(side='left')

    def _build_full_task_name(self, prefix: str, inst: str, preset: str) -> (str, str):
        """构建完整任务名，返回 (suffix, full_name)。"""
        tt = self._trigger_type_var.get()
        from core.utils import sanitize_task_name

        def _fmt_time(t):
            h, m = t.split(":")
            h = int(h)
            m = int(m)
            tn = _('lki.autoupdate.schedule.trigger_desc.hour_prefix')
            tn2 = _('lki.autoupdate.schedule.trigger_desc.min_suffix')
            if m == 0:
                return f"{h}{tn}"
            return f"{h}{tn}{m}{tn2}"

        if tt == 'once':
            d = self._date_picker.get() if self._date_picker else ""
            t = self._time_picker.get() if self._time_picker else "00:00"
            trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.once')}-{d}-{_fmt_time(t)}"
        elif tt == 'daily':
            t = self._time_picker.get() if self._time_picker else "00:00"
            trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.daily')}-{_fmt_time(t)}"
        elif tt == 'weekly':
            t = self._time_picker.get() if self._time_picker else "00:00"
            days = [code for code, var in self._trigger_days_vars.items() if var.get()]
            day_names = {'mon': _('lki.autoupdate.schedule.mon'), 'tue': _('lki.autoupdate.schedule.tue'),
                        'wed': _('lki.autoupdate.schedule.wed'), 'thu': _('lki.autoupdate.schedule.thu'),
                        'fri': _('lki.autoupdate.schedule.fri'), 'sat': _('lki.autoupdate.schedule.sat'),
                        'sun': _('lki.autoupdate.schedule.sun')}
            ds = "-".join(day_names.get(d, d) for d in days) if days else _('lki.autoupdate.schedule.all')
            trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.weekly')}-{ds}-{_fmt_time(t)}"
        elif tt == 'at_logon':
            trigger_part = _('lki.autoupdate.schedule.trigger_desc.at_logon')
        elif tt == 'at_startup':
            trigger_part = _('lki.autoupdate.schedule.trigger_desc.at_startup')
        elif tt == 'on_idle':
            n = self._trigger_idle_var.get()
            trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.on_idle')}{n}{_('lki.autoupdate.schedule.trigger_desc.min')}"
        else:
            trigger_part = _('lki.autoupdate.schedule.trigger_desc.daily')
        suffix = f"{inst}-{preset}-{trigger_part}"
        full = sanitize_task_name(f"{prefix}-{suffix}")
        return suffix, full

    def _update_full_name_label(self):
        """更新底部的完整任务名预览。"""
        prefix = self._prefix_var.get().strip()
        inst = self._instance_var.get()
        preset = self._preset_var.get()
        _suffix, full = self._build_full_task_name(prefix, inst, preset)
        self._full_name_label.config(text=full)

    def _update_default_task_name(self):
        """触发条件变化后刷新预览。"""
        self._update_full_name_label()

    def _reset_to_default_name(self):
        """恢复默认前缀。"""
        self._user_edited_name = False
        self._prefix_var.set(_('lki.autoupdate.schedule.default_name'))
        self._update_full_name_label()

    def _on_trigger_type_changed(self, event=None):
        display = self._trigger_combo.get()
        type_map = {_(key): t for t, key in TRIGGER_TYPES}
        trigger_type = type_map.get(display, 'daily')
        self._trigger_type_var.set(trigger_type)
        self._build_trigger_params(trigger_type)
        self._update_full_name_label()

    # ── 确定 → 创建任务 ──
    def _on_ok(self):
        instance_id = self._selected_instance_id
        preset_id = self._selected_preset_id
        run_client = self._run_client_var.get()
        trigger_type = self._trigger_type_var.get()
        instance_name = self._instance_var.get()
        preset_name = self._preset_var.get()
        time_str = self._time_picker.get() if self._time_picker else None
        date_str = self._date_picker.get() if self._date_picker else None
        idle_min = self._trigger_idle_var.get()
        days = [code for code, var in self._trigger_days_vars.items() if var.get()] if trigger_type == 'weekly' else None

        # 校验
        if trigger_type == 'weekly' and not days:
            messagebox.showwarning(self.title(), _('lki.autoupdate.schedule.error.no_days'), parent=self)
            return

        # 交给父窗口创建任务
        # 构建任务名：前缀+自动后缀
        prefix = self._prefix_var.get().strip() or _('lki.autoupdate.schedule.default_name')
        _suffix, task_name = self._build_full_task_name(prefix, instance_name, preset_name)
        self.master._on_create_schedule(
            instance_id, preset_id, run_client,
            trigger_type, instance_name, preset_name,
            time_str=time_str, date_str=date_str, days=days, idle_min=idle_min,
            task_name=task_name or None
        )
        self.destroy()


# --- (新增：全局路由排序窗口) ---
class RoutePriorityWindow(BaseDialog):  # <-- 继承 BaseDialog
    def __init__(self, parent, icons,
                 current_routes_ids: List[str],
                 all_routes_masterlist: List[str],
                 on_save_callback: Callable):

        super().__init__(parent)
        self.title(_('lki.routes.title'))
        self.resizable(False, False)

        self.icons = icons
        self.on_save_callback = on_save_callback

        self.route_name_to_id = {v: k for k, v in get_route_id_to_name().items()}

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # --- (路由排序 UI) ---
        route_frame = ttk.Frame(main_frame)
        route_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=5)
        route_frame.columnconfigure(0, weight=1)
        route_frame.rowconfigure(0, weight=1)

        self.route_listbox = tk.Listbox(route_frame, exportselection=False, height=5)
        self.route_listbox.grid(row=0, column=0, sticky='nsew', padx=(5, 0), pady=5)

        route_list_scrollbar = ttk.Scrollbar(route_frame, orient='vertical', command=self.route_listbox.yview)
        route_list_scrollbar.grid(row=0, column=1, sticky='ns', pady=5, padx=(0, 5))
        self.route_listbox.config(yscrollcommand=route_list_scrollbar.set)

        self.route_listbox.bind('<<ListboxSelect>>', self._on_route_listbox_select)

        route_btn_frame = ttk.Frame(route_frame)
        route_btn_frame.grid(row=0, column=2, sticky='ns', pady=5, padx=(0, 5))

        self.btn_route_up = ttk.Button(route_btn_frame, image=self.icons.up, style="Toolbutton",
                                       command=self._move_route_up, state='disabled')
        self.btn_route_up.pack(pady=2)

        self.btn_route_down = ttk.Button(route_btn_frame, image=self.icons.down, style="Toolbutton",
                                         command=self._move_route_down, state='disabled')
        self.btn_route_down.pack(pady=2)

        ToolTip(self.btn_route_up, _('lki.tooltip.route_up'))
        ToolTip(self.btn_route_down, _('lki.tooltip.route_down'))

        ttk.Label(route_frame, text=_('lki.routes.hint'), style="Hint.TLabel", wraplength=utils.scale_dpi(self, 220)) \
            .grid(row=1, column=0, columnspan=3, sticky='w', padx=5, pady=(5, 0))

        # --- (按钮) ---
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=1, column=0, columnspan=2, sticky='e')
        ttk.Button(button_frame, text=_('lki.btn.save'), command=self._on_save).pack(side='right')
        ttk.Button(button_frame, text=_('lki.btn.cancel'), command=self.destroy).pack(side='right', padx=5)

        self._populate_route_listbox(current_routes_ids, all_routes_masterlist)

    def _populate_route_listbox(self, current_routes_ids: List[str], all_routes_masterlist: List[str]):
        """填充路由列表框，确保所有路由都在其中"""
        self.route_listbox.delete(0, 'end')

        final_route_ids = []

        # 1. 按已保存的顺序添加
        for r_id in current_routes_ids:
            if r_id in all_routes_masterlist and r_id not in final_route_ids:
                final_route_ids.append(r_id)

        # 2. 添加任何在 masterlist 中但不在已保存列表中的新路由
        for r_id in all_routes_masterlist:
            if r_id not in final_route_ids:
                final_route_ids.append(r_id)

        # 填充 listbox
        for r_id in final_route_ids:
            name = get_route_id_to_name().get(r_id, r_id)
            self.route_listbox.insert('end', name)

    def _on_route_listbox_select(self, event=None):
        """更新上/下按钮的状态"""
        try:
            idx = self.route_listbox.curselection()[0]
            size = self.route_listbox.size()

            self.btn_route_up.config(state='normal' if idx > 0 else 'disabled')
            self.btn_route_down.config(state='normal' if idx < (size - 1) else 'disabled')

        except IndexError:
            self.btn_route_up.config(state='disabled')
            self.btn_route_down.config(state='disabled')

    def _move_route_up(self):
        try:
            idx = self.route_listbox.curselection()[0]
            if idx == 0:
                return

            text = self.route_listbox.get(idx)
            self.route_listbox.delete(idx)
            self.route_listbox.insert(idx - 1, text)
            self.route_listbox.selection_set(idx - 1)
            self.route_listbox.activate(idx - 1)
            self._on_route_listbox_select()
        except IndexError:
            pass

    def _move_route_down(self):
        try:
            idx = self.route_listbox.curselection()[0]
            if idx == (self.route_listbox.size() - 1):
                return

            text = self.route_listbox.get(idx)
            self.route_listbox.delete(idx)
            self.route_listbox.insert(idx + 1, text)
            self.route_listbox.selection_set(idx + 1)
            self.route_listbox.activate(idx + 1)
            self._on_route_listbox_select()
        except IndexError:
            pass

    def _on_save(self):
        new_routes_names = list(self.route_listbox.get(0, 'end'))
        new_route_ids = [self.route_name_to_id.get(name, 'gitee') for name in new_routes_names]

        self.on_save_callback(new_route_ids)
        self.destroy()
# --- (新增结束) ---


class AutoUpdateConfigDialog(BaseDialog):
    def __init__(self, parent, mgr, instance_id: str, instance_name: str, preset_id: str, preset_name: str):
        super().__init__(parent)
        self.title(_('lki.autoupdate.title'))
        self.resizable(True, True)
        self.minsize(width=520, height=420)

        self._mgr = mgr
        self._scheduler = SchedulerBackend()

        all_instances = mgr.get_all()
        self._instance_name_to_id: dict = {
            data['name']: iid for iid, data in all_instances.items()
        }
        self._instance_names: list = list(self._instance_name_to_id.keys())

        self._selected_instance_id = instance_id
        self._selected_preset_id = preset_id
        self._dialog_instance_name = instance_name  # 供 _build_shortcut_tab 使用

        self._run_client_var = tk.BooleanVar(value=True)

        try:
            import win32com.client as _win32com
        except ImportError:
            _win32com = None
        self._has_win32com = _win32com is not None

        if _win32com:
            shell = _win32com.Dispatch('WScript.Shell')
            self._desktop = Path(shell.SpecialFolders('Desktop'))
        else:
            self._desktop = Path.home() / 'Desktop'
        self.shortcut_path_var = tk.StringVar(
            value=str(self._desktop / self._make_shortcut_name(instance_name, preset_name))
        )

        # ── 主布局：仅有 Notebook ──
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        self._shortcut_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self._shortcut_frame, text=_('lki.autoupdate.shortcut.tab'))
        self._build_shortcut_tab()

        self._schedule_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self._schedule_frame, text=_('lki.autoupdate.schedule.tab'))
        self._build_schedule_tab()

    # ────────────────────────────────
    # 快捷方式标签页
    # ────────────────────────────────
    def _build_shortcut_tab(self):
        f = self._shortcut_frame
        f.columnconfigure(1, weight=1)

        row = 0

        # Row 0: 实例选择
        ttk.Label(f, text=_('lki.autoupdate.instance_label')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=3)
        self._instance_var = tk.StringVar(value=self._dialog_instance_name)
        self._instance_combo = ttk.Combobox(
            f, textvariable=self._instance_var,
            values=self._instance_names, state='readonly', width=40)
        self._instance_combo.grid(row=row, column=1, sticky='we', pady=3)
        self._instance_combo.bind('<<ComboboxSelected>>', self._on_instance_changed)
        row += 1

        # Row 1: 预设选择
        ttk.Label(f, text=_('lki.autoupdate.preset_label')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=3)
        self._preset_var = tk.StringVar()
        self._preset_combo = ttk.Combobox(
            f, textvariable=self._preset_var, state='readonly', width=40)
        self._preset_combo.grid(row=row, column=1, sticky='we', pady=3)
        self._preset_combo.bind('<<ComboboxSelected>>', self._on_preset_changed)
        self._populate_presets(self._selected_instance_id, self._selected_preset_id)
        row += 1

        # Row 2: 共享复选框
        cb_run_client = ttk.Checkbutton(f, text=_('lki.autoupdate.run_client'),
                                        variable=self._run_client_var)
        cb_run_client.grid(row=row, column=0, columnspan=2, sticky='w', pady=(3, 0))
        row += 1

        # Separator
        ttk.Separator(f, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='we', pady=(8, 5))
        row += 1

        # Row 4: 保存位置
        ttk.Label(f, text=_('lki.autoupdate.save_location')).grid(
            row=row, column=0, sticky='e', padx=(0, 10), pady=5)
        path_frame = ttk.Frame(f)
        path_frame.grid(row=row, column=1, sticky='we', pady=5)
        path_frame.columnconfigure(0, weight=1)

        self._shortcut_path_entry = ttk.Entry(path_frame, textvariable=self.shortcut_path_var, width=50)
        self._shortcut_path_entry.grid(row=0, column=0, sticky='we')
        browse_btn = ttk.Button(path_frame, text=_('lki.autoupdate.btn.browse'), command=self._on_browse)
        browse_btn.grid(row=0, column=1, sticky='w', padx=(5, 0))
        row += 1

        # Row 5: 生成快捷方式 按钮
        is_pywin32_ok = self._has_win32com
        self._btn_create_shortcut = ttk.Button(
            f, text=_('lki.autoupdate.shortcut.btn_create'),
            command=self._on_create_shortcut,
            state='normal' if is_pywin32_ok else 'disabled'
        )
        self._btn_create_shortcut.grid(row=row, column=0, columnspan=2, sticky='we', pady=(5, 3))
        row += 1

        # 描述文字
        desc_label = ttk.Label(
            f, text=_('lki.autoupdate.shortcut.description'),
            wraplength=460, foreground='gray', justify='left')
        desc_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(0, 5))

        if not is_pywin32_ok:
            self._shortcut_path_entry.config(state='disabled')
            browse_btn.config(state='disabled')
            ttk.Label(f, text=_('lki.autoupdate.shortcut.pywin32_missing'),
                      foreground='red').grid(row=row + 1, column=0, columnspan=2, sticky='w', pady=2)

    # ────────────────────────────────
    # 计划任务标签页
    # ────────────────────────────────
    def _build_schedule_tab(self):
        f = self._schedule_frame
        f.columnconfigure(1, weight=1)

        row = 0

        # --- Existing Tasks section ---
        ttk.Label(f, text=_('lki.autoupdate.schedule.existing_tasks')).grid(
            row=row, column=0, columnspan=2, sticky='w', pady=(0, 5))
        row += 1

        # Task list (fills remaining space)
        f.rowconfigure(row, weight=1)
        list_frame = ttk.Frame(f)
        list_frame.grid(row=row, column=0, columnspan=2, sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._task_listbox = tk.Listbox(list_frame, height=4, exportselection=False)
        self._task_listbox.grid(row=0, column=0, sticky='nsew')
        task_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self._task_listbox.yview)
        task_scroll.grid(row=0, column=1, sticky='ns')
        self._task_listbox.config(yscrollcommand=task_scroll.set)
        self._task_listbox.bind('<<ListboxSelect>>', self._on_task_select)
        row += 1

        # Task 操作按钮
        task_btn_frame = ttk.Frame(f)
        task_btn_frame.grid(row=row, column=0, columnspan=2, sticky='we', pady=(5, 0))
        self._btn_task_create = ttk.Button(task_btn_frame, text=_('lki.autoupdate.schedule.btn.create'),
                                           command=self._on_open_create_dialog)
        self._btn_task_create.pack(side='left', padx=(0, 5))
        self._btn_task_run = ttk.Button(task_btn_frame, text=_('lki.autoupdate.schedule.btn.run_now'),
                                        command=self._on_run_task_now, state='disabled')
        self._btn_task_run.pack(side='left', padx=(0, 5))
        self._btn_task_toggle = ttk.Button(task_btn_frame, text=_('lki.autoupdate.schedule.btn.disable'),
                                           command=self._on_toggle_task, state='disabled')
        self._btn_task_toggle.pack(side='left', padx=5)
        self._btn_task_edit = ttk.Button(task_btn_frame, text=_('lki.autoupdate.schedule.btn.edit'),
                                         command=self._on_edit_task, state='disabled')
        self._btn_task_edit.pack(side='left', padx=5)
        self._btn_task_delete = ttk.Button(task_btn_frame, text=_('lki.autoupdate.schedule.btn.delete'),
                                           command=self._on_delete_task, state='disabled',
                                           style="danger.TButton")
        self._btn_task_delete.pack(side='left', padx=5)
        row += 1

        # 描述文字
        desc_label = ttk.Label(
            f, text=_('lki.autoupdate.schedule.description'),
            wraplength=480, foreground='gray', justify='left')
        desc_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 0))

        self._refresh_task_list()


    def _on_open_create_dialog(self):
        """打开新建计划任务的配置弹窗。"""
        dialog = TriggerConfigDialog(
            self, self._mgr, self._scheduler,
            self._selected_instance_id,
            self._selected_preset_id
        )
        dialog.wait_window()
        self._refresh_task_list()

    def _on_create_schedule(self, instance_id, preset_id, run_client,
                            trigger_type, instance_name, preset_name,
                            time_str=None, date_str=None, days=None, idle_min=None,
                            task_name=None):
        """创建计划任务的核心逻辑，接收显式参数。"""
        description = _('lki.autoupdate.shortcut_description') % instance_name
        run_str = " Run" if run_client else ""
        description += f" ({preset_name}/{trigger_type}{run_str})"

        def _fmt_time(t):
            h, m = t.split(":")
            return f"{int(h)}:{int(m):02d}"

        try:
            # 始终从触发参数构建后缀
            if trigger_type == 'once':
                trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.once')}-{date_str}-{_fmt_time(time_str)}"
            elif trigger_type == 'daily':
                trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.daily')}-{_fmt_time(time_str)}"
            elif trigger_type == 'weekly':
                if not days:
                    messagebox.showwarning(_('lki.autoupdate.title'),
                                           _('lki.autoupdate.schedule.error.no_days'), parent=self)
                    return
                day_names = {'mon': _('lki.autoupdate.schedule.mon'), 'tue': _('lki.autoupdate.schedule.tue'),
                            'wed': _('lki.autoupdate.schedule.wed'), 'thu': _('lki.autoupdate.schedule.thu'),
                            'fri': _('lki.autoupdate.schedule.fri'), 'sat': _('lki.autoupdate.schedule.sat'),
                            'sun': _('lki.autoupdate.schedule.sun')}
                ds = "-".join(day_names.get(d, d) for d in days)
                trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.weekly')}-{ds}-{_fmt_time(time_str)}"
            elif trigger_type == 'at_logon':
                trigger_part = _('lki.autoupdate.schedule.trigger_desc.at_logon')
            elif trigger_type == 'at_startup':
                trigger_part = _('lki.autoupdate.schedule.trigger_desc.at_startup')
            elif trigger_type == 'on_idle':
                trigger_part = f"{_('lki.autoupdate.schedule.trigger_desc.on_idle')}{idle_min}{_('lki.autoupdate.schedule.trigger_desc.min')}"
            else:
                return

            suffix = f"{instance_name}-{preset_name}-{trigger_part}"

            # 提取用户前缀
            prefix = _('lki.autoupdate.schedule.default_name')
            if task_name and task_name.strip() and instance_name in task_name:
                idx = task_name.index(instance_name)
                extracted = task_name[:idx].rstrip('-').strip()
                if extracted:
                    prefix = extracted
            task_name = utils.sanitize_task_name(f"{prefix}-{suffix}")

            if trigger_type == 'once':
                path = self._scheduler.create_once(
                    task_name, instance_id, preset_id, run_client, time_str, description, date_str)
            elif trigger_type == 'daily':
                path = self._scheduler.create_daily(
                    task_name, instance_id, preset_id, run_client, time_str, description)
            elif trigger_type == 'weekly':
                path = self._scheduler.create_weekly(
                    task_name, instance_id, preset_id, run_client, time_str, days, description)
            elif trigger_type == 'at_logon':
                path = self._scheduler.create_at_logon(
                    task_name, instance_id, preset_id, run_client, description)
            elif trigger_type == 'at_startup':
                path = self._scheduler.create_at_startup(
                    task_name, instance_id, preset_id, run_client, description)
            elif trigger_type == 'on_idle':
                path = self._scheduler.create_on_idle(
                    task_name, instance_id, preset_id, run_client, idle_min, description)
            else:
                return

            messagebox.showinfo(
                _('lki.autoupdate.title'),
                _('lki.autoupdate.schedule.created') % path,
                parent=self
            )
            self._refresh_task_list()

        except ValueError as ve:
            messagebox.showwarning(
                _('lki.autoupdate.title'),
                _('lki.autoupdate.schedule.error.invalid_time') % str(ve),
                parent=self
            )
        except Exception as e:
            messagebox.showerror(
                _('lki.autoupdate.title'),
                _('lki.autoupdate.schedule.error.create_failed') % e,
                parent=self
            )

    def _refresh_task_list(self):
        self._task_listbox.delete(0, 'end')
        self._task_listbox.task_map = {}
        try:
            tasks = self._scheduler.list_tasks()
            if not tasks:
                self._task_listbox.insert('end', _('lki.autoupdate.schedule.no_tasks'))
            for task in tasks:
                display = self._format_task_display(task)
                self._task_listbox.insert('end', display)
                self._task_listbox.task_map[display] = task
        except Exception as e:
            self._task_listbox.insert('end', f"Error: {e}")
        self._update_task_buttons()

    @staticmethod
    def _format_task_display(task: Dict) -> str:
        base = task.get('name', '?')
        trigger = task.get('trigger', {})
        ttype = trigger.get('type', 'unknown')
        status = _('lki.autoupdate.schedule.status_enabled') if task.get('enabled') else _('lki.autoupdate.schedule.status_disabled')

        detail = ""
        if ttype == 'once':
            t = trigger.get('time', '')
            d = trigger.get('date', '')
            detail = f" {d} {t}" if d and t else f" {t}" if t else ""
        elif ttype == 'daily':
            t = trigger.get('time', '')
            detail = f" {t}" if t else ""
        elif ttype == 'weekly':
            t = trigger.get('time', '')
            days = trigger.get('days', [])
            days_str = ",".join(d[:3].title() for d in days) if days else ""
            detail = f" {t} {days_str}" if t or days_str else ""
        elif ttype == 'on_idle':
            idle = trigger.get('idle_minutes', 10)
            detail = f" {idle}min"
        elif ttype == 'at_logon':
            detail = " @logon"
        elif ttype == 'at_startup':
            detail = " @boot"
        else:
            return f"[{status}] {base}"

        return f"[{status}] {base} ({ttype}{detail})"

    def _on_task_select(self, event=None):
        self._update_task_buttons()

    def _update_task_buttons(self):
        selection = self._task_listbox.curselection()
        if not selection or not hasattr(self._task_listbox, 'task_map'):
            self._btn_task_run.config(state='disabled')
            self._btn_task_toggle.config(state='disabled')
            self._btn_task_delete.config(state='disabled')
            self._btn_task_edit.config(state='disabled')
            return
        display = self._task_listbox.get(selection[0])
        task = self._task_listbox.task_map.get(display)
        if not task:
            self._btn_task_run.config(state='disabled')
            self._btn_task_toggle.config(state='disabled')
            self._btn_task_delete.config(state='disabled')
            self._btn_task_edit.config(state='disabled')
            return
        self._btn_task_run.config(state='normal')
        self._btn_task_toggle.config(
            state='normal',
            text=_('lki.autoupdate.schedule.btn.disable') if task.get('enabled') else _('lki.autoupdate.schedule.btn.enable')
        )
        self._btn_task_delete.config(state='normal')
        self._btn_task_edit.config(state='normal')
        self._btn_task_create.config(state='normal')

    def _get_selected_task(self) -> Optional[Dict]:
        selection = self._task_listbox.curselection()
        if not selection or not hasattr(self._task_listbox, 'task_map'):
            return None
        display = self._task_listbox.get(selection[0])
        return self._task_listbox.task_map.get(display)

    def _on_run_task_now(self):
        task = self._get_selected_task()
        if not task:
            return
        if messagebox.askyesno(_('lki.autoupdate.title'),
                               _('lki.autoupdate.schedule.run_now_confirm') % task.get('name', ''),
                               parent=self):
            self._scheduler.run_task_now(task['name'])

    def _on_toggle_task(self):
        task = self._get_selected_task()
        if not task:
            return
        if task.get('enabled'):
            self._scheduler.disable_task(task['name'])
        else:
            self._scheduler.enable_task(task['name'])
        self._refresh_task_list()

    def _on_delete_task(self):
        task = self._get_selected_task()
        if not task:
            return
        if messagebox.askyesno(_('lki.autoupdate.title'),
                               _('lki.autoupdate.schedule.delete_confirm') % task.get('name', ''),
                               parent=self):
            self._scheduler.delete_task(task['name'])
            self._refresh_task_list()

    def _on_edit_task(self):
        """编辑已有计划任务：删除旧任务 → 打开创建弹窗（新建即替换）。"""
        task = self._get_selected_task()
        if not task:
            return
        old_name = task.get('name', '')
        if not old_name:
            return

        if not messagebox.askyesno(
            _('lki.autoupdate.title'),
            _('lki.autoupdate.schedule.edit_confirm') % old_name,
            parent=self
        ):
            return

        # 先删除旧任务
        self._scheduler.delete_task(old_name)

        # 打开创建弹窗（新建即替换，预填旧名称）
        dialog = TriggerConfigDialog(
            self, self._mgr, self._scheduler,
            self._selected_instance_id,
            self._selected_preset_id,
            initial_task_name=old_name
        )
        dialog.wait_window()
        self._refresh_task_list()

    @staticmethod
    def _make_shortcut_name(instance_name: str, preset_name: str) -> str:
        from core.localizer import _
        safe_base = utils.sanitize_task_name(f"{instance_name}-{preset_name}")
        return f"{_('lki.autoupdate.shortcut_default_title') % safe_base}.lnk"

    def _populate_presets(self, instance_id: str, default_preset_id: str):
        instance_data = self._mgr.get_instance(instance_id)
        presets = instance_data.get('presets', {}) if instance_data else {}

        self._preset_name_to_id: dict = {}
        for pid, pdata in presets.items():
            if pdata.get('is_default'):
                display = _(pdata['name_key'])
            else:
                display = pdata.get('name', pid)
            self._preset_name_to_id[display] = pid

        preset_names = list(self._preset_name_to_id.keys())
        self._preset_combo.config(values=preset_names)

        default_display = next(
            (n for n, pid in self._preset_name_to_id.items() if pid == default_preset_id),
            preset_names[0] if preset_names else ''
        )
        self._preset_var.set(default_display)
        self._selected_preset_id = self._preset_name_to_id.get(default_display, default_preset_id)

    def _on_instance_changed(self, _event=None):
        name = self._instance_var.get()
        iid = self._instance_name_to_id.get(name)
        if not iid:
            return
        self._selected_instance_id = iid
        instance_data = self._mgr.get_instance(iid)
        active_preset_id = instance_data.get('active_preset_id', 'default') if instance_data else 'default'
        self._populate_presets(iid, active_preset_id)
        self._update_shortcut_path()

    def _on_preset_changed(self, _event=None):
        display = self._preset_var.get()
        self._selected_preset_id = self._preset_name_to_id.get(display, self._selected_preset_id)
        self._update_shortcut_path()

    def _update_shortcut_path(self):
        instance_name = self._instance_var.get()
        preset_name = self._preset_var.get()
        new_name = self._make_shortcut_name(instance_name, preset_name)
        current_dir = Path(self.shortcut_path_var.get()).parent
        self.shortcut_path_var.set(str(current_dir / new_name))

    def _on_browse(self):
        initial_dir = str(Path(self.shortcut_path_var.get()).parent)
        initial_file = Path(self.shortcut_path_var.get()).name
        save_path = filedialog.asksaveasfilename(
            parent=self,
            title=_('lki.autoupdate.file_dialog_title'),
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".lnk",
            filetypes=[(_('lki.autoupdate.file_type_name'), "*.lnk"), ("All files", "*.*")]
        )
        if save_path:
            self.shortcut_path_var.set(os.path.normpath(save_path))

    def _on_create_shortcut(self):
        save_path = self.shortcut_path_var.get()
        if not save_path:
            messagebox.showwarning(_('lki.autoupdate.title'), _('lki.autoupdate.error.no_path'), parent=self)
            return

        if not self._has_win32com:
            messagebox.showerror(_('lki.autoupdate.title'), "pywin32 library is missing.", parent=self)
            return

        try:
            instance_data = self._mgr.get_instance(self._selected_instance_id)
            instance_name = instance_data['name'] if instance_data else self._instance_var.get()
            korabli_exe = Path(instance_data['path']) / 'Korabli.exe' if instance_data else None

            target_exe, full_args, target_dir = build_autoexec_args(
                self._selected_instance_id, self._selected_preset_id,
                self._run_client_var.get()
            )

            if korabli_exe and korabli_exe.is_file():
                icon_location = f"{korabli_exe}, 0"
            elif utils.is_running_as_msix():
                # MSIX 的 LKNext.exe 是重解析点，不携带图标资源
                # 留空让 Windows 使用默认快捷方式图标
                icon_location = ""
            else:
                icon_path = str(dirs.base_path / 'resources' / 'logo' / 'logo.ico')
                icon_location = f"{icon_path}, 0"

            import win32com.client as _win32com
            shell = _win32com.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(save_path)

            shortcut.TargetPath = target_exe
            shortcut.Arguments = full_args
            shortcut.WorkingDirectory = target_dir
            shortcut.IconLocation = icon_location
            shortcut.Description = _('lki.autoupdate.shortcut_description') % instance_name
            shortcut.Save()

            messagebox.showinfo(
                _('lki.autoupdate.success.title'),
                _('lki.autoupdate.success.message') % save_path,
                parent=self
            )
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                _('lki.autoupdate.title'),
                _('lki.autoupdate.error.create_failed') % e,
                parent=self
            )