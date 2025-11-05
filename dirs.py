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
import sys
from pathlib import Path

base_path: Path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))

try:
    # Use LocalAppData for settings/cache if available
    APP_DATA_PATH = Path(os.getenv('LOCALAPPDATA', '')) / 'LocalizedKorabli' / 'LKInstallerNext'
    if not os.access(os.getenv('LOCALAPPDATA', ''), os.W_OK):
        raise Exception("LocalAppData not writable")
    os.makedirs(APP_DATA_PATH, exist_ok=True)
except Exception:
    # Fallback to alongside executable (portable mode)
    APP_DATA_PATH = base_path / 'lki_data'

CACHE_DIR = APP_DATA_PATH / 'cache'
TEMP_DIR = APP_DATA_PATH / 'temp'
SETTINGS_DIR = APP_DATA_PATH / 'settings'
LOG_DIR = APP_DATA_PATH / 'logs'