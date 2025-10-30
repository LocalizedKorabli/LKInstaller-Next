import json
import os
import glob
import settings
import utils

locales_dir = utils.base_path.joinpath('resources/locales')

class Localizer:
    def __init__(self, lang='en'):
        self.translations = {}
        self.current_lang = lang
        self.load_language(lang)

    def load_language(self, language_code):
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
            print(f"Loaded language: {language_code}")
        except FileNotFoundError:
            print(f"Warning: Translation file not found for {language_code}. Falling back to default (en).")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {file_path}")

    def gettext(self, text):
        return self.translations.get(text, text)

# (假设 settings.py 已经使用 utils.select_locale_by_system_lang_code() 设置了 language)
global_translator = Localizer(settings.global_settings.language)
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
                print(f"Warning: '{f_path}' 中缺少 'lki.lang.name'。")
        except Exception as e:
            print(f"Error loading locale '{f_path}': {e}")
    return langs
