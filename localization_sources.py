import utils
from localizer import _
from typing import Dict, Optional, List

# --- (链接定义保持不变) ---
EE_PACK_URL = 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N/raw/main/BuiltInMods/LKExperienceEnhancement.zip'

MO_ROUTES_CHS_LIVE = {
    'gitee': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/',
    'gitlab': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n/-/raw/main/Localizations/latest/',
    'github': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/'
}

MO_ROUTES_CHS_PT = {
    'gitee': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/',
    'gitlab': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n-publictest/-/raw/Localizations/Localizations/latest/',
    'github': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/'
}

MO_ROUTES_EN_LIVE = {
    'gitlab': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/Localizations/latest/',
    'github': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/Localizations/latest/'
}

MO_ROUTES_EN_PT = {
    'gitlab': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/Localizations/latest/',
    'github': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/Localizations/latest/'
}


# --- (链接定义结束) ---


class LocalizationSource:
    """存储一个可安装本地化包的数据。"""

    def __init__(self, source_id: str, name_key: str,
                 mo_routes_live: dict, mo_routes_pt: dict, ee_url: Optional[str]):
        self.id = source_id
        self.name_key = name_key

        self.mo_routes = {
            'production': mo_routes_live,
            'pts': mo_routes_pt
        }
        self.ee_url = ee_url

    def get_routes_for_type(self, instance_type: str = 'production') -> Optional[dict]:
        """获取 'production' 或 'pts' 的下载路由"""
        return self.mo_routes.get(instance_type)


class SourceManager:
    """管理所有可用的本地化来源。"""

    def __init__(self):
        self.sources: Dict[str, LocalizationSource] = {}
        self._register_sources()

    def _register_sources(self):
        # 1. 简体中文 (包含 live 和 pt 路由)
        self.add_source(
            source_id="zh_CN",
            name_key="l10n.zh_CN.name",
            mo_routes_live=MO_ROUTES_CHS_LIVE,
            mo_routes_pt=MO_ROUTES_CHS_PT,
            ee_url=EE_PACK_URL
        )

        # 2. 英文 (包含 live 和 pt 路由)
        self.add_source(
            source_id="en",
            name_key="l10n.en.name",
            mo_routes_live=MO_ROUTES_EN_LIVE,
            mo_routes_pt=MO_ROUTES_EN_PT,
            ee_url=None
        )

    def add_source(self, source_id: str, name_key: str, mo_routes_live: dict, mo_routes_pt: dict,
                   ee_url: Optional[str]):
        self.sources[source_id] = LocalizationSource(source_id, name_key, mo_routes_live, mo_routes_pt, ee_url)

    def get_source(self, source_id: str) -> Optional[LocalizationSource]:
        return self.sources.get(source_id)

    def get_all_sources(self) -> Dict[str, LocalizationSource]:
        return self.sources

    def get_display_maps(self) -> (dict, dict):
        """
        返回 (id_to_name, name_to_id) 映射表，用于UI显示。
        """
        id_to_name = {}
        name_to_id = {}
        for source_id, source_data in self.sources.items():
            display_name = _(source_data.name_key)
            id_to_name[source_id] = display_name
            name_to_id[display_name] = source_id
        return id_to_name, name_to_id

    # --- (新增) ---
    def get_routes_for_source(self, source_id: str) -> List[str]:
        """获取一个本地化来源可用的下载线路列表 (例如 ['gitee', 'gitlab'])"""
        source = self.get_source(source_id)
        if not source:
            return ['gitee']  # 安全回退

        # 假设 production 和 pts 具有相同的路由键 (gitee, gitlab...)
        routes_dict = source.mo_routes.get('production')
        if not routes_dict:
            return ['gitee']  # 安全回退

        return list(routes_dict.keys())
    # --- (新增结束) ---


# 全局实例
global_source_manager = SourceManager()