import locale
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Set, Dict

base_path: Path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))

major2exact: Dict[str, str] = {
    'zh': 'zh_CN'
}


def get_system_language_codes() -> Tuple[Optional[str], Optional[str]]:
    try:
        default_locale = locale.getdefaultlocale()
        if default_locale and default_locale[0]:
            exact_lang = default_locale[0].replace('-', '_')
            major_lang = exact_lang.split('_')[0].lower()
            return exact_lang, major_lang

    except Exception as e:
        print(f'Error getting system locale: {e}')
        return None, None

    return None, None


'''
Returns sets of exact languages and major languages.
'''


def gather_locales() -> Tuple[Set[str], Set[str]]:
    exact = set([])
    major = set([])
    for _locale in os.listdir(base_path.joinpath('resources/locales')):
        if not _locale.endswith('.json'):
            continue
        _locale = _locale.replace('.json', '')
        exact.add(_locale)
        major.add(_locale.split('_')[0])
    return exact, major


def select_locale_by_system_lang_code():
    exact, major = get_system_language_codes()
    available_exact, available_major = gather_locales()
    if exact and exact in available_exact:
        return exact
    elif major and major in available_major:
        return major2exact.get(major, 'en')
    else:
        return 'en'


# --- (已修改：简化逻辑) ---
def determine_default_l10n_lang(ui_lang: str) -> str:
    """
    根据 UI 语言确定默认的*本地化*语言。
    (不再需要 instance_type)
    """
    # 映射 UI 语言 (zh_CN) -> 本地化语言 (zh_CN)
    # (之后可以添加 'zh_TW': 'zh_TW' 等)
    mapping = {
        'zh_CN': 'zh_CN',
        'en': 'en'
    }

    # 回退到 'en'
    return mapping.get(ui_lang, 'en')