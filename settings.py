import json
import os
import uuid  # <-- 新增
from pathlib import Path
from typing import Dict, Any

from utils import select_locale_by_system_lang_code

settings_path: Path = Path('settings/global.json')


class GlobalSettings:
    def __init__(self):

        defaults = {
            'language': select_locale_by_system_lang_code(),
            'theme': 'light',
            'proxy': {
                'mode': 'disabled',
                'host': '',
                'port': '',
                'user': '',
                'password': ''
            },
            'presets': {
                "default": {
                    "name_key": "lki.preset.default.name",
                    "lang_code": "en",  # 默认预设的默认语言
                    "is_default": True  # <-- 新增：防止删除/重命名
                }
            }
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

        if 'presets' in saved_data:
            self.data['presets'].update(saved_data.get('presets', {}))

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

    # --- (新增：预设管理方法) ---
    def add_preset(self, name: str, lang_code: str) -> str:
        """创建一个新的自定义预设并返回其 ID"""
        preset_id = str(uuid.uuid4())
        self.data['presets'][preset_id] = {
            "name": name,
            "lang_code": lang_code,
            "is_default": False
        }
        self.save()
        return preset_id

    def update_preset_data(self, preset_id: str, new_data: Dict[str, Any]):
        """更新一个预设的数据（例如，更改 lang_code）"""
        if preset_id in self.data['presets']:
            self.data['presets'][preset_id].update(new_data)
            self.save()

    def rename_preset(self, preset_id: str, new_name: str):
        """重命名一个自定义预设"""
        if preset_id in self.data['presets'] and not self.data['presets'][preset_id].get('is_default'):
            self.data['presets'][preset_id]['name'] = new_name
            self.save()

    def delete_preset(self, preset_id: str):
        """删除一个自定义预设"""
        if preset_id in self.data['presets'] and not self.data['presets'][preset_id].get('is_default'):
            del self.data['presets'][preset_id]
            self.save()
    # --- (新增结束) ---


global_settings = GlobalSettings()