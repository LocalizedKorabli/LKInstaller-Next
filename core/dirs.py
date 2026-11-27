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
import ctypes
import os
import sys
from pathlib import Path


def resolve_real_path(path: Path) -> Path:
    """Resolve Windows MSIX VFS/AppData redirections to the real physical path."""
    if os.name != 'nt' or not path.exists():
        return path

    FILE_READ_ATTRIBUTES = 0x80
    FILE_SHARE_ALL = 0x07
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateFileW(
        str(path),
        FILE_READ_ATTRIBUTES,
        FILE_SHARE_ALL,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if handle == INVALID_HANDLE_VALUE or handle == 0:
        return path

    try:
        length = kernel32.GetFinalPathNameByHandleW(handle, None, 0, 0)
        if length <= 0:
            return path
        buf = ctypes.create_unicode_buffer(length)
        written = kernel32.GetFinalPathNameByHandleW(handle, buf, length, 0)
        if written <= 0:
            return path
        resolved = buf.value
        if resolved.startswith('\\\\?\\UNC\\'):
            resolved = '\\\\' + resolved[8:]
        elif resolved.startswith('\\\\?\\'):
            resolved = resolved[4:]
        return Path(resolved)
    except Exception:
        return path
    finally:
        kernel32.CloseHandle(handle)


# In development: __file__ is project_root/core/dirs.py, so .parent.parent = project_root
# In PyInstaller: sys._MEIPASS points to the extraction directory directly
base_path: Path = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent.parent)))

try:
    # Use LocalAppData for settings/cache if available
    APP_DATA_PATH = Path(os.getenv('LOCALAPPDATA', '')) / 'LocalizedKorabli' / 'LKInstallerNext'
    if not os.access(os.getenv('LOCALAPPDATA', ''), os.W_OK):
        raise Exception("LocalAppData not writable")
    os.makedirs(APP_DATA_PATH, exist_ok=True)
    APP_DATA_PATH = resolve_real_path(APP_DATA_PATH)
except Exception:
    # Fallback to alongside executable (portable mode)
    APP_DATA_PATH = base_path / 'lki_data'

CACHE_DIR = APP_DATA_PATH / 'cache'
TEMP_DIR = APP_DATA_PATH / 'temp'
SETTINGS_DIR = APP_DATA_PATH / 'settings'
LOG_DIR = APP_DATA_PATH / 'logs'
