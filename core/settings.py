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
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional  # (确保导入 Optional)

# (新增导入)
import platform

try:
    import winreg
except ImportError:
    winreg = None  # 保证在非 Windows 系统或 pywin32 未安装时不会崩溃

# (修改：导入 localizer 以便验证语言)
try:
    import keyring
except Exception as _keyring_err:
    keyring = None
    # 不用 log()，此时 logger 可能尚未初始化；写 stderr 供日志捕获
    import sys as _sys
    _sys.stderr.write(f"Warning: keyring import failed, proxy credentials disabled: {_keyring_err}\n")

from core.utils import select_locale_by_system_lang_code, get_system_language_codes, is_system_gmt8_timezone, is_running_as_msix
from core.dirs import SETTINGS_DIR
from core.localizer import get_available_languages
from core.logger import log

PROXY_KEYRING_SERVICE = "LKInstallerNext"


def save_proxy_credentials(user: str, password: str) -> None:
    """将代理凭据存入 Windows Credential Manager（通过 keyring）。"""
    if not keyring:
        return
    try:
        keyring.set_password(PROXY_KEYRING_SERVICE, "proxy_user", user)
        keyring.set_password(PROXY_KEYRING_SERVICE, "proxy_password", password)
    except Exception as e:
        log(f"Warning: Could not save proxy credentials to keyring: {e}")


def load_proxy_credentials() -> tuple:
    """从 Windows Credential Manager 读取代理凭据，返回 (user, password)。"""
    if not keyring:
        return "", ""
    try:
        user = keyring.get_password(PROXY_KEYRING_SERVICE, "proxy_user") or ""
        password = keyring.get_password(PROXY_KEYRING_SERVICE, "proxy_password") or ""
        return user, password
    except Exception as e:
        log(f"Warning: Could not load proxy credentials from keyring: {e}")
        return "", ""


settings_path: Path = SETTINGS_DIR / 'global.json'


# (新增辅助函数)
def _read_installer_language_from_registry() -> Optional[str]:
    """
    尝试从 HKLM 读取 Inno Setup 安装程序设置的语言代码。
    """
    if platform.system() != "Windows" or not winreg:
        return None

    try:
        # HKLM 需要管理员权限才能写入, 但所有用户通常都可以读取
        key_path = r'Software\LocalizedKorabli\LKInstallerNext'
        # (使用 64 位注册表视图)
        key_flags = winreg.KEY_READ | winreg.KEY_WOW64_64KEY

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, key_flags) as key:
            value, reg_type = winreg.QueryValueEx(key, 'InstallLanguage')
            if reg_type == winreg.REG_SZ:
                log(f"Read language from installer registry: {value}")
                return value
    except FileNotFoundError:
        # 键或值不存在, 这是正常的 (例如在开发环境中)
        log("Installer language registry key not found (normal for dev).")
    except Exception as e:
        log(f"Warning: Could not read installer language from registry: {e}")

    return None


