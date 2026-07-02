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

from core.localizer import _

# ── 各语言的 mods 下载 URL ──
MODS_URLS = {
    "chs": 'https://tapio.lanzn.com/b0nxzso2b',
    "en": None,
    "de": None,
    "es": None,
    "cht": None,
    "ja": None,
}

# ── 本地化包下载路由 ──
LANG_ROUTES = {
    "chs": {
        "production": {
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
        },
        "pts": {
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
    },
    "en": {
        "production": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        },
        "pts": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-lesta-i18n-publictest/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-LESTA-I18N-PublicTest/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        }
    },
    "de": {
        "production": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-de/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-de/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-de/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        },
        "pts": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-de-pt/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-de-pt/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-de-pt/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE-PT/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE-PT/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-DE-PT/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        }
    },
    "es": {
        "production": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-es/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-es/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-es/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        },
        "pts": {
            'gitlab': {
                'mo': 'https://gitlab.com/localizedkorabli/korabli-i18n-es-pt/-/raw/main/Localizations/latest/global.mo',
                'version': 'https://gitlab.com/localizedkorabli/korabli-i18n-es-pt/-/raw/main/Localizations/latest/version.info',
                'ee': 'https://gitlab.com/localizedkorabli/korabli-i18n-es-pt/-/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            },
            'github': {
                'mo': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES-PT/raw/main/Localizations/latest/global.mo',
                'version': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES-PT/raw/main/Localizations/latest/version.info',
                'ee': 'https://github.com/LocalizedKorabli/Korabli-I18n-ES-PT/raw/main/BuiltInMods/LKExperienceEnhancement.zip'
            }
        }
    },
    "cht": {
        "production": {
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
        },
        "pts": {
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
    },
    "ja": {
        "production": {
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
        },
        "pts": {
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
    },
}

# 5. 字体包路由
# 元数据（所有字体版本信息汇总在一个 metadata.json）
FONTS_METADATA_URL = "https://localizedkorabli.org/metadata/fonts/metadata.json"
# 下载链接模板（{font_id} 替换为具体字体 ID，如 SrcHelios-MainlandCN）
FONTS_DOWNLOAD_URL_TEMPLATE = "https://dl.localizedkorabli.org/fonts/{font_id}.7z"

FONTS_ROUTES = {
    "cloudflare": {
        'metadata': FONTS_METADATA_URL,
        'download_template': FONTS_DOWNLOAD_URL_TEMPLATE
    }
}

# 可用字体 ID 列表
FONT_IDS = [
    "SrcWagon-MainlandCN",
    "SrcWagon-TWProvince",
    "SrcWagon-HKSAR",
    "SrcWagon-JP",
    "SrcHelios-MainlandCN",
]

# 字体 ID → UI 显示键 映射
FONT_DISPLAY_KEYS = {
    "SrcWagon-MainlandCN": "lki.preset.manager.font_opt.SrcWagon-MainlandCN",
    "SrcWagon-TWProvince": "lki.preset.manager.font_opt.SrcWagon-TWProvince",
    "SrcWagon-HKSAR": "lki.preset.manager.font_opt.SrcWagon-HKSAR",
    "SrcWagon-JP": "lki.preset.manager.font_opt.SrcWagon-JP",
    "SrcHelios-MainlandCN": "lki.preset.manager.font_opt.SrcHelios-MainlandCN",
}

# 语言 → 默认推荐字体 ID 映射
LANG_DEFAULT_FONT = {
    "zh_CN": "SrcWagon-MainlandCN",
    "zh_TW": "SrcWagon-TWProvince",
    "ja": "SrcWagon-JP",
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
                 mods_url: Optional[str]):
        self.id = source_id
        self.name_key = name_key

        self.routes = {
            'production': routes_live,
            'pts': routes_pt
        }
        self.mods_url = mods_url

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
        # 语言简码 → 内部 source_id 映射
        lang_to_id = {"chs": "zh_CN", "en": "en", "de": "de", "es": "es", "cht": "zh_TW", "ja": "ja"}
        for code, routes in LANG_ROUTES.items():
            self.add_source(
                source_id=lang_to_id[code],
                name_key=f"lki.i18n.lang.{lang_to_id[code]}.name",
                routes_live=routes["production"],
                routes_pt=routes["pts"],
                mods_url=MODS_URLS.get(code),
            )

        # 注册全局资产 (字体包)
        self.global_assets["fonts"] = FONTS_ROUTES

    def add_source(self, source_id: str, name_key: str, routes_live: dict, routes_pt: dict,
                   mods_url: Optional[str]):
        self.sources[source_id] = LocalizationSource(source_id, name_key, routes_live, routes_pt, mods_url)

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

    def get_default_font_id(self, lang_code: str) -> str:
        """返回指定语言推荐安装的字体 ID，空字符串表示不安装字体。"""
        return LANG_DEFAULT_FONT.get(lang_code, "")


# 全局实例
global_source_manager = SourceManager()
