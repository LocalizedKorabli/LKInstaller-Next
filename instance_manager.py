import json
import os
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

import utils
from localizer import _
from utils import determine_default_l10n_lang
from localization_sources import global_source_manager

instances_path: Path = Path('lki/settings/instances.json')


class InstanceManager:
    def __init__(self):
        self.instances: Dict[str, Any] = {}
        self.load()

    def _generate_id(self, path: str) -> str:
        """使用 sha256(path) 作为实例的唯一键"""
        normalized_path = os.path.normpath(os.path.abspath(path))
        return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()

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
        for instance_id, data in self.instances.items():
            # (已修改：移除 download_route 和 download_routes)
            for preset_id, preset_data in data.get('presets', {}).items():
                if 'download_route' in preset_data:
                    print(f"Migrating preset {preset_id} (removing download_route)...")
                    del preset_data['download_route']
                    needs_save = True
                if 'download_routes' in preset_data:
                    print(f"Migrating preset {preset_id} (removing download_routes)...")
                    del preset_data['download_routes']
                    needs_save = True
            # (迁移结束)

            if 'presets' not in data:
                print(f"Migrating old instance data for {instance_id}...")

                default_lang_code = 'zh_CN'

                data['presets'] = {
                    "default": {
                        "name_key": "lki.preset.default.name",
                        "lang_code": default_lang_code,
                        # (download_routes 已移除)
                        "use_ee": True,
                        "use_mods": True,
                        "use_fonts": True, # <-- (新增)
                        "is_default": True
                    }
                }
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

    # (已修改：移除 download_routes)
    def add_instance(self, name: str, path: str, type: str, current_ui_lang: str) -> str:
        """
        添加一个新实例，并为其创建默认预设。
        """
        instance_id = self._generate_id(path)
        if instance_id in self.instances:
            return instance_id

        default_lang_code = determine_default_l10n_lang(current_ui_lang)

        default_preset_data = {
            "name_key": "lki.preset.default.name",
            "lang_code": default_lang_code,
            # (download_routes 已移除)
            "use_ee": True,
            "use_mods": True,
            "use_fonts": True, # <-- (新增)
            "is_default": True
        }

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

    # (已修改：签名变更)
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
            # (download_routes 已移除)
            "use_ee": use_ee,
            "use_mods": use_mods,
            "use_fonts": use_fonts, # <-- (新增)
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