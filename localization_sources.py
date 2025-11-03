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

from typing import Dict, Optional, List

from localizer import _

MODS_URL_CHS = 'https://tapio.lanzn.com/b0nxzso2b'
MODS_URL_EN = None
MODS_URL_CHT = None

# 1. 简体中文路由
CHS_LIVE_ROUTES = {
    'gitee': {
        'mo': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n/-/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N/raw/main/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}
CHS_PT_ROUTES = {
    'gitee': {
        'mo': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/global.mo',
        'version': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/version.info',
        'ee': 'https://gitee.com/localized-korabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n-publictest/-/raw/Localizations/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n-publictest/-/raw/Localizations/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-lesta-l10n-publictest/-/raw/Localizations/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-LESTA-L10N-PublicTest/raw/Localizations/BuiltInMods/LKExperienceEnhancement.zip'
    }
}

# 2. 英文路由
EN_LIVE_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/Localizations/latest/version.info',
        'ee': f'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/Localizations/latest/version.info',
        'ee': f'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}
EN_PT_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/Localizations/latest/version.info',
        'ee': f'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/Localizations/latest/version.info',
        'ee': f'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}

# 3. 繁体中文路由
CHT_LIVE_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht/-/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT/raw/main/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}
CHT_PT_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht-publictest/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht-publictest/-/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-l10n-cht-publictest/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT-PublicTest/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT-PublicTest/raw/main/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-L10n-CHT-PublicTest/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}



class LocalizationSource:
    """存储一个可安装本地化包的数据。"""

    def __init__(self, source_id: str, name_key: str,
                 routes_live: dict, routes_pt: dict,
                 mods_url: Optional[str],
                 requires_fonts: bool):  # <-- (1. 新增参数)
        self.id = source_id
        self.name_key = name_key

        self.routes = {
            'production': routes_live,
            'pts': routes_pt
        }
        self.mods_url = mods_url
        self.requires_fonts = requires_fonts  # <-- (2. 新增属性)

    def get_routes_for_type(self, instance_type: str = 'production') -> Optional[dict]:
        """获取 'production' 或 'pts' 的下载路由字典"""
        return self.routes.get(instance_type)

    # (已修改：现在返回完整的字典)
    def get_urls(self, instance_type: str, route_id: str) -> Optional[Dict[str, str]]:
        """
        根据实例类型和下载线路，获取 MO, EE 和 Version 的 URL。
        返回: {'mo': 'url', 'ee': 'url', 'version': 'url'}
        """
        routes_for_type = self.get_routes_for_type(instance_type)
        if routes_for_type:
            # (回退到第一个可用的路由)
            return routes_for_type.get(route_id, next(iter(routes_for_type.values()), None))
        return None

    def get_available_route_ids(self) -> List[str]:
        """获取此来源所有可用的路由 ID (例如 ['gitee', 'gitlab'])"""
        routes_prod = self.routes.get('production', {})
        routes_pt = self.routes.get('pts', {})

        all_keys = list(routes_prod.keys()) + list(routes_pt.keys())

        unique_keys = []
        for key in all_keys:
            if key not in unique_keys:
                unique_keys.append(key)

        return unique_keys


class SourceManager:
    """管理所有可用的本地化来源。"""

    def __init__(self):
        self.sources: Dict[str, LocalizationSource] = {}
        self.global_assets: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._register_sources()

    def _register_sources(self):
        # 1. 简体中文
        self.add_source(
            source_id="zh_CN",
            name_key="lki.i18n.lang.zh_CN.name",
            routes_live=CHS_LIVE_ROUTES,
            routes_pt=CHS_PT_ROUTES,
            mods_url=MODS_URL_CHS,
            requires_fonts=True
        )

        # 2. 英文
        self.add_source(
            source_id="en",
            name_key="lki.i18n.lang.en.name",
            routes_live=EN_LIVE_ROUTES,
            routes_pt=EN_PT_ROUTES,
            mods_url=MODS_URL_EN,
            requires_fonts=False
        )
        
        # 3. 繁体中文
        self.add_source(
            source_id="zh_TW",
            name_key="lki.i18n.lang.zh_TW.name",
            routes_live=CHT_LIVE_ROUTES,
            routes_pt=CHT_PT_ROUTES,
            mods_url=MODS_URL_CHT,
            requires_fonts=True
        )

        # --- (新增：定义全局资产) ---
        self.global_assets["fonts_srcwagon"] = {
            "cloudflare": {
                "zip": "https://dl.localizedkorabli.org/fonts/srcwagon/SrcWagon-MK.zip",
                "version": "https://dl.localizedkorabli.org/fonts/srcwagon/version_info.json"
            }
            # (你将来可以在这里添加 'gitee', 'gitlab' 等)
        }
        # --- (新增结束) ---

    def add_source(self, source_id: str, name_key: str, routes_live: dict, routes_pt: dict,
                   mods_url: Optional[str], requires_fonts: bool):  # <-- (5. 新增参数)
        self.sources[source_id] = LocalizationSource(source_id, name_key, routes_live, routes_pt, mods_url,
                                                     requires_fonts)  # <-- (6. 传入参数)

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

    def get_routes_for_source(self, source_id: str) -> List[str]:
        """获取一个本地化来源可用的下载线路列表 (例如 ['gitee', 'gitlab'])"""
        source = self.get_source(source_id)
        if not source:
            return ['gitee']

        keys = source.get_available_route_ids()

        if not keys:
            return ['gitee']

        return keys

    def get_all_available_route_ids(self) -> List[str]:
        """获取 *所有* 来源中 *所有* 可用的唯一路由 ID。"""
        all_keys = set()
        for source in self.sources.values():
            for route_dict in source.routes.values():
                all_keys.update(route_dict.keys())

        # (新增) 也包括全局资产的路由
        for asset in self.global_assets.values():
            all_keys.update(asset.keys())

        return sorted(list(all_keys))

    def get_mods_url(self, source_id: str) -> Optional[str]:
        """获取一个本地化来源的 mods 下载 URL"""
        source = self.get_source(source_id)
        if source:
            return source.mods_url
        return None

    # --- (新增：获取全局资产 URL) ---
    def get_global_asset_urls(self, asset_id: str, route_id: str) -> Optional[Dict[str, str]]:
        """
        获取一个全局资产（如字体）的 URL 字典。
        """
        asset_routes = self.global_assets.get(asset_id)
        if asset_routes:
            # (回退到第一个可用的路由)
            return asset_routes.get(route_id, next(iter(asset_routes.values()), None))
        return None

    # --- (新增结束) ---

    # --- (7. 新增您所请求的方法) ---
    def lang_code_requires_fonts(self, lang_code: str) -> bool:
        """
        检查一个语言代码是否默认需要字体包。
        """
        source = self.get_source(lang_code)
        if source:
            return source.requires_fonts  # (在步骤 1 & 2 中添加)

        # (安全回退：如果未指定，则假设需要字体)
        # 这对于迁移旧的、未指定此属性的预设很重要
        return True
    # --- (新增结束) ---


# 全局实例
global_source_manager = SourceManager()
