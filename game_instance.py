import os
import json
import hashlib
import win32api
from pathlib import Path
from typing import Dict, Any, Optional, List


# 注意：这个模块需要 'pywin32'
# 请运行: pip install pywin32

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
        print(f"Error calculating SHA256 for {filepath}: {e}")
        return None


class LocalizationInfo:
    """
    一个数据类，用于保存 installation_info.json 的内容。
    """

    def __init__(self, version: str, files: Dict[str, str], lang_code: Optional[str] = None, l10n_sub_version: Optional[str] = None):
        self.version: str = version
        self.files: Dict[str, str] = files
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
                print(f"Warning: Did not find Korabli64.exe or WorldOfWarships64.exe in {self.bin_folder_path}")
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
            print(f"Error reading exe product version from {exe_path_str}: {e}")
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
            print(f"Error loading {info_path}: {e}")
            return None

    def verify_files(self) -> bool:
        """
        验证 l10n_info 中的所有文件哈希值是否与磁盘上的文件匹配。
        """
        if not self.l10n_info:
            return False

        if self.l10n_info.version == "INACTIVE":
            return True

        if not self.l10n_info.files:
            return False

        for relative_path, expected_hash in self.l10n_info.files.items():

            # --- (这是修复) ---
            # 验证器必须在 mods 目录中查找文件
            absolute_path = self.bin_folder_path / "mods" / relative_path
            # --- (修复结束) ---

            actual_hash = _calculate_sha256(absolute_path)

            if actual_hash != expected_hash:
                print(f"Verification FAILED for {relative_path}: Hash mismatch.")
                return False

        print(f"Verification SUCCESS for version {self.exe_version} ({self.bin_folder_name})")
        return True


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
            print(f"Warning: 'bin' directory not found in {self.path}")
            return

        for folder_name in os.listdir(bin_path):
            if folder_name.isdigit():
                folder_path = bin_path / folder_name
                if folder_path.is_dir():
                    print(f"Found game version folder: {folder_name}")
                    self.versions.append(GameVersion(folder_path, self.path))

        self.versions.sort(key=lambda v: v.exe_version or "0.0", reverse=True)

    def get_latest_version(self) -> Optional[GameVersion]:
        """
        获取最新的（基于 .exe 版本号） GameVersion。
        """
        if not self.versions:
            return None
        return self.versions[0]