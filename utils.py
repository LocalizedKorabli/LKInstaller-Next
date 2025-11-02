import locale
import os
import sys
import tkinter
import time
from pathlib import Path
from typing import Optional, Tuple, List, Set, Dict

base_path: Path = Path(getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__))))

major2exact: Dict[str, str] = {
    'zh': 'zh_CN',
    'en': 'en'
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


# --- (新增：时区检查) ---
def is_system_gmt8_timezone() -> bool:
    """检查本地系统时区是否为 GMT+8。"""
    try:
        # time.timezone 返回 UTC 以西的偏移秒数。
        # 对于 GMT+8（中国），在非夏令时期间，该值应为 -28800。
        is_dst = time.daylight and time.localtime().tm_isdst
        offset_seconds = -time.altzone if is_dst else -time.timezone

        if offset_seconds == 28800:  # 8 * 60 * 60
            return True
    except Exception as e:
        print(f"Error checking timezone: {e}")
    return False


# --- (新增结束) ---


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

def scale_dpi(widget: tkinter.Misc, value: int) -> int:
    """
    使用存储在 Toplevel 上的缩放因子来缩放像素值。
    """
    try:
        # 获取存储在根窗口上的 scaling_factor
        scaling_factor = widget.winfo_toplevel().scaling_factor
        return int(value * scaling_factor)
    except Exception:
        # 如果 scaling_factor 不存在，则回退
        return value