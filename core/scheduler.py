import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

from core.logger import log
from core import utils

TASK_FOLDER = "\\"

DAYS_OF_WEEK_MAP = {
    'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4,
    'fri': 5, 'sat': 6, 'sun': 7
}
DAYS_OF_WEEK_SHORT = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

TASK_TRIGGER_ONCE = 1
TASK_TRIGGER_DAILY = 2
TASK_TRIGGER_WEEKLY = 3
TASK_TRIGGER_LOGON = 9
TASK_TRIGGER_BOOT = 8
TASK_TRIGGER_IDLE = 6

class SchedulerError(Exception):
    pass

def build_autoexec_args(instance_id: str, preset_id: str, run_client: bool) -> tuple:
    """
    构建自动执行所需的 (target_alias, full_args, working_dir)。
    scheduler 和 shortcut 共用此逻辑。
    """
    preset_arg = f'--auto-execute-preset "{instance_id}:{preset_id}"'
    run_arg = "--runclient" if run_client else ""
    full_args = f"{preset_arg} {run_arg}".strip()

    target_alias = "LKNext.exe"
    if utils.is_running_as_msix():
        working_dir = os.path.expanduser("~")
        # MSIX 执行别名路径（Task Scheduler 可解析）
        target_alias = os.path.join(os.environ.get('LOCALAPPDATA', working_dir),
                                     r'Microsoft\WindowsApps\LKNext.exe')
    else:
        working_dir = str(Path(sys.executable).parent)
        target_alias = str(Path(sys.executable))  # 使用完整路径确保计划任务能解析

    return target_alias, full_args, working_dir


