import os
import shutil
import hashlib
import zipfile
import json
import polib
import uuid  # <-- (新增)
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
MODS_TEMP = TEMP_DIR / 'mods'  # <-- (新增: mods 临时目录)


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


# (新增: Mods 助手函数 - 提取 zip 中的 mod 文件)
def _extract_zip_mods(zip_path: Path, temp_target_dir: Path):
    """从 ZIP 文件中提取 .mo/.l10mod/.i18nmod 文件到临时目录。"""

    # 允许的文件后缀
    ALLOWED_EXTENSIONS = ('.mo', '.l10mod', '.i18nmod')

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 尝试处理可能的 GBK 编码
            zf = process_possible_gbk_zip(zf)

            for member in zf.namelist():
                # 只处理允许的后缀
                if member.lower().endswith(ALLOWED_EXTENSIONS):
                    safe_member = Path(member)
                    if safe_member.is_absolute() or ".." in member:
                        continue  # 跳过不安全路径

                    # 为每个文件创建一个临时子目录来解压
                    temp_sub_dir = TEMP_DIR / str(uuid.uuid4())
                    mkdir(temp_sub_dir)

                    # 解压到临时子目录
                    zf.extract(member, path=str(temp_sub_dir))

                    # 查找提取的文件
                    extracted_file_path = temp_sub_dir / safe_member

                    # 查找 extracted_file_path 的实际位置 (以防 zip 内部路径包含目录)
                    if not extracted_file_path.is_file():
                        # 尝试在解压的根目录或其子目录中查找
                        found_files = list(Path(temp_sub_dir).glob('**/*'))
                        file_found = next((f for f in found_files if f.name == safe_member.name and f.is_file()), None)

                        if not file_found:
                            shutil.rmtree(temp_sub_dir)
                            continue  # 文件未找到，跳过
                        extracted_file_path = file_found

                    # 创建唯一文件名
                    unique_filename = f"{uuid.uuid4()}{extracted_file_path.suffix}"
                    final_path = temp_target_dir / unique_filename

                    # 移动到最终临时目录
                    shutil.move(extracted_file_path, final_path)

                    # 清理临时解压目录
                    shutil.rmtree(temp_sub_dir)

    except Exception as e:
        print(f"Warning: Failed to process zip file {zip_path}: {e}")


# (新增: Mods 处理函数 - 核心逻辑)
def process_mods_for_installation(instance_id: str, instance_path: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    扫描实例的本地 mods 文件夹，处理文件和 zip，并将它们打包成两个 mkmod。
    返回: (mo_mkmod_path, json_mkmod_path)
    """
    MODS_SOURCE_DIR = instance_path / 'lki' / 'i18n_mods'
    TEMP_PROCESS_DIR = MODS_TEMP / instance_id  # 临时存储所有解压/复制的文件

    # 目标 mkmod 文件路径
    MO_MKMOD_PATH = MODS_TEMP / f"{instance_id}_mo_mod.mkmod"
    JSON_MKMOD_PATH = MODS_TEMP / f"{instance_id}_json_mod.mkmod"

    # 清理和创建临时目录
    if TEMP_PROCESS_DIR.is_dir():
        shutil.rmtree(TEMP_PROCESS_DIR)
    mkdir(TEMP_PROCESS_DIR)

    # 确保清理旧的 mkmod 文件
    if MO_MKMOD_PATH.is_file():
        os.remove(MO_MKMOD_PATH)
    if JSON_MKMOD_PATH.is_file():
        os.remove(JSON_MKMOD_PATH)

    # 1. 遍历源文件夹
    if not MODS_SOURCE_DIR.is_dir():
        print(f"Mods source directory not found: {MODS_SOURCE_DIR}")
        # 如果目录不存在，返回 None, None (非致命错误)
        return None, None

    for item in os.listdir(MODS_SOURCE_DIR):
        item_path = MODS_SOURCE_DIR / item
        if item_path.is_file():
            # a. 处理 zip 文件
            if item.lower().endswith('.zip'):
                _extract_zip_mods(item_path, TEMP_PROCESS_DIR)

            # b. 处理 mods 文件 (.mo, .l10mod, .i18nmod)
            elif item.lower().endswith(('.mo', '.l10mod', '.i18nmod')):
                # 移动文件到临时目录，并重命名为唯一名称以避免冲突
                unique_filename = f"{uuid.uuid4()}{item_path.suffix}"
                final_path = TEMP_PROCESS_DIR / unique_filename
                shutil.copy(item_path, final_path)  # 使用 copy 以防用户需要保留源文件

    # 2. 将收集到的文件打包
    mo_files_to_add: Dict[str, Path] = {}
    json_files_to_add: Dict[str, Path] = {}

    for file in os.listdir(TEMP_PROCESS_DIR):
        file_path = TEMP_PROCESS_DIR / file
        if file.lower().endswith('.mo'):
            # zip 内部的路径: texts/ru/LC_MESSAGES/文件名.mo
            arcname = f"texts/ru/LC_MESSAGES/{file}"
            mo_files_to_add[arcname] = file_path

        elif file.lower().endswith(('.l10mod', '.i18nmod')):
            # zip 内部的路径: json_mods/文件名.l10mod
            arcname = f"json_mods/{file}"
            json_files_to_add[arcname] = file_path

    mo_mkmod_path = None
    if mo_files_to_add:
        create_mkmod(MO_MKMOD_PATH, mo_files_to_add)
        mo_mkmod_path = MO_MKMOD_PATH

    json_mkmod_path = None
    if json_files_to_add:
        create_mkmod(JSON_MKMOD_PATH, json_files_to_add)
        json_mkmod_path = JSON_MKMOD_PATH

    # 3. 清理临时处理目录
    if TEMP_PROCESS_DIR.is_dir():
        shutil.rmtree(TEMP_PROCESS_DIR)

    return mo_mkmod_path, json_mkmod_path

# --- (Mod 处理逻辑已根据您的文件移除) ---