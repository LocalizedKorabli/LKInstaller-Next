import os
import shutil
import hashlib
import zipfile
import json
import polib
from pathlib import Path
from typing import Dict, List, Union, Any, Optional, Tuple
import xml.etree.ElementTree as Et

# (来自 installer_gui.py, 已重命名)
BUILTIN_LOCALE_CONFIG_ZH_CN = '''<locale_config>
    <locale_id>ru</locale_id>
    <text_path>../res/texts</text_path>
    <text_domain>global</text_domain>
    <lang_mapping>
        <lang acceptLang="ru" egs="ru" fonts="CN" full="russian" languageBar="true" localeRfcName="ru" short="ru" />
    </lang_mapping>
</locale_config>
'''

# 缓存和临时目录
CACHE_DIR = Path('lki/cache')
TEMP_DIR = Path('lki/temp')
L10N_CACHE = CACHE_DIR / 'i18n'
EE_CACHE = CACHE_DIR / 'ee'
LOCALE_CONFIG_TEMP = TEMP_DIR / 'locale_config'
EE_UNPACK_TEMP = TEMP_DIR / 'ee'
FONTS_CACHE = CACHE_DIR / 'fonts'
FONTS_UNPACK_TEMP = TEMP_DIR / 'fonts'

# (来自 installer_gui.py)
def mkdir(t_dir: Any):
    os.makedirs(t_dir, exist_ok=True)


def clear_temp_dir():
    """在每次安装开始时清除临时文件夹"""
    if TEMP_DIR.is_dir():
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            print(f"Warning: Could not clear temp dir: {e}")
    mkdir(TEMP_DIR)


# (来自 installer_gui.py)
def process_possible_gbk_zip(zip_file: zipfile.ZipFile):
    name_to_info = zip_file.NameToInfo
    for name, info in name_to_info.copy().items():
        try:
            real_name = name.encode('cp437').decode('gbk')
            if real_name != name:
                info.filename = real_name
                del name_to_info[name]
                name_to_info[real_name] = info
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    return zip_file


def get_sha256(filepath: Path) -> Optional[str]:
    """计算文件的 SHA256 哈希值"""
    if not filepath.is_file():
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating SHA256 for {filepath}: {e}")
        return None


# (来自 installer_gui.py)
def fix_paths_xml(build_dir: Path):
    if not build_dir.is_dir():
        return
    xml_path = build_dir / 'paths.xml'
    if not xml_path.is_file():
        print(f"Warning: paths.xml not found in {build_dir}")
        return

    try:
        tree = Et.parse(xml_path)
        root = tree.getroot()
        paths_element = root.find('Paths')

        if paths_element is None:
            return

        current_paths = [path.text for path in paths_element.findall('Path')]

        # (来自 installer_gui.py)
        # (已移除 run_dir_num 检查，如您上传的文件所示)
        new_paths_to_add = [
            ('../res_mods', {}),
            ('../mods', {'type': 'mods'})
        ]

        elements_to_insert = []
        needs_save = False

        for text, attrib in new_paths_to_add:
            if text not in current_paths:
                new_path_element = Et.Element('Path', attrib=attrib)
                new_path_element.text = text
                elements_to_insert.append(new_path_element)
                needs_save = True

        if needs_save:
            for element in reversed(elements_to_insert):
                paths_element.insert(0, element)
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            print(f"Updated '{xml_path}'.")

    except Exception as e:
        print(f"Error modifying XML {xml_path}: {e}")


# (新增)
def get_locale_config_content(lang_code: str) -> Optional[str]:
    """获取特定语言的 locale_config.xml 内容"""
    # (已修改：使用重命名后的变量)
    lang2lconf = {
        'zh_CN': BUILTIN_LOCALE_CONFIG_ZH_CN,
        'zh_TW': BUILTIN_LOCALE_CONFIG_ZH_CN
    }
    return lang2lconf.get(lang_code, None)


# (新增)
def write_locale_config_to_temp(lang_code: str) -> Optional[Path]:
    """将 locale_config 写入临时文件并返回路径"""
    content = get_locale_config_content(lang_code)
    if content is None:
        return None

    config_path = LOCALE_CONFIG_TEMP / lang_code / 'locale_config.xml'
    mkdir(config_path.parent)

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return config_path


# (新增)
def create_mkmod(output_path: Path, files_to_add: Dict[str, Path]):
    """
    创建一个不压缩的 .mkmod (zip) 文件。
    files_to_add: {'zip内的路径': '本地文件路径'}
    """
    mkdir(output_path.parent)
    try:
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_STORED) as zf:
            for arcname, local_path in files_to_add.items():
                if local_path and local_path.is_file():
                    zf.write(local_path, arcname=arcname)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Failed to create {output_path}: {e}")

# --- (Mod 处理逻辑已根据您的文件移除) ---