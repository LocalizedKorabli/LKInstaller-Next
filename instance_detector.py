import os
import string
import winreg
import xml.etree.ElementTree as Et
from pathlib import Path
from typing import List, Optional, Tuple, Set
from localizer import _


# --- (逻辑从 installer_gui.py 移植而来) ---

def _find_all_drives() -> List[str]:
    """返回所有驱动器盘符的列表, e.g., ['C:/', 'D:/']"""
    return ['%s:/' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]


def detect_instance_type_from_path(path: Path) -> Optional[str]:
    """
    检查给定路径是否为有效的游戏实例，并返回其类型。
    返回 type_code (e.g. 'production') 或 None。
    """
    # 1. 基础验证 (来自 installer_gui.py)
    try:
        if not path.is_dir():
            return None
        # (LGC 和 Steam 的 .exe 名称不同)
        if not (path / 'Korabli.exe').is_file() and not (path / 'WorldOfWarships.exe').is_file():
            return None
        if not (path / 'bin').is_dir():
            return None
    except Exception:
        return None

    # 2. 检查 Steam (来自 installer_gui.py)
    if (path / 'steam_api64.dll').is_file():
        # Steam 客户端始终是正式服
        return 'production'

    # 3. 检查 game_info.xml (来自 installer_gui.py)
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

    return None  # 未能识别


def _find_from_registry() -> Set[Tuple[str, str]]:
    """
    通过 Lesta Game Center 注册表和 preferences.xml 查找实例。
    """
    found = set()
    try:
        # 1. 查找 LGC 路径 (来自 installer_gui.py)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\lgc\DefaultIcon') as key:
            lgc_dir_str, _ = winreg.QueryValueEx(key, '')

        if ',' in lgc_dir_str:
            lgc_dir_str = lgc_dir_str.split(',')[0]

        # 2. 查找 preferences.xml (来自 installer_gui.py)
        preferences_path = Path(lgc_dir_str).parent / 'preferences.xml'
        if not preferences_path.is_file():
            return found

        # 3. 解析 XML (来自 installer_gui.py)
        pref_root = Et.parse(preferences_path).getroot()
        games_block = pref_root.find('.//application/games_manager/games')
        if games_block is None:
            return found

        for game in games_block.findall('.//game'):
            wd_elem = game.find('working_dir')
            if wd_elem is not None:
                path_str = wd_elem.text
                # 4. 验证是否为 MK (来自 installer_gui.py)
                type_code = detect_instance_type_from_path(Path(path_str))
                if type_code:
                    found.add((os.path.normpath(path_str), type_code))

    except FileNotFoundError:
        print("LGC registry key or preferences.xml not found. Skipping registry scan.")
    except Exception as e:
        print(f"Error scanning registry: {e}")
    return found


def _find_from_common_paths() -> Set[Tuple[str, str]]:
    """
    扫描所有驱动器中的常见安装路径。
    """
    found = set()
    drives = _find_all_drives()

    # 路径列表来自 installer_gui.py
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
            if path.is_dir():
                type_code = detect_instance_type_from_path(path)
                if type_code:
                    found.add((os.path.normpath(str(path)), type_code))
    return found


def detect_instances() -> List[Tuple[str, str]]:
    """
    检测所有游戏实例（来自注册表和常见路径）。
    返回: (path, type_code) 元组的列表。
    """
    print("Starting instance detection...")
    all_found = _find_from_registry()
    all_found.update(_find_from_common_paths())
    print(f"Detection finished. Found {len(all_found)} potential instances.")
    return list(all_found)