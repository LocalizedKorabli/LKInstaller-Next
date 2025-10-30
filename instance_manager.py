import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

import utils  # 用于 utils.base_path

# 你的请求：与 settings.json 放在同一目录
instances_path: Path = Path('settings/instances.json')


class InstanceManager:
    def __init__(self):
        self.instances: Dict[str, Any] = {}
        self.load()

    def _generate_id(self, path: str) -> str:
        """使用 sha256(path) 作为实例的唯一键"""
        # 规范化路径以确保一致性 (例如 C:/Games 和 C:\Games 应相同)
        normalized_path = os.path.normpath(os.path.abspath(path))
        return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()

    def load(self):
        """从 instances.json 加载实例字典"""
        if instances_path.is_file():
            try:
                with open(instances_path, 'r', encoding='utf-8') as f:
                    self.instances = json.load(f)
            except Exception as ex:
                print(f'Failed to load instances: {ex}')
                self.instances = {}
        else:
            self.instances = {}

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

    def add_instance(self, name: str, path: str, type: str, preset: str) -> str:
        """
        添加一个新实例。如果路径已存在，则不执行任何操作。
        返回实例 ID。
        """
        instance_id = self._generate_id(path)
        if instance_id in self.instances:
            # 路径已存在，不覆盖
            return instance_id

        self.instances[instance_id] = {
            "name": name,  # 将来用于重命名
            "path": path,
            "type": type,  # 'production' 或 'pts'
            "preset": preset  # 默认预设
        }
        self.save()
        return instance_id

    def update_instance(self, instance_id: str, data: Dict[str, Any]):
        """更新现有实例的键/值（例如更改 'preset'）"""
        if instance_id not in self.instances:
            print(f"Error: Cannot update non-existent instance {instance_id}")
            return

        self.instances[instance_id].update(data)
        self.save()  # 自动保存


# 全局实例
global_instance_manager = InstanceManager()