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
import string
import winreg
import xml.etree.ElementTree as Et
from pathlib import Path
import vdf
from logger import log
from typing import List, Optional, Tuple, Set

MK_STEAM_APP_ID = '3114940'

def _find_all_drives() -> List[str]:
    """返回所有驱动器盘符的列表, e.g., ['C:/', 'D:/']"""
    return ['%s:/' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]


def get_instance_type_from_path(path: Path) -> Optional[str]:
    """
    检查给定路径是否为有效的游戏实例，并返回其类型。
    返回 type_code (e.g. 'production') 或 None。
    """
    try:
        if not path.is_dir():
            return None
        if not (path / 'Korabli.exe').is_file():
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
            log(f"Error parsing game_info.xml at {path}: {e}")

    return None


# Scan from Steam
def _get_steam_install_path() -> Optional[str]:
    """从 Windows 注册表获取 Steam 的安装路径。"""
    try:
        # 尝试 64 位注册表路径
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam")
    except FileNotFoundError:
        try:
            # 尝试 32 位注册表路径
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
        except FileNotFoundError:
            return None

    try:
        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        return install_path
    except Exception:
        return None
    finally:
        if 'key' in locals():
            winreg.CloseKey(key)


def _get_steam_library_paths(steam_path: str) -> List[str]:
    """解析 libraryfolders.vdf 文件以获取所有游戏库的 steamapps 路径。"""
    library_paths = []

    default_steamapps = os.path.join(steam_path, "steamapps")
    if os.path.exists(default_steamapps):
        library_paths.append(default_steamapps)

    vdf_path = os.path.join(default_steamapps, "libraryfolders.vdf")

    if not os.path.exists(vdf_path):
        return library_paths

    try:
        with open(vdf_path, 'r', encoding='utf-8') as f:
            data = vdf.load(f)

        library_folders = data.get('libraryfolders', {})
        # VDF 结构可能因 Steam 版本而异，这里尝试遍历可能的键
        # 检查 'libraryfolders' 下是否有数字键
        if isinstance(library_folders, dict):
            for key, folder_data in library_folders.items():
                if isinstance(key, str) and key.isdigit() and 'path' in folder_data:
                    path = folder_data['path']
                    extra_steamapps = os.path.join(path, "steamapps")
                    if os.path.exists(extra_steamapps):
                        library_paths.append(extra_steamapps)

    except Exception as e:
        log(f"Error parsing libraryfolders.vdf: {e}")

    return library_paths


def _find_from_steam(app_id: str) -> List[Tuple[str, str]]:
    log("Scanning Steam...")
    steam_install_path = _get_steam_install_path()
    if not steam_install_path:
        log("Steam install path not found via registry.")
        return []

    steam_game_found: List[Tuple[str, str]] = []

    library_folders = _get_steam_library_paths(steam_install_path)

    for lib_path_steamapps in library_folders:
        acf_file = os.path.join(lib_path_steamapps, f"appmanifest_{app_id}.acf")

        if not os.path.exists(acf_file):
            continue
        try:
            with open(acf_file, 'r', encoding='utf-8') as f:
                acf_data = vdf.load(f)

            game_folder_name = acf_data.get('AppState', {}).get('installdir')

            if not game_folder_name:
                continue
            library_root = os.path.dirname(lib_path_steamapps)
            game_directory = os.path.join(library_root, "steamapps", "common", game_folder_name)
            if not os.path.exists(game_directory):
                continue
            type_code = get_instance_type_from_path(Path(game_directory))
            if type_code:
                normalized_path = os.path.normpath(game_directory)
                steam_game_found.append((normalized_path, type_code))
                log(f"Mir Korabley Steam instance found: {normalized_path}")
            else:
                log(f"Found Steam game {app_id}, but not a Mir Korabley instance.")

        except Exception as e:
            log(f"Error parsing appmanifest for {app_id}: {e}")

    return steam_game_found


# --- 原有的 LGC 和通用路径查找功能 (未修改) ---

def _find_from_registry() -> List[Tuple[str, str]]:
    log("Scanning LGC registries...")
    found_list: List[Tuple[str, str]] = []
    seen_paths: Set[str] = set()
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
                    seen_paths.add(normalized_path)
                    log(f"Mir Korabley instance found in LGC registries: {normalized_path}")

    except FileNotFoundError:
        log("LGC registry key or preferences.xml not found. Skipping registry scan.")
    except Exception as e:
        log(f"Error scanning registry: {e}")
    return found_list


def _find_from_common_paths() -> List[Tuple[str, str]]:
    log("Scanning hardcoded common paths...")
    found_list: List[Tuple[str, str]] = []
    seen_paths: Set[str] = set()
    drives = _find_all_drives()

    common_suffixes = [
        'Games/Korabli',
        'Games/Korabli_PT',
        'Korabli',
        'Korabli_PT',
        # Default steam instance paths
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
                    seen_paths.add(normalized_path)
                    log(f"Mir Korabley instance found via scanning hardcoded common paths: {normalized_path}")

    return found_list


def find_instances_for_auto_import() -> List[Tuple[str, str]]:
    """
    检测所有游戏实例（来自注册表、常见路径和特定 Steam 游戏），并按发现顺序返回列表。
    返回: (path, type_code) 元组的列表。
    """
    log("Starting instance detection...")
    # LGC reg
    registry_found_sorted: List[Tuple[str, str]] = _find_from_registry()

    # Steam
    steam_game_found: List[Tuple[str, str]] = _find_from_steam(MK_STEAM_APP_ID)

    # Iteration
    common_found_sorted: List[Tuple[str, str]] = _find_from_common_paths()

    final_list: List[Tuple[str, str]] = []
    seen_paths: Set[str] = set()

    for scan_type in [registry_found_sorted, steam_game_found, common_found_sorted]:
        for _path, _type_code in scan_type:
            if _path not in seen_paths:
                final_list.append((_path, _type_code))
                seen_paths.add(_path)

    log(f"Detection finished. Found {len(final_list)} potential instances.")
    return final_list