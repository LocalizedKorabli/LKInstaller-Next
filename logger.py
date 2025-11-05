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
import os
import platform
import sys
import time
from io import TextIOWrapper
from pathlib import Path
from typing import Optional

import atexit  # 导入 atexit

import dirs

current_log_file_name: str = ''

# --- 全局变量 ---
_original_stdout = sys.stdout
_original_stderr = sys.stderr
_log_file_handle: Optional[TextIOWrapper] = None  # 我们将保持一个全局的文件句柄


class StreamToLogger:
    """
    一个经过修复的类，现在只用于重定向 sys.stderr。
    它能安全处理原始流为 None 的情况。
    """

    def __init__(self, original_stream, log_file):
        self.original_stream = original_stream  # 这将是 _original_stderr
        self.log_file = log_file  # 这将是 _log_file_handle

    def write(self, buf):
        """将缓冲区内容写入原始流 (如果存在) 和日志文件。"""
        try:
            # 1. 写入原始流 (如果存在)
            if self.original_stream:
                self.original_stream.write(buf)
                self.original_stream.flush()

            # 2. 写入日志文件
            if self.log_file:
                # 崩溃日志不需要额外的时间戳
                self.log_file.write(buf)
                self.log_file.flush()
        except Exception:
            # (忽略写入错误, 例如当程序关闭时)
            pass

    def flush(self):
        """刷新两个流 (如果它们存在)。"""
        try:
            if self.original_stream:
                self.original_stream.flush()
            if self.log_file:
                self.log_file.flush()
        except Exception:
            pass


def log(*args, sep=' ', end='\n'):
    """
    新的日志方法，行为类似内置的 print()。
    将消息写入日志文件，并打印到原始控制台。
    """
    global _log_file_handle, _original_stdout

    # 像 print() 一样构建消息字符串
    message = sep.join(map(str, args)) + end

    try:
        # 1. 写入日志文件 (带时间戳)
        if _log_file_handle:
            timestamp = time.strftime('%H:%M:%S')
            _log_file_handle.write(f"[{timestamp}] {message}")
            _log_file_handle.flush()

        # 2. 打印到原始控制台 (如果存在)
        if _original_stdout:
            _original_stdout.write(message)
            _original_stdout.flush()
    except Exception:
        # (忽略写入错误)
        pass


def setup_logger():
    global current_log_file_name, _log_file_handle, _original_stdout, _original_stderr

    # --- 路径设置 (与您原版文件一致) ---
    base_path = Path('')
    try:
        base_path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))
        APP_DATA_PATH = Path(os.getenv('LOCALAPPDATA', '')) / 'LocalizedKorabli' / 'LKInstallerNext'
        if not os.access(os.getenv('LOCALAPPDATA', ''), os.W_OK):
            raise Exception("LocalAppData not writable")
        os.makedirs(APP_DATA_PATH, exist_ok=True)
    except Exception:
        if 'base_path' not in locals():
            base_path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))
        APP_DATA_PATH = base_path / 'lki_data'
        os.makedirs(APP_DATA_PATH, exist_ok=True)

    # 定义日志目录和文件路径
    LOG_DIR = dirs.LOG_DIR
    os.makedirs(LOG_DIR, exist_ok=True)
    current_log_file_name = f"lki-next-{time.strftime('%Y-%m-%d-%H-%M')}.log"
    LOG_FILE_PATH = LOG_DIR / current_log_file_name
    # --- 路径设置结束 ---

    try:
        # 1. 打开全局日志文件句柄
        _log_file_handle = open(LOG_FILE_PATH, 'a', encoding='utf-8')
    except Exception as e:
        # 如果连日志都打不开，只能尝试在控制台打印
        if _original_stdout:
            _original_stdout.write(f"FATAL: Could not open log file {LOG_FILE_PATH}. Error: {e}\n")
        return  # 无法继续

    # 注册退出函数，确保文件被关闭
    atexit.register(close_logger)

    # 2. 在重定向前，打印日志文件的位置到 *原始* 控制台 (如果存在)
    if _original_stdout:
        _original_stdout.write(f"Logging initialized. Log file: {LOG_FILE_PATH}\n")

    # 3. 只重定向 STDERR 来捕获崩溃
    stderr_logger = StreamToLogger(_original_stderr, _log_file_handle)
    sys.stderr = stderr_logger

    # 4. (关键) 我们不再重定向 sys.stdout

    # 5. 使用新的 log() 函数写入初始信息
    # 注意：现在我们调用 log() 而不是 print()
    log(f"--- Log Start: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    log(f"Platform: {platform.platform()}")
    log(f"Program: {sys.executable}")
    log(f"Base Path: {base_path}")
    log(f"Log File: {LOG_FILE_PATH}")


def close_logger():
    """在程序退出时自动关闭日志文件。"""
    global _log_file_handle
    log(f"--- Log End: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    if _log_file_handle:
        try:
            _log_file_handle.close()
        except Exception:
            pass
        _log_file_handle = None