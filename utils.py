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
