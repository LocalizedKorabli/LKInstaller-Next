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

import os
import string
import winreg
import xml.etree.ElementTree as Et
from pathlib import Path
from typing import List, Optional, Tuple, Set


# --- (逻辑从 installer_gui.py 移植而来) ---

def _find_all_drives() -> List[str]:
    """返回所有驱动器盘符的列表, e.g., ['C:/', 'D:/']"""
    return ['%s:/' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]


# (已重命名)
def get_instance_type_from_path(path: Path) -> Optional[str]:
    """
    检查给定路径是否为有效的游戏实例，并返回其类型。
    返回 type_code (e.g. 'production') 或 None。
    """
    try:
        if not path.is_dir():
            return None
        if not (path / 'Korabli.exe').is_file() and not (path / 'WorldOfWarships.exe').is_file():
            return None
        if not (path / 'bin').is_dir():
            return None
    except Exception:
        return None

    if (path / 'steam_api64.dll').is_file():
        return 'production'

    xml_path = path / 'game_info.xml'
    if xml_path.is_file():
        try:
            tree = Et.parse(xml_path)
            game_id_elem = tree.find('.//game/id')
            if game_id_elem is not None:
                game_id = game_id_elem.text
                if game_id == 'MK.RU.PRODUCTION':
                    return 'production'
                if game_id == 'MK.RPT.PRODUCTION':
                    return 'pts'
        except Exception as e:
            print(f"Error parsing game_info.xml at {path}: {e}")

    return None


def _find_from_registry() -> List[Tuple[str, str]]:
    """
    通过 Lesta Game Center 注册表和 preferences.xml 查找实例，并按发现顺序返回列表。
    """
    found_list: List[Tuple[str, str]] = []  # <-- (使用列表而非集合来保留发现顺序)
    seen_paths: Set[str] = set()  # <-- (使用集合进行去重)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\lgc\DefaultIcon') as key:
            lgc_dir_str, _ = winreg.QueryValueEx(key, '')

        if ',' in lgc_dir_str:
            lgc_dir_str = lgc_dir_str.split(',')[0]

        preferences_path = Path(lgc_dir_str).parent / 'preferences.xml'
        if not preferences_path.is_file():
            return found_list

        pref_root = Et.parse(preferences_path).getroot()
        games_block = pref_root.find('.//application/games_manager/games')
        if games_block is None:
            return found_list

        for game in games_block.findall('.//game'):
            wd_elem = game.find('working_dir')
            if wd_elem is not None:
                path_str = wd_elem.text
                path = Path(path_str)
                type_code = get_instance_type_from_path(path)
                normalized_path = os.path.normpath(path_str)

                if type_code and normalized_path not in seen_paths:
                    found_list.append((normalized_path, type_code))
                    seen_paths.add(normalized_path)  # <-- (在找到时去重)

    except FileNotFoundError:
        print("LGC registry key or preferences.xml not found. Skipping registry scan.")
    except Exception as e:
        print(f"Error scanning registry: {e}")
    return found_list


# 修改返回类型：不再需要 mtime，返回 List[Tuple[str, str]]
def _find_from_common_paths() -> List[Tuple[str, str]]:
    """
    扫描所有驱动器中的常见安装路径，并按硬编码扫描顺序返回列表。
    """
    found_list: List[Tuple[str, str]] = []
    seen_paths: Set[str] = set()  # <-- (使用集合进行去重)
    drives = _find_all_drives()

    common_suffixes = [
        'Games/Korabli',
        'Games/Korabli_PT',
        'Korabli',
        'Korabli_PT',
        'SteamLibrary/steamapps/common/Korabli',
        'SteamLibrary/steamapps/common/Korabli_PT',
        'Program Files (x86)/Steam/steamapps/common/Korabli',
        'Program Files (x86)/Steam/steamapps/common/Korabli_PT',
        'Program Files/Steam/steamapps/common/Korabli',
        'Program Files/Steam/steamapps/common/Korabli_PT',
    ]

    for drive in drives:
        for suffix in common_suffixes:
            path = Path(drive) / suffix
            normalized_path = os.path.normpath(str(path))

            if path.is_dir() and normalized_path not in seen_paths:
                type_code = get_instance_type_from_path(path)
                if type_code:
                    found_list.append((normalized_path, type_code))
                    seen_paths.add(normalized_path)  # <-- (在找到时去重)

    # 结果已根据 "drive" -> "suffix" 的顺序自然排序
    return found_list


# (已重命名)
def find_instances_for_auto_import() -> List[Tuple[str, str]]:
    """
    检测所有游戏实例（来自注册表和常见路径），并按发现顺序返回列表。
    返回: (path, type_code) 元组的列表。
    """
    print("Starting instance detection...")

    # 1. 获取通用路径结果 (List, 按扫描顺序排序)
    common_found_sorted: List[Tuple[str, str]] = _find_from_common_paths()

    # 2. 获取注册表结果 (List, 按 LGC preferences.xml 顺序排序)
    registry_found_sorted: List[Tuple[str, str]] = _find_from_registry()

    final_list: List[Tuple[str, str]] = []
    seen_paths: Set[str] = set()

    # 3. 将通用路径的结果添加到最终列表（优先）
    for path, type_code in common_found_sorted:
        if path not in seen_paths:
            final_list.append((path, type_code))
            seen_paths.add(path)

    # 4. 将注册表的结果添加到最终列表（次之）
    for path, type_code in registry_found_sorted:
        if path not in seen_paths:
            final_list.append((path, type_code))
            seen_paths.add(path)

    print(f"Detection finished. Found {len(final_list)} potential instances.")
    return final_list