class GlobalSettings:
    def __init__(self):
        from installation.localization_sources import global_source_manager
        all_available_routes = global_source_manager.get_all_available_route_ids()

        # Define route priority by timezone and language
        exact_lang, _ = get_system_language_codes()
        is_gmt8 = is_system_gmt8_timezone()

        if exact_lang == 'zh_CN' and is_gmt8:
            preferred_routes = ['tencent', 'cloudflare', 'gitee', 'gitlab', 'github']
        else:
            preferred_routes = ['cloudflare', 'gitlab', 'github', 'tencent', 'gitee']

        default_route_priority = list(preferred_routes)
        for route in all_available_routes:
            if route not in default_route_priority:
                default_route_priority.append(route)

        system_default_lang = select_locale_by_system_lang_code()

        defaults = {
            'language': system_default_lang,
            'theme': 'light',
            'proxy': {
                'mode': 'system',
                'host': '',
                'port': '',
                'user': '',
                'password': ''
            },
            'ever_launched': False,
            'download_routes_priority': default_route_priority,
            'checked_instance_ids': []
        }

        saved_data: Dict[str, Any] = {}
        if settings_path.is_file():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            except Exception as ex:
                log(f'Failed to load global settings: {ex}')

        is_first_launch = not saved_data.get('ever_launched', False)

        if is_first_launch and not is_running_as_msix():
            log("First launch detected, checking for installer language...")
            installer_lang = _read_installer_language_from_registry()

            if installer_lang:
                # 验证该语言是否在 'resources/locales' 中存在
                available_langs = get_available_languages()  # 返回 {code: name}
                if installer_lang in available_langs:
                    log(f"Setting default language from installer registry: {installer_lang}")
                    # 覆盖掉 system_default_lang
                    defaults['language'] = installer_lang
                else:
                    log(f"Warning: Installer language '{installer_lang}' is not available, falling back to system default.")

        self.data = defaults

        # (下面的逻辑保持不变，它会优先加载已保存的 global.json)
        if 'language' in saved_data:
            self.data['language'] = saved_data['language']
        if 'theme' in saved_data:
            self.data['theme'] = saved_data['theme']

        # ... (其余的加载逻辑) ...
        if 'proxy' in saved_data:
            self.data['proxy'].update(saved_data.get('proxy', {}))

        # 从 Credential Manager 加载代理凭据（用户名和密码均不写入 JSON）
        keyring_user, keyring_password = load_proxy_credentials()
        # 回退到 JSON 中的旧值（迁移兼容：旧版本可能将 user 写在 JSON 里）
        mem_user = keyring_user or self.data['proxy'].get('user', '')
        mem_password = keyring_password or self.data['proxy'].get('password', '')
        self.data['proxy']['user'] = mem_user
        self.data['proxy']['password'] = mem_password
        # 若凭据来自旧 JSON 而非 keyring，自动迁移到 Credential Manager
        if (not keyring_user and mem_user) or (not keyring_password and mem_password):
            save_proxy_credentials(mem_user, mem_password)

        if 'ever_launched' in saved_data:
            self.data['ever_launched'] = saved_data['ever_launched']

        if 'download_routes_priority' in saved_data:
            self.data['download_routes_priority'] = saved_data['download_routes_priority']

        if 'checked_instance_ids' in saved_data:
            self.data['checked_instance_ids'] = saved_data['checked_instance_ids']

        migration_needs_save = False
        current_routes = self.data['download_routes_priority']
        for route in all_available_routes:
            if route not in current_routes:
                log(f"Migrating settings: adding new route '{route}'")
                current_routes.append(route)
                migration_needs_save = True

        if migration_needs_save:
            log("Saving migrated settings...")
            self.save()

    # ... (GlobalSettings 的其余部分保持不变) ...
    @property
    def language(self):
        """提供 settings.global_settings.language 的直接访问"""
        return self.data.get('language', 'en')

    @language.setter
    def language(self, value):
        """提供 settings.global_settings.language 的直接设置"""
        self.data['language'] = value

    def get(self, key: str, default: Any = None) -> Any:
        """按键获取设置值，支持点号访问嵌套字典"""
        if '.' not in key:
            return self.data.get(key, default)

        current = self.data
        try:
            for part in key.split('.'):
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """按键设置值，支持点号访问嵌套字典"""
        if '.' not in key:
            self.data[key] = value
            return

        current = self.data
        parts = key.split('.')
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def save(self):
        """将所有设置保存到 JSON 文件（代理密码不写入 JSON）"""
        import copy
        try:
            os.makedirs(settings_path.parent, exist_ok=True)
            data_to_save = copy.deepcopy(self.data)
            proxy = data_to_save.get('proxy', {})
            proxy.pop('user', None)
            proxy.pop('password', None)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Warning: Could not save global settings: {e}")


global_settings = GlobalSettings()
