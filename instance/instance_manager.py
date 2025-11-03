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

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import utils
from localization_sources import global_source_manager  # (确保这个导入存在)
from utils import determine_default_l10n_lang, SETTINGS_DIR

instances_path: Path = SETTINGS_DIR / 'instances.json'


class InstanceManager:
    def __init__(self):
        self.instances: Dict[str, Any] = {}
        self.load()

    def _generate_id(self, path: str) -> str:
        """使用 sha256(path) 作为实例的唯一键"""
        normalized_path = os.path.normpath(os.path.abspath(path))
        return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()

    # --- (已修改：采纳您的建议，使其具有语言依赖性) ---
    def _get_default_preset_data(self, lang_code: str) -> Dict[str, Any]:
        """
        返回一个标准的“默认预设”字典结构。
        'use_fonts' 的值取决于语言。
        """

        # (修改：从 localization_sources 查询默认值)
        # 我们假设 global_source_manager 现在有这个方法
        try:
            default_fonts = global_source_manager.lang_code_requires_fonts(lang_code)
        except AttributeError:
            print(f"Warning: global_source_manager.lang_code_requires_fonts() not found. Defaulting use_fonts to True.")
            default_fonts = True  # (回退到旧逻辑)
        except Exception as e:
            print(f"Error checking font requirement for {lang_code}: {e}. Defaulting use_fonts to True.")
            default_fonts = True

        return {
            "name_key": "lki.preset.default.name",
            "lang_code": lang_code,
            "use_ee": True,
            "use_mods": True,
            "use_fonts": default_fonts,  # (已修改)
            "is_default": True
        }

    # --- (修改结束) ---

    def load(self):
        """从 instances.json 加载实例字典并迁移旧数据"""
        if instances_path.is_file():
            try:
                with open(instances_path, 'r', encoding='utf-8') as f:
                    self.instances = json.load(f)
            except Exception as ex:
                print(f'Failed to load instances: {ex}')
                self.instances = {}
        else:
            self.instances = {}

        needs_save = False

        # (已修改：use_fonts 不再是静态默认值)
        component_defaults = {
            "use_ee": True,
            "use_mods": True
            # "use_fonts" 将被单独处理
        }

        for instance_id, data in self.instances.items():
            # (1. 移除旧的路由键)
            for preset_id, preset_data in data.get('presets', {}).items():
                if 'download_route' in preset_data:
                    del preset_data['download_route']
                    needs_save = True
                if 'download_routes' in preset_data:
                    del preset_data['download_routes']
                    needs_save = True

            # (2. 检查 'presets' 键是否存在)
            if 'presets' in data:
                # (已修改：迭代检查所有预设)
                for preset_id, preset_data in data.get('presets', {}).items():
                    # (a. 补全静态默认键)
                    for key, default_value in component_defaults.items():
                        if key not in preset_data:
                            print(f"Migrating preset {preset_id} for {instance_id} (adding {key}: {default_value})...")
                            preset_data[key] = default_value
                            needs_save = True

                    # (b. 补全语言相关的 'use_fonts' 键)
                    if 'use_fonts' not in preset_data:
                        # (使用预设中已存的 lang_code 来决定默认值)
                        lang_code = preset_data.get('lang_code', 'en')  # (回退到 'en')
                        try:
                            default_fonts = global_source_manager.lang_code_requires_fonts(lang_code)
                        except Exception:
                            default_fonts = True  # (回退)

                        print(
                            f"Migrating preset {preset_id} for {instance_id} (adding use_fonts: {default_fonts} for lang={lang_code})...")
                        preset_data['use_fonts'] = default_fonts
                        needs_save = True

            else:
                # (3. 'presets' 键完全缺失, 创建全新的默认预设)
                print(f"Migrating old instance data for {instance_id} (creating default preset)...")

                default_lang_code = utils.select_locale_by_system_lang_code()  # (保持 load 方法中的硬编码回退)
                default_preset = self._get_default_preset_data(default_lang_code)

                data['presets'] = {"default": default_preset}
                data['active_preset_id'] = "default"
                needs_save = True

        if needs_save:
            print("Migration complete, saving updated instances.json...")
            self.save()

    def save(self):
        """将当前所有实例保存回 instances.json"""
        os.makedirs(instances_path.parent, exist_ok=True)
        with open(instances_path, 'w', encoding='utf-8') as f:
            json.dump(self.instances, f, indent=2, ensure_ascii=False)

    def get_all(self) -> Dict[str, Any]:
        """获取所有实例的字典"""
        return self.instances

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """按 ID 获取单个实例的数据"""
        return self.instances.get(instance_id)

    def get_active_preset(self, game_root_path: Path) -> Dict[str, Any]:
        """
        (新增) 辅助函数，用于根据实例路径获取其活动的预设数据。
        """
        instance_id = self._generate_id(str(game_root_path))
        instance_data = self.get_instance(instance_id)

        if not instance_data:
            return {}

        presets = instance_data.get('presets', {})
        active_preset_id = instance_data.get('active_preset_id', 'default')

        return presets.get(active_preset_id, {})

    def delete_instance(self, instance_id: str):
        """删除一个实例"""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self.save()

    def _move_instance(self, instance_id: str, direction: int):
        """
        在实例字典中向上 (-1) 或向下 (+1) 移动一个条目。
        """
        if instance_id not in self.instances:
            return

        keys = list(self.instances.keys())
        try:
            index = keys.index(instance_id)
        except ValueError:
            return

        new_index = index + direction

        if new_index < 0 or new_index >= len(keys):
            return

        keys.insert(new_index, keys.pop(index))

        new_instances = {key: self.instances[key] for key in keys}
        self.instances = new_instances
        self.save()

    def move_instance_up(self, instance_id: str):
        """在列表中将实例上移一位"""
        self._move_instance(instance_id, -1)

    def move_instance_down(self, instance_id: str):
        """在列表中将实例下移一位"""
        self._move_instance(instance_id, 1)

    # (已修改：使用 _get_default_preset_data 辅助方法)
    def add_instance(self, name: str, path: str, type: str, current_ui_lang: str) -> str:
        """
        添加一个新实例，并为其创建默认预设。
        """
        instance_id = self._generate_id(path)
        if instance_id in self.instances:
            return instance_id

        default_lang_code = determine_default_l10n_lang(current_ui_lang)

        # (已修改：调用辅助方法，自动获取正确的 use_fonts)
        default_preset_data = self._get_default_preset_data(default_lang_code)

        self.instances[instance_id] = {
            "name": name,
            "path": path,
            "type": type,
            "active_preset_id": "default",
            "presets": {
                "default": default_preset_data
            }
        }
        self.save()
        return instance_id

    def update_instance_data(self, instance_id: str, data: Dict[str, Any]):
        """更新实例的顶层数据（例如 'active_preset_id'）"""
        if instance_id not in self.instances:
            return
        self.instances[instance_id].update(data)
        self.save()

    def add_preset(self, instance_id: str, name: str, lang_code: str, use_ee: bool,
                   use_mods: bool, use_fonts: bool) -> str:
        """为特定实例创建一个新的自定义预设并返回其 ID"""
        if instance_id not in self.instances:
            return None

        self.instances[instance_id].setdefault('presets', {})

        preset_id = str(uuid.uuid4())
        self.instances[instance_id]['presets'][preset_id] = {
            "name": name,
            "lang_code": lang_code,
            "use_ee": use_ee,
            "use_mods": use_mods,
            "use_fonts": use_fonts,
            "is_default": False
        }
        self.save()
        return preset_id

    def update_preset_data(self, instance_id: str, preset_id: str, new_data: Dict[str, Any]):
        """更新特定实例中某个预设的数据（例如，更改 lang_code）"""
        if instance_id in self.instances and preset_id in self.instances[instance_id]['presets']:
            self.instances[instance_id]['presets'][preset_id].update(new_data)
            self.save()

    def rename_preset(self, instance_id: str, preset_id: str, new_name: str):
        """重命名特定实例中的某个自定义预设"""
        if instance_id in self.instances and preset_id in self.instances[instance_id]['presets']:
            preset = self.instances[instance_id]['presets'][preset_id]
            if not preset.get('is_default'):
                preset['name'] = new_name
                self.save()

    def delete_preset(self, instance_id: str, preset_id: str):
        """删除特定实例中的某个自定义预设"""
        if instance_id in self.instances and preset_id in self.instances[instance_id]['presets']:
            preset = self.instances[instance_id]['presets'][preset_id]
            if not preset.get('is_default'):
                del self.instances[instance_id]['presets'][preset_id]
                self.save()


# 全局实例
global_instance_manager = InstanceManager()
