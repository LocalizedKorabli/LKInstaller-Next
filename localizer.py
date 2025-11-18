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
import glob
import json
import os
from typing import Optional, Dict, Tuple

import dirs

from logger import log

locales_dir = dirs.base_path.joinpath('resources/locales')

_best_fonts: Dict[str, Tuple[str, str]] = {
    'zh_CN': ('Segoe UI', 'Microsoft YaHei'),
    'zh_TW': ('Segoe UI', 'Microsoft JhengHei'),
    'en': ('Segoe UI', 'Arial'),
    'ja': ('Yu Gothic', 'MS Gothic'),
    'ru': ('Aptos', 'Arial')
}


class Localizer:
    def __init__(self, lang: Optional[str]):
        self.translations = {}
        self.current_lang = lang
        self.load_language(lang)

    def load_language(self, language_code: Optional[str]):
        should_log = True
        if language_code is None:
            language_code = 'en'
            should_log = False
        file_path = os.path.join(locales_dir, f"{language_code}.json")
        default_file = os.path.join(locales_dir, 'en.json')
        try:
            with open(default_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            if language_code != 'en':
                with open(file_path, 'r', encoding='utf-8') as f:
                    target_translations = json.load(f)
                    self.translations.update(target_translations)
            self.current_lang = language_code
            if should_log:
                log(f"Loaded language: {language_code}")
        except FileNotFoundError:
            log(f"Warning: Translation file not found for {language_code}. Falling back to default (en).")
        except json.JSONDecodeError:
            log(f"Error: Invalid JSON format in {file_path}")

    def gettext(self, text):
        return self.translations.get(text, text)

    # Currently not used
    def get_language_defined_best_fonts(self) -> Tuple[str, str]:
        return _best_fonts.get(self.current_lang, ('Segoe UI', 'Microsoft YaHei'))

global_translator = Localizer(None)
_ = global_translator.gettext


def get_available_languages():
    """
    扫描 'resources/locales' 文件夹，加载 JSON，并返回一个 {code: name} 字典。
    """
    langs = {}
    for f_path in glob.glob(os.path.join(locales_dir, '*.json')):
        try:
            locale_code = os.path.basename(f_path).split('.')[0]
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            lang_name = data.get('lki.lang.name')
            if lang_name:
                langs[locale_code] = lang_name
            else:
                log(f"Warning: '{f_path}' 中缺少 'lki.lang.name'。")
        except Exception as e:
            log(f"Error loading locale '{f_path}': {e}")
    return langs
