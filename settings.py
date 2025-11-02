import json
import os
from pathlib import Path
from typing import Dict, Any

# (已修改：导入新函数)
from utils import select_locale_by_system_lang_code, get_system_language_codes, is_system_gmt8_timezone, SETTINGS_DIR

settings_path: Path = SETTINGS_DIR / 'global.json'


class GlobalSettings:
    def __init__(self):
        from localization_sources import global_source_manager
        all_available_routes = global_source_manager.get_all_available_route_ids()
        # --- (新增：首次启动时的区域设置) ---
        exact_lang, _ = get_system_language_codes()
        is_gmt8 = is_system_gmt8_timezone()

        if exact_lang == 'zh_CN' and is_gmt8:
            # 位于中国大陆 (首选)
            preferred_routes = ['cloudflare', 'gitee', 'gitlab']
        else:
            # 位于其他地区 (首选)
            preferred_routes = ['cloudflare', 'gitlab', 'github']

            # (新增) 合并首选路由和剩余路由
        default_route_priority = list(preferred_routes)
        for route in all_available_routes:
            if route not in default_route_priority:
                default_route_priority.append(route)
        # --- (新增结束) ---

        defaults = {
            'language': select_locale_by_system_lang_code(),
            'theme': 'light',
            'proxy': {
                'mode': 'system',
                'host': '',
                'port': '',
                'user': '',
                'password': ''
            },
            'ever_launched': False,
            'download_routes_priority': default_route_priority,  # <-- (已修改)
            'checked_instance_ids': []
        }

        saved_data: Dict[str, Any] = {}
        if settings_path.is_file():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            except Exception as ex:
                print(f'Failed to load global settings: {ex}')

        self.data = defaults

        if 'language' in saved_data:
            self.data['language'] = saved_data['language']
        if 'theme' in saved_data:
            self.data['theme'] = saved_data['theme']

        if 'proxy' in saved_data:
            self.data['proxy'].update(saved_data.get('proxy', {}))

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
                print(f"Migrating settings: adding new route '{route}'")
                current_routes.append(route)
                migration_needs_save = True

        if migration_needs_save:
            print("Saving migrated settings...")
            self.save()

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
        """将所有设置保存到 JSON 文件"""
        os.makedirs(settings_path.parent, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # --- (所有 preset 相关的方法已移除) ---


global_settings = GlobalSettings()