class SchedulerBackend:
    def __init__(self):
        self._service = None
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            try:
                import win32com.client
                self._service = win32com.client.Dispatch("Schedule.Service")
                self._service.Connect()
                self._connected = True
                log("Task Scheduler COM connected successfully")
            except Exception as e:
                log(f"Task Scheduler COM connection failed: {e}")
                raise SchedulerError(f"Cannot connect to Task Scheduler: {e}")

    def _get_folder(self, path: str):
        self._ensure_connected()
        try:
            return self._service.GetFolder(path)
        except Exception as e:
            log(f"Task Scheduler folder get failed: {e}")
            try:
                root = self._service.GetFolder("\\")
                root.CreateFolder(path, "")
                log(f"Created Task Scheduler folder: {path}")
                return self._service.GetFolder(path)
            except Exception as e:
                log(f"Task Scheduler folder creation failed: {e}")
                raise SchedulerError(f"Cannot create folder {path}: {e}")


    def create_once(self, task_name: str, instance_id: str, preset_id: str,
                    run_client: bool, time_str: str, description: str = "",
                    date_str: Optional[str] = None) -> str:
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_ONCE,
                lambda trigger: self._set_once_params(trigger, time_str, date_str)
            )
        except Exception:
            if not date_str:
                date_str = time.strftime("%Y/%m/%d")
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC ONCE', f'/ST {time_str} /SD {date_str.replace("-", "/")}'
            )

    def create_daily(self, task_name: str, instance_id: str, preset_id: str,
                     run_client: bool, time_str: str, description: str = "") -> str:
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_DAILY,
                lambda trigger: self._set_daily_params(trigger, time_str)
            )
        except Exception:
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC DAILY', f'/ST {time_str}'
            )

    def create_weekly(self, task_name: str, instance_id: str, preset_id: str,
                      run_client: bool, time_str: str, days: List[str],
                      description: str = "") -> str:
        day_codes = [d.lower()[:3] for d in days]
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_WEEKLY,
                lambda trigger: self._set_weekly_params(trigger, time_str, day_codes)
            )
        except Exception:
            day_str = ",".join(d.upper() for d in day_codes)
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC WEEKLY', f'/D {day_str} /ST {time_str}'
            )

    def create_at_logon(self, task_name: str, instance_id: str, preset_id: str,
                        run_client: bool, description: str = "") -> str:
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_LOGON,
                lambda trigger: setattr(trigger, 'UserId', '')
            )
        except Exception:
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC ONLOGON', '/IT'
            )

    def create_at_startup(self, task_name: str, instance_id: str, preset_id: str,
                          run_client: bool, description: str = "") -> str:
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_BOOT,
                lambda trigger: None
            )
        except Exception:
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC ONSTART', '/IT'
            )

    def create_on_idle(self, task_name: str, instance_id: str, preset_id: str,
                       run_client: bool, idle_minutes: int, description: str = "") -> str:
        try:
            return self._com_create_trigger(
                task_name, instance_id, preset_id, run_client,
                description, TASK_TRIGGER_IDLE,
                lambda trigger: setattr(trigger, 'IdleWait', idle_minutes)
            )
        except Exception:
            return self._schtasks_create(
                task_name, instance_id, preset_id, run_client,
                '/SC ONIDLE', f'/I {idle_minutes}'
            )

    def _com_create_trigger(self, task_name: str, instance_id: str, preset_id: str,
                            run_client: bool, description: str,
                            trigger_type: int, set_trigger_params) -> str:
        self._ensure_connected()
        prefixed_name = f"LKInstallerNext-{task_name}"
        try:
            target_exe, full_args, working_dir = build_autoexec_args(
                instance_id, preset_id, run_client
            )
            task = self._service.NewTask(0)
            task.RegistrationInfo.Author = "LKInstallerNext"
            task.RegistrationInfo.Description = description or f"LK Next: auto-update {instance_id}"
            task.Settings.Enabled = True
            task.Settings.StartWhenAvailable = True
            task.Settings.DisallowStartIfOnBatteries = False
            task.Settings.StopIfGoingOnBatteries = False
            task.Settings.RunOnlyIfIdle = False
            task.Principal.RunLevel = 0
            action = task.Actions.Create(0)
            action.Path = target_exe
            action.Arguments = full_args
            action.WorkingDirectory = working_dir
            trigger = task.Triggers.Create(trigger_type)
            trigger.Enabled = True
            trigger.StartBoundary = "2000-01-01T00:00:00"
            set_trigger_params(trigger)
            folder = self._get_folder(TASK_FOLDER)
            folder.RegisterTaskDefinition(
                prefixed_name, task, 6, "", "", 1
            )
            log(f"Scheduled task created via COM: {prefixed_name}")
            return prefixed_name
        except Exception as e:
            log(f"COM task creation failed for '{prefixed_name}': {e}")
            import traceback
            log(f"COM traceback: {traceback.format_exc()}")
            raise

    @staticmethod
    def _set_once_params(trigger, time_str: str, date_str: Optional[str] = None):
        hours, minutes = time_str.split(":") if ":" in time_str else (time_str[:2], time_str[2:])
        if date_str:
            # date_str 格式为 YYYY-MM-DD
            date_clean = date_str.replace("-", "")
            y, m, d = date_clean[:4], date_clean[4:6], date_clean[6:8]
            trigger.StartBoundary = f"{y}-{m}-{d}T{int(hours):02d}:{int(minutes):02d}:00"
        else:
            import datetime
            today = datetime.date.today()
            trigger.StartBoundary = f"{today}T{int(hours):02d}:{int(minutes):02d}:00"

    @staticmethod
    def _set_daily_params(trigger, time_str: str):
        hours, minutes = time_str.split(":") if ":" in time_str else (time_str[:2], time_str[2:])
        trigger.StartBoundary = f"2000-01-01T{int(hours):02d}:{int(minutes):02d}:00"
        trigger.DaysInterval = 1

    @staticmethod
    def _set_weekly_params(trigger, time_str: str, days: List[str]):
        hours, minutes = time_str.split(":") if ":" in time_str else (time_str[:2], time_str[2:])
        trigger.StartBoundary = f"2000-01-01T{int(hours):02d}:{int(minutes):02d}:00"
        trigger.WeeksInterval = 1
        for day_code in days:
            day_num = DAYS_OF_WEEK_MAP.get(day_code.lower()[:3], 0)
            if day_num:
                trigger.DaysOfWeek |= 1 << (day_num - 1)

    def _schtasks_create(self, task_name, instance_id, preset_id, run_client, sc_args, extra_args) -> str:
        target_exe, full_args, working_dir = build_autoexec_args(
            instance_id, preset_id, run_client
        )
        full_path = f"LKInstallerNext\\{task_name}"
        cmd = [
            'schtasks', '/Create', '/F',
            '/TN', full_path,
            '/TR', f'"{target_exe}" {full_args}',
        ]
        cmd.extend(sc_args.split())
        if extra_args:
            cmd.extend(extra_args.split())
        if '/IT' not in cmd:
            cmd.append('/IT')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                raise SchedulerError(f"schtasks failed: {result.stderr.strip()}")
            log(f"Scheduled task created via schtasks: {full_path}")
            return full_path
        except FileNotFoundError:
            raise SchedulerError("schtasks.exe not found on this system")
        except subprocess.TimeoutExpired:
            raise SchedulerError("schtasks timed out")

    def delete_task(self, task_name: str) -> bool:
        try:
            folder = self._get_folder(TASK_FOLDER)
            folder.DeleteTask(task_name, 0)
            log(f"Deleted scheduled task: {TASK_FOLDER}\\{task_name}")
            return True
        except Exception as e:
            log(f"COM delete failed, trying schtasks: {e}")
        try:
            full_path = f"LKInstallerNext\\{task_name}"
            result = subprocess.run(
                ['schtasks', '/Delete', '/F', '/TN', full_path],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            log(f"schtasks delete failed: {e}")
            return False

    def rename_task(self, task_name: str, new_name: str) -> bool:
        """将已存在的计划任务重命名。尝试 COM，失败则回退到 schtasks。"""
        new_name = utils.sanitize_task_name(new_name)
        if not new_name or new_name == task_name:
            return False
        try:
            self._ensure_connected()
            folder = self._get_folder(TASK_FOLDER)
            task = folder.GetTask(task_name)
            definition = task.Definition
            # 在新名称下注册相同的定义
            folder.RegisterTaskDefinition(new_name, definition, 6, "", "", 1)
            # 删除旧任务
            folder.DeleteTask(task_name, 0)
            log(f"Renamed scheduled task: {TASK_FOLDER}\\{task_name} -> {new_name}")
            return True
        except Exception as e:
            log(f"COM rename failed, trying schtasks: {e}")
        try:
            # schtasks 回退：通过导出/重新导入实现
            full_old = f"LKInstallerNext-{task_name}"
            full_new = f"LKInstallerNext-{new_name}"
            # 导出旧任务为 XML
            export = subprocess.run(
                ['schtasks', '/Query', '/XML', '/TN', full_old],
                capture_output=True, text=True, timeout=15
            )
            if export.returncode != 0 or not export.stdout.strip():
                return False
            # 用 XML 创建新任务
            create = subprocess.run(
                ['schtasks', '/Create', '/TN', full_new, '/XML', '-', '/F'],
                input=export.stdout, capture_output=True, text=True, timeout=15
            )
            if create.returncode != 0:
                return False
            # 删除旧任务
            subprocess.run(
                ['schtasks', '/Delete', '/F', '/TN', full_old],
                capture_output=True, text=True, timeout=10
            )
            log(f"Renamed scheduled task via schtasks: {task_name} -> {new_name}")
            return True
        except Exception as e:
            log(f"schtasks rename failed: {e}")
            return False

    def enable_task(self, task_name: str) -> bool:
        return self._set_task_enabled(task_name, True)

    def disable_task(self, task_name: str) -> bool:
        return self._set_task_enabled(task_name, False)

    def _set_task_enabled(self, task_name: str, enabled: bool) -> bool:
        try:
            self._ensure_connected()
            folder = self._get_folder(TASK_FOLDER)
            task = folder.GetTask(task_name)
            task.Enabled = enabled
            log(f"{'Enabled' if enabled else 'Disabled'} task: {TASK_FOLDER}\\{task_name}")
            return True
        except Exception as e:
            log(f"Failed to {'enable' if enabled else 'disable'} task via COM: {e}")
        try:
            full_path = f"LKInstallerNext\\{task_name}"
            flag = '/ENABLE' if enabled else '/DISABLE'
            result = subprocess.run(
                ['schtasks', '/Change', flag, '/TN', full_path],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            log(f"schtasks change failed: {e}")
            return False

    def run_task_now(self, task_name: str) -> bool:
        try:
            self._ensure_connected()
            folder = self._get_folder(TASK_FOLDER)
            task = folder.GetTask(task_name)
            task.Run("")
            log(f"Triggered task run: {TASK_FOLDER}\\{task_name}")
            return True
        except Exception as e:
            log(f"Failed to run task via COM: {e}")
        try:
            full_path = f"LKInstallerNext\\{task_name}"
            result = subprocess.run(
                ['schtasks', '/Run', '/TN', full_path],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            log(f"schtasks run failed: {e}")
            return False

    def task_exists(self, task_name: str) -> bool:
        try:
            self._ensure_connected()
            folder = self._get_folder(TASK_FOLDER)
            folder.GetTask(task_name)
            return True
        except Exception:
            return False

    def list_tasks(self) -> List[Dict]:
        tasks = []
        try:
            self._ensure_connected()
            folder = self._get_folder(TASK_FOLDER)
            collection = folder.GetTasks(1)
            for task in collection:
                name = task.Name
                if name.startswith('LKInstallerNext-') or name.startswith('LKInstallerNext\\'):
                    tasks.append(self._com_extract_info(task))
            # 兼容旧版子文件夹中的任务
            try:
                old_folder = self._get_folder("\\LKInstallerNext")
                old_collection = old_folder.GetTasks(1)
                for task in old_collection:
                    tasks.append(self._com_extract_info(task))
            except Exception:
                pass
        except Exception as e:
            log(f"COM list failed, trying schtasks: {e}")
            return self._schtasks_list()
        return tasks

    def _com_extract_info(self, task) -> Dict:
        info = {
            'name': task.Name,
            'enabled': task.Enabled,
            'state': task.State,
            'trigger': {'type': 'unknown'},
            'description': '',
        }
        try:
            triggers = task.Definition.Triggers
            if triggers.Count > 0:
                trigger = triggers[1]
                trigger_type = trigger.Type
                type_map = {
                    TASK_TRIGGER_ONCE: 'once',
                    TASK_TRIGGER_DAILY: 'daily',
                    TASK_TRIGGER_WEEKLY: 'weekly',
                    TASK_TRIGGER_LOGON: 'at_logon',
                    TASK_TRIGGER_BOOT: 'at_startup',
                    TASK_TRIGGER_IDLE: 'on_idle',
                }
                ttype = type_map.get(trigger_type, 'unknown')
                info['trigger']['type'] = ttype
                sb = getattr(trigger, 'StartBoundary', '')
                if sb and len(sb) >= 16:
                    info['trigger']['time'] = sb[11:16]
                    info['trigger']['date'] = sb[0:10]
                if ttype == 'weekly':
                    info['trigger']['days'] = self._com_get_weekdays(trigger)
                if ttype == 'on_idle':
                    info['trigger']['idle_minutes'] = getattr(trigger, 'IdleWait', 10)
            info['description'] = getattr(task.Definition.RegistrationInfo, 'Description', '')
        except Exception:
            pass
        return info

    @staticmethod
    def _com_get_weekdays(trigger):
        days = []
        day_names = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        dw = getattr(trigger, 'DaysOfWeek', 0)
        for i in range(7):
            if dw & (1 << i):
                days.append(day_names[(i + 1) % 7])
        return days

    def _schtasks_list(self) -> List[Dict]:
        tasks = []
        for pattern in ['LKInstallerNext-*', '\\LKInstallerNext\\*']:
            try:
                result = subprocess.run(
                    ['schtasks', '/Query', '/FO', 'CSV', '/V', '/TN', pattern],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode != 0:
                    continue
                lines = result.stdout.strip().splitlines()
                if len(lines) < 2:
                    continue
                headers = [h.strip('" ') for h in lines[0].split('","')]

                # 从 CSV 中找到需要的列（不区分大小写）
                col_map = {}
                for col_name in ('Schedule Type', 'Scheduled Type', 'Schedule',
                                 'Start Time', 'Start', 'Days', 'Description', 'Status', 'TaskName'):
                    for i, h in enumerate(headers):
                        if h.lower() == col_name.lower():
                            col_map[col_name] = i

                # schtasks 文本 → 内部类型 映射
                SCHTYPE_MAP = {
                    'once': 'once',
                    'daily': 'daily',
                    'weekly': 'weekly',
                    'at logon': 'at_logon',
                    'at system startup': 'at_startup',
                    'on idle': 'on_idle',
                }

                for line in lines[1:]:
                    if not line.strip():
                        continue
                    values = [v.strip('" ') for v in line.split('","')]
                    if len(values) < len(headers):
                        continue
                    row = dict(zip(headers, values))
                    task_name = row.get('TaskName', '')
                    if '\\' in task_name:
                        task_name = task_name.rsplit('\\', 1)[-1]

                    # 解析触发类型
                    trig = {'type': 'unknown'}
                    schedule_idx = col_map.get('Schedule Type', col_map.get('Scheduled Type', col_map.get('Schedule')))
                    if schedule_idx is not None and schedule_idx < len(values):
                        raw_type = values[schedule_idx].lower().strip()
                        for keyword, code in SCHTYPE_MAP.items():
                            if keyword in raw_type:
                                trig['type'] = code
                                break

                    # 解析开始时间
                    time_idx = col_map.get('Start Time', col_map.get('Start'))
                    if time_idx is not None and time_idx < len(values):
                        raw_time = values[time_idx].strip()
                        if raw_time:
                            if ' ' in raw_time:
                                parts = raw_time.split(' ')
                                trig['date'] = parts[0].replace('/', '-')
                                if len(parts) > 1 and len(parts[1]) >= 5:
                                    trig['time'] = parts[1][:5]
                            elif len(raw_time) >= 5:
                                trig['time'] = raw_time[:5]

                    # 解析星期（仅 weekly）
                    days_idx = col_map.get('Days')
                    if days_idx is not None and days_idx < len(values) and trig['type'] == 'weekly':
                        raw_days = values[days_idx].strip().lower()
                        day_map = {'mon': 'mon', 'tue': 'tue', 'wed': 'wed',
                                   'thu': 'thu', 'fri': 'fri', 'sat': 'sat', 'sun': 'sun'}
                        parsed = []
                        for k, v in day_map.items():
                            if k in raw_days:
                                parsed.append(v)
                        if parsed:
                            trig['days'] = parsed

                    tasks.append({
                        'name': task_name,
                        'enabled': 'Disabled' not in row.get('Status', 'Ready'),
                        'state': 3 if 'Running' in row.get('Status', '') else 3,
                        'trigger': trig,
                        'description': row.get('Description', ''),
                    })
            except Exception as e:
                log(f"schtasks query for {pattern} failed: {e}")
        return tasks

    def get_task_info(self, task_name: str) -> Optional[Dict]:
        tasks = self.list_tasks()
        for t in tasks:
            if t['name'] == task_name:
                return t
        return None


