import os
import json
import hashlib
import win32api  # 用于读取 .exe 版本
from pathlib import Path
from typing import Dict, Any, Optional, List


def _calculate_sha256(filepath: Path) -> Optional[str]:
    """计算文件的 SHA256 哈希值"""
    if not filepath.is_file():
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # 逐块读取以处理大文件
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
        # 字典格式: { "相对路径": "sha256_hash" }
        self.files: Dict[str, str] = files


class GameVersion:
    """
    代表一个单独的游戏版本，对应于 "bin/" 目录下的一个数字文件夹。
    """

    def __init__(self, bin_folder_path: Path):
        self.bin_folder_path: Path = bin_folder_path
        self.bin_folder_name: str = bin_folder_path.name
        self.exe_version: Optional[str] = None  # 格式 "25.11"
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
            # 尝试回退到 WorldOfWarships.exe (适用于 WG 客户端)
            exe_path = self.bin_folder_path / "bin64" / "WorldOfWarships64.exe"
            if not exe_path.is_file():
                print(f"Warning: Did not find Korabli64.exe or WorldOfWarships64.exe in {self.bin_folder_path}")
                return None

        try:
            info = win32api.GetFileVersionInfo(str(exe_path), '\\')
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']

            # 版本号格式为 a.b.c.d
            major = (ms >> 16) & 0xffff
            minor = (ms >> 0) & 0xffff
            # build = (ls >> 16) & 0xffff
            # patch = (ls >> 0) & 0xffff

            # 仅返回 "a.b" 部分
            return f"{major}.{minor}"

        except Exception as e:
            print(f"Error reading exe version from {exe_path}: {e}")
            return None

    def _load_l10n_info(self) -> Optional[LocalizationInfo]:
        """
        从 lki/installation_info.json 加载本地化安装信息。
        """
        info_path = self.bin_folder_path / "lki" / "installation_info.json"
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

    def verify_files(self, game_root_path: Path) -> bool:
        """
        验证 l10n_info 中的所有文件哈希值是否与磁盘上的文件匹配。
        """
        if not self.l10n_info:
            return False  # 没有安装信息

        if not self.l10n_info.files:
            return False  # 有 info 文件但没有文件列表

        for relative_path, expected_hash in self.l10n_info.files.items():
            # 相对路径是相对于游戏根目录 (e.g., bin/12345/res_mods/...)
            absolute_path = game_root_path / relative_path

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
        self.instance_id: str = instance_id  # sha256(path)
        self.path: Path = path
        self.name: str = name  # 用户定义的名称 (e.g., "Mir Korabley Live")
        self.type: str = type  # 'production' 或 'pts'

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
                    self.versions.append(GameVersion(folder_path))

        # 可选：按版本号排序
        self.versions.sort(key=lambda v: v.exe_version or "0.0", reverse=True)

    def get_latest_version(self) -> Optional[GameVersion]:
        """
_load_and_display_instances        获取最新的（基于 .exe 版本号） GameVersion。
        """
        if not self.versions:
            return None
        # 假设列表已经在 _discover_game_versions 中排序
        return self.versions[0]