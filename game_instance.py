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

    def __init__(self, version: str, files: Dict[str, str]):
        self.version: str = version
        self.files: Dict[str, str] = files


class GameVersion:
    """
    代表一个单独的游戏版本，对应于 "bin/" 目录下的一个数字文件夹。
    """

    # (已修改：__init__ 现在需要 game_root_path)
    def __init__(self, bin_folder_path: Path, game_root_path: Path):
        self.bin_folder_path: Path = bin_folder_path
        self.game_root_path: Path = game_root_path  # <-- (新增)
        self.bin_folder_name: str = bin_folder_path.name
        self.exe_version: Optional[str] = None
        self.l10n_info: Optional[LocalizationInfo] = None

        self.load_details()

    def load_details(self):
        """加载此版本的所有动态属性"""
        self.exe_version = self._load_exe_version()
        self.l10n_info = self._load_l10n_info()

    def _load_exe_version(self) -> Optional[str]:
        """
        从 bin64/Korabli64.exe 中提取文件版本 (a.b)
        """
        exe_path = self.bin_folder_path / "bin64" / "Korabli64.exe"
        if not exe_path.is_file():
            exe_path = self.bin_folder_path / "bin64" / "WorldOfWarships64.exe"
            if not exe_path.is_file():
                print(f"Warning: Did not find Korabli64.exe or WorldOfWarships64.exe in {self.bin_folder_path}")
                return None

        try:
            info = win32api.GetFileVersionInfo(str(exe_path), '\\')
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']

            major = (ms >> 16) & 0xffff
            minor = (ms >> 0) & 0xffff

            return f"{major}.{minor}"

        except Exception as e:
            print(f"Error reading exe version from {exe_path}: {e}")
            return None

    # (已修改：使用新的 info 路径)
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
                files=data.get("files", {})
            )
        except Exception as e:
            print(f"Error loading {info_path}: {e}")
            return None

    # (已修改：使用 self.game_root_path)
    def verify_files(self) -> bool:
        """
        验证 l10n_info 中的所有文件哈希值是否与磁盘上的文件匹配。
        """
        if not self.l10n_info:
            return False

        if not self.l10n_info.files:
            return False

        for relative_path, expected_hash in self.l10n_info.files.items():
            # 相对路径是相对于游戏根目录 (e.g., bin/12345/res_mods/...)
            absolute_path = self.game_root_path / relative_path

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
                    # (已修改：传递 self.path)
                    self.versions.append(GameVersion(folder_path, self.path))

        self.versions.sort(key=lambda v: v.exe_version or "0.0", reverse=True)

    def get_latest_version(self) -> Optional[GameVersion]:
        """
        获取最新的（基于 .exe 版本号） GameVersion。
        """
        if not self.versions:
            return None
        return self.versions[0]