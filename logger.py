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
import os
import platform
import sys
import time
from pathlib import Path

import utils

current_log_file_name: str = ''

class StreamToLogger:
    def __init__(self, original_stream, log_file_path):
        self.original_stream = original_stream
        self.log_file_path = log_file_path
        self.log_file = None
        try:
            self.log_file = open(self.log_file_path, 'a', encoding='utf-8')
        except Exception as e:
            # 如果日志文件无法打开，在原始控制台打印致命错误
            self.original_stream.write(f"FATAL: Could not open log file {self.log_file_path}. Error: {e}\n")

    def write(self, buf):
        """将缓冲区内容写入原始流和日志文件。"""
        try:
            self.original_stream.write(buf)
            self.original_stream.flush()

            if self.log_file:
                self.log_file.write(buf)
                self.log_file.flush()
        except Exception:
            # (忽略写入错误, 例如当程序关闭时)
            pass

    def flush(self):
        """刷新两个流。"""
        try:
            self.original_stream.flush()
            if self.log_file:
                self.log_file.flush()
        except Exception:
            pass

    def __del__(self):
        """确保在对象销毁时关闭文件。"""
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass

def setup_logger():
    base_path = Path('.')
    try:
        # 抓取 base_path (来自 utils.py)
        # sys._MEIPASS 是 PyInstaller 在打包时使用的临时路径
        base_path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))

        # 抓取 APP_DATA_PATH 逻辑 (来自 utils.py)
        # 必须在这里复制，因为 utils.py 尚未导入
        APP_DATA_PATH = Path(os.getenv('LOCALAPPDATA', '')) / 'LocalizedKorabli' / 'LKInstallerNext'
        if not os.access(os.getenv('LOCALAPPDATA', ''), os.W_OK):
            raise Exception("LocalAppData not writable")
        os.makedirs(APP_DATA_PATH, exist_ok=True)
    except Exception:
        # 回退到可执行文件旁边 (portable mode)
        # (确保 base_path 已被定义)
        if 'base_path' not in locals():
            base_path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))
        APP_DATA_PATH = base_path / 'lki_data'
        os.makedirs(APP_DATA_PATH, exist_ok=True)

    # 定义日志目录和文件路径
    LOG_DIR = utils.LOG_DIR
    os.makedirs(LOG_DIR, exist_ok=True)
    global current_log_file_name
    current_log_file_name = f"lki-next-{time.strftime('%Y-%m-%d-%H:%M')}.log"
    LOG_FILE_PATH = LOG_DIR / current_log_file_name

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # 2. 在重定向前，打印日志文件的位置到 *原始* 控制台
    original_stdout.write(f"Logging initialized. Log file: {LOG_FILE_PATH}\n")

    # 3. 创建日志记录器实例
    stdout_logger = StreamToLogger(original_stdout, LOG_FILE_PATH)
    stderr_logger = StreamToLogger(original_stderr, LOG_FILE_PATH)

    sys.stdout = stdout_logger
    sys.stderr = stderr_logger

    print(f"\n--- Log Start: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    print(f"Platform: {platform.platform()}")
    print(f"Program: {sys.executable}")
    print(f"Base Path: {base_path}")
    print(f"Log File: {LOG_FILE_PATH}")