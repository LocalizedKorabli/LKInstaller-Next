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
from typing import Dict, Optional, List

from localizer import _

MODS_URL_CHS = 'https://tapio.lanzn.com/b0nxzso2b'
MODS_URL_EN = None
MODS_URL_CHT = None
MODS_URL_JA = None

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

# 4. 日语路由
JA_LIVE_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja/-/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA/raw/main/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}
JA_PT_ROUTES = {
    'gitlab': {
        'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja-pt/-/raw/main/Localizations/latest/global.mo',
        'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja-pt/-/raw/main/Localizations/latest/version.info',
        'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-ja-pt/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    },
    'github': {
        'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA-PT/raw/main/Localizations/latest/global.mo',
        'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA-PT/raw/main/Localizations/latest/version.info',
        'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-JA-PT/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
    }
}

# 5. 字体包路由 (SrcWagon)
FONTS_SRCWAGON_ROUTES = {
    'tencent': {
        'zip': 'http://lk-1251573974.cos.accelerate.myqcloud.com/fonts/srcwagon/SrcWagon-MK.zip',
        'version': 'http://lk-1251573974.cos.accelerate.myqcloud.com/fonts/srcwagon/version_info.json'
    },
    "cloudflare": {
        'zip': "https://dl.localizedkorabli.org/fonts/srcwagon/SrcWagon-MK.zip",
        'version': "https://dl.localizedkorabli.org/fonts/srcwagon/version_info.json"
    }
}

# 6. 软件本体更新路由 (LKI Next)
LKI_UPDATE_ROUTES = {
    'tencent': {
        'version': "http://lk-1251573974.cos.accelerate.myqcloud.com/lki/lk-next/version_info.json",
        'download': "http://lk-1251573974.cos.accelerate.myqcloud.com/lki/lk-next/lki_setup.exe"
    },
    'cloudflare': {
        'version': "https://dl.localizedkorabli.org/lki/lk-next/version_info.json",
        'download': "https://dl.localizedkorabli.org/lki/lk-next/lki_setup.exe"
    }
}

def get_route_id_to_name():
    return {
        'gitee': _('lki.i18n.route.gitee'),
        'gitlab': _('lki.i18n.route.gitlab'),
        'github': _('lki.i18n.route.github'),
        'cloudflare': _('lki.i18n.route.cloudflare'),
        'tencent': _('lki.i18n.route.tencent')
    }

class LocalizationSource:
    """存储一个可安装本地化包的数据。"""

    def __init__(self, source_id: str, name_key: str,
                 routes_live: dict, routes_pt: dict,
                 mods_url: Optional[str],
                 requires_fonts: bool):
        self.id = source_id
        self.name_key = name_key

        self.routes = {
            'production': routes_live,
            'pts': routes_pt
        }
        self.mods_url = mods_url
        self.requires_fonts = requires_fonts

    def get_routes_for_type(self, instance_type: str = 'production') -> Optional[dict]:
        """获取 'production' 或 'pts' 的下载路由字典"""
        return self.routes.get(instance_type)

    def get_urls(self, instance_type: str, route_id: str) -> Optional[Dict[str, str]]:
        """
        根据实例类型和下载线路，获取 MO, EE 和 Version 的 URL。
        返回: {'mo': 'url', 'ee': 'url', 'version': 'url'}
        """
        routes_for_type = self.get_routes_for_type(instance_type)
        if routes_for_type:
            # (回退到第一个可用的路由)
            return routes_for_type.get(route_id)
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

        # 4. 日语
        self.add_source(
            source_id="ja",
            name_key="lki.i18n.lang.ja.name",
            routes_live=JA_LIVE_ROUTES,
            routes_pt=JA_PT_ROUTES,
            mods_url=MODS_URL_JA,
            requires_fonts=True
        )

        # 注册全局资产 (字体包)
        # 使用上面定义的全局常量，而不是硬编码
        self.global_assets["fonts_srcwagon"] = FONTS_SRCWAGON_ROUTES

    def add_source(self, source_id: str, name_key: str, routes_live: dict, routes_pt: dict,
                   mods_url: Optional[str], requires_fonts: bool):
        self.sources[source_id] = LocalizationSource(source_id, name_key, routes_live, routes_pt, mods_url,
                                                     requires_fonts)

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

    def get_all_available_route_ids(self) -> List[str]:
        """获取 *所有* 来源中 *所有* 可用的唯一路由 ID。"""
        all_keys = set()
        for source in self.sources.values():
            for route_dict in source.routes.values():
                all_keys.update(route_dict.keys())

        for asset in self.global_assets.values():
            all_keys.update(asset.keys())

        all_keys.update(LKI_UPDATE_ROUTES.keys())

        return sorted(list(all_keys))

    def get_mods_url(self, source_id: str) -> Optional[str]:
        """获取一个本地化来源的 mods 下载 URL"""
        source = self.get_source(source_id)
        if source:
            return source.mods_url
        return None

    def get_global_asset_urls(self, asset_id: str, route_id: str) -> Optional[Dict[str, str]]:
        """
        获取一个全局资产（如字体）的 URL 字典。
        """
        asset_routes = self.global_assets.get(asset_id)
        if asset_routes:
            return asset_routes.get(route_id, next(iter(asset_routes.values()), None))
        return None

    def lang_code_requires_fonts(self, lang_code: str) -> bool:
        """
        检查一个语言代码是否可能需要字体包。
        """
        # May reactivate this
        # source = self.get_source(lang_code)
        # if source:
        #    return source.requires_fonts
        return False


# 全局实例
global_source_manager = SourceManager()