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
import hashlib
import json
import os
import subprocess  # (新增)
from pathlib import Path
from logger import log
from typing import Dict, Optional, List, Tuple  # (新增 Tuple)

import win32api


def _calculate_sha256(filepath: Path) -> Optional[str]:
    """计算文件的 SHA256 哈希值"""
    if not filepath.is_file():
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
    except Exception as e:
        log(f"Error calculating SHA256 for {filepath}: {e}")
        return None


class LocalizationInfo:
    """
    一个数据类，用于保存 installation_info.json 的内容。
    """

    def __init__(self, version: str, files: Dict[str, Dict[str, str]], lang_code: Optional[str] = None,
                 l10n_sub_version: Optional[str] = None):
        self.version: str = version
        self.files: Dict[str, Dict[str, str]] = files  # <-- (修改)
        self.lang_code: Optional[str] = lang_code
        self.l10n_sub_version: Optional[str] = l10n_sub_version


class GameVersion:
    """
    代表一个单独的游戏版本，对应于 "bin/" 目录下的一个数字文件夹。
    """

    def __init__(self, bin_folder_path: Path, game_root_path: Path):
        self.bin_folder_path: Path = bin_folder_path
        self.game_root_path: Path = game_root_path
        self.bin_folder_name: str = bin_folder_path.name
        self.exe_version: Optional[str] = None
        self.l10n_info: Optional[LocalizationInfo] = None

        self.load_details()

    def load_details(self):
        """加载此版本的所有动态属性"""
        self.exe_version = self._load_exe_version()
        self.l10n_info = self._load_l10n_info()

    # --- (已修改：读取 ProductVersion 字符串) ---
    def _load_exe_version(self) -> Optional[str]:
        """
        从 bin64/Korabli64.exe 中提取产品版本 (a.b.c.d)
        """
        exe_path_str = str(self.bin_folder_path / "bin64" / "Korabli64.exe")
        if not os.path.exists(exe_path_str):
            exe_path_str = str(self.bin_folder_path / "bin64" / "WorldOfWarships64.exe")
            if not os.path.exists(exe_path_str):
                log(f"Warning: Did not find Korabli64.exe or WorldOfWarships64.exe in {self.bin_folder_path}")
                return None

        try:
            # 1. 获取语言和代码页
            lang, codepage = win32api.GetFileVersionInfo(exe_path_str, '\\VarFileInfo\\Translation')[0]

            # 2. 构建字符串路径
            str_info_path = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\ProductVersion'

            # 3. 查询 ProductVersion 字符串
            product_version_string = win32api.GetFileVersionInfo(exe_path_str, str_info_path)

            if product_version_string:
                # 4. 清理字符串 (例如 "25,11,0,8828504" -> "25.11.0.8828504")
                clean_version = product_version_string.replace(',', '.').strip()
                return clean_version
            else:
                # (回退逻辑，以防万一 ProductVersion 字符串为空)
                info = win32api.GetFileVersionInfo(exe_path_str, '\\')
                ms = info['ProductVersionMS']
                ls = info['ProductVersionLS']
                major = (ms >> 16) & 0xffff
                minor = (ms >> 0) & 0xffff
                patch = (ls >> 16) & 0xffff
                build = (ls >> 0) & 0xffff
                return f"{major}.{minor}.{patch}.{build}"

        except Exception as e:
            log(f"Error reading exe product version from {exe_path_str}: {e}")
            return None

    # --- (修改结束) ---

    def _load_l10n_info(self) -> Optional[LocalizationInfo]:
        """
        从 [实例]/lki/info/[版本号]/installation_info.json 加载信息。
        """
        info_path = self.game_root_path / "lki" / "info" / self.bin_folder_name / "installation_info.json"
        if not info_path.is_file():
            return None

        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return LocalizationInfo(
                version=data.get("version"),
                files=data.get("files", {}),
                lang_code=data.get("lang_code"),
                l10n_sub_version=data.get("l10n_sub_version")
            )
        except Exception as e:
            log(f"Error loading {info_path}: {e}")
            return None

    def get_component_statuses(self) -> Dict[str, str]:
        """
        验证所有已知组件 (i18n, ee, font) 并返回其状态。
        返回: {"i18n": "ok", "ee": "tampered", "font": "not_installed"}
        """
        # (已修改：不再检查预设，始终检查所有组件)
        all_components = ["i18n", "ee", "font", "mods"]

        if not self.l10n_info:
            return {comp: "not_installed" for comp in all_components}

        if self.l10n_info.version == "INACTIVE":
            return {comp: "inactive" for comp in all_components}

        statuses = {}
        files_data = self.l10n_info.files

        for component in all_components:
            path_dict = files_data.get(component)

            if not path_dict:
                # (组件已启用，但 info.json 中没有条目 = 损坏/未安装)
                statuses[component] = "not_installed"
                continue

            is_verified = True
            for relative_path, expected_hash in path_dict.items():
                # (新逻辑：relative_path 是 "mods/file.mkmod")
                # (self.bin_folder_path 是 ".../bin/8828504")
                absolute_path = self.bin_folder_path / relative_path

                actual_hash = _calculate_sha256(absolute_path)

                if actual_hash != expected_hash:
                    log(f"Verification FAILED for {relative_path}: Hash mismatch.")
                    is_verified = False
                    break  # 一个坏文件使该组件失败

            statuses[component] = "ok" if is_verified else "tampered"

        return statuses


class GameInstance:
    """
    代表一个完整的游戏实例（例如 "C:/Games/Korabli"）。
    它包含多个 GameVersion 对象。
    """

    def __init__(self, instance_id: str, path: Path, name: str, type: str):
        self.instance_id: str = instance_id
        self.path: Path = path
        self.name: str = name
        self.type: str = type

        self.versions: List[GameVersion] = []

        self._discover_game_versions()

    def _discover_game_versions(self):
        """
        扫描 bin/ 目录以查找所有数字文件夹并将其加载为 GameVersion。
        """
        self.versions = []
        bin_path = self.path / "bin"
        if not bin_path.is_dir():
            log(f"Warning: 'bin' directory not found in {self.path}")
            return

        for folder_name in os.listdir(bin_path):
            if folder_name.isdigit():
                folder_path = bin_path / folder_name
                if folder_path.is_dir():
                    log(f"Found game version folder: {folder_name}")
                    self.versions.append(GameVersion(folder_path, self.path))

        self.versions.sort(key=lambda v: v.exe_version or "0.0", reverse=True)

    def get_latest_version(self) -> Optional[GameVersion]:
        """
        获取最新的（基于 .exe 版本号） GameVersion。
        """
        if not self.versions:
            return None
        return self.versions[0]

    # (新增)
    def launch_game(self) -> Tuple[bool, Optional[str]]:
        """
        Tries to launch the game executable.
        Returns (success, executable_name or None)
        """
        executables_to_try = ["lgc_api.exe", "Korabli.exe", "WorldOfWarships.exe"]

        for exe in executables_to_try:
            exe_path = self.path / exe
            if exe_path.is_file():
                try:
                    log(f"Attempting to launch: {exe_path}")
                    subprocess.Popen([str(exe_path)], cwd=str(self.path))
                    return True, exe
                except Exception as e:
                    log(f"Failed to start {exe}: {e}")
                    # Try the next one

        log(f"Error: Could not find any of {executables_to_try} in {self.path}")
        return False, None  # Failed to find any