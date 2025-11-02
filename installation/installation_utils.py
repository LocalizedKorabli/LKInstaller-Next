import os
import shutil
import hashlib
import zipfile
import json
import polib
import uuid
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
CACHE_DIR = Path('../lki/cache')
TEMP_DIR = Path('../lki/temp')
L10N_CACHE = CACHE_DIR / 'i18n'
EE_CACHE = CACHE_DIR / 'ee'
LOCALE_CONFIG_TEMP = TEMP_DIR / 'locale_config'
EE_UNPACK_TEMP = TEMP_DIR / 'ee'
FONTS_CACHE = CACHE_DIR / 'fonts'
FONTS_UNPACK_TEMP = TEMP_DIR / 'fonts'
MODS_TEMP = TEMP_DIR / 'mods'


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
# (其他辅助函数如 fix_paths_xml, get_locale_config_content, write_locale_config_to_temp 保持不变)
    except Exception as e:
        print(f"Error modifying XML {xml_path}: {e}")


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

def create_mkmod(output_path: Path, files_to_add: Dict[str, Path]):
    """
    创建一个不压缩的 .mkmod (zip) 文件.
    files_to_add: {'zip内的路径': '本地文件路径'}
    """
    mkdir(output_path.parent)
    try:
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_STORED) as zf:
            for arcname, local_path in files_to_add.items():
                if local_path and local_path.is_file():
                    # Check for placeholder file (using startswith for safe check)
                    if local_path.name.startswith("mod_placeholder_src"):
                        # Write "placeholder" content directly into the zip
                        zf.writestr(arcname, "placeholder")
                    else:
                        zf.write(local_path, arcname=arcname)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Failed to create {output_path}: {e}")


# (Mods 助手函数: _extract_zip_mods 保持不变)

def _extract_zip_mods(zip_path: Path, temp_target_dir: Path):
    """从 ZIP 文件中提取 .mo/.l10nmod/.i18nmod 文件到临时目录."""

    # 允许的文件后缀
    ALLOWED_EXTENSIONS = ('.mo', '.l10nmod', '.i18nmod')

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
                            continue  # 文件未找到, 跳过
                        extracted_file_path = file_found

                    # 创建唯一文件名，且防止带空格的文件不被mkmod加载系统读取
                    unique_filename = f"{safe_member.stem}@{uuid.uuid4()}{extracted_file_path.suffix}".replace(' ', '_')
                    final_path = temp_target_dir / unique_filename

                    # 移动到最终临时目录
                    shutil.move(extracted_file_path, final_path)

                    # 清理临时解压目录
                    shutil.rmtree(temp_sub_dir)

    except Exception as e:
        print(f"Warning: Failed to process zip file {zip_path}: {e}")


# --- JSON Mods 编译辅助函数 (基于您的输入) ---

def append_json_mod(json_mod: Dict[str, Any],
                    json_mods_d: Dict[str, Union[str, List[str]]],
                    json_mods_m: Dict[str, str]):
    """将单个 JSON Mod 的替换规则聚合到字典中."""
    if 'replace' in json_mod.keys():
        replaces = json_mod.get('replace')
        if isinstance(replaces, Dict):
            for r_k in replaces.keys():
                r_v = replaces[r_k]
                if isinstance(r_v, (str, List)):
                    json_mods_d[r_k] = r_v
    if 'words' in json_mod.keys():
        words = json_mod.get('words')
        if isinstance(words, Dict):
            for w_k in words.keys():
                w_v = words[w_k]
                if isinstance(w_v, str):
                    json_mods_m[w_k] = w_v


def process_json_mod_entries(source_mo: polib.MOFile,
                             json_mods_d_replace: Dict[str, Union[str, List[str]]],
                             json_mods_m_replace: Dict[str, str]) -> List[polib.MOEntry]:
    """
    根据聚合的替换规则, 应用到 source_mo 的副本上, 并返回被修改的条目列表.
    """
    modified_entries = []

    # 遍历 source_mo 中的每个条目
    for entry in source_mo:
        modified_in_pass = False

        if not entry.msgid:
            continue

        modified_entry = entry

        # --- Words Replacement (m_replace) ---
        original_msgstr = modified_entry.msgstr
        original_msgstr_plural = modified_entry.msgstr_plural.copy() if modified_entry.msgid_plural else None

        if modified_entry.msgid_plural:
            msgstrs: Dict[int, str] = modified_entry.msgstr_plural
            for m_k in json_mods_m_replace:
                m_v = json_mods_m_replace[m_k]
                for i in msgstrs.keys():
                    if m_k in msgstrs.get(i):
                        msgstrs[i] = msgstrs.get(i).replace(m_k, m_v)
                        modified_in_pass = True
            if modified_in_pass:
                modified_entry.msgstr_plural = msgstrs
        else:
            msgstr = modified_entry.msgstr
            for m_k in json_mods_m_replace:
                m_v = json_mods_m_replace[m_k]
                if m_k in msgstr:
                    modified_entry.msgstr = msgstr.replace(m_k, m_v)
                    modified_in_pass = True

        # --- Direct/List Replacement (d_replace, 'replace' block) ---
        for d_k in json_mods_d_replace:
            if modified_entry.msgid == d_k:
                target_text = json_mods_d_replace[d_k]

                if modified_entry.msgid_plural:
                    if isinstance(target_text, str):
                        list_l = len(modified_entry.msgstr_plural) if modified_entry.msgstr_plural else 1
                        modified_entry.msgstr_plural = {i: target_text for i in range(list_l)}
                    elif isinstance(target_text, List):
                        # Assuming target_text is correctly formatted List[str]
                        modified_entry.msgstr_plural = {i: target_text[i] for i in range(len(target_text))}
                else:
                    if isinstance(target_text, str):
                        modified_entry.msgstr = target_text

                modified_in_pass = True

        if modified_in_pass:
            modified_entries.append(modified_entry)

    return modified_entries


def process_mods_for_installation(instance_id: str, instance_path: Path, mo_file_path: Path, lang_code: str) -> Tuple[
    Optional[Path], Optional[Path]]:
    """
    1. 收集本地 Mods 文件 (.mo, .l10nmod, .i18nmod).
    2. 处理 JSON Mods (.l10nmod/.i18nmod) 并将其编译成 *多个* 临时的 .mo 文件.
    3. 打包成两个 mkmod: lk_i18n_mo_mod.mkmod (原生 .mo) 和 lk_i18n_json_mod.mkmod (编译 .mo).
    4. 总是生成 mkmod (包含占位符).
    返回: (mo_mkmod_path, json_mkmod_path)
    """
    MODS_SOURCE_DIR = instance_path / 'lki' / 'i18n_mods' / lang_code
    TEMP_PROCESS_DIR = MODS_TEMP / instance_id

    # 关键修改: 为当前实例创建唯一的占位符路径
    PLACEHOLDER_SOURCE_NAME = f"mod_placeholder_src_{uuid.uuid4()}.txt"
    PLACEHOLDER_SOURCE_PATH = TEMP_DIR / PLACEHOLDER_SOURCE_NAME

    # 目标 mkmod 文件路径
    MO_MKMOD_PATH = MODS_TEMP / f"{instance_id}_mo_mod.mkmod"
    JSON_MKMOD_PATH = MODS_TEMP / f"{instance_id}_json_mod.mkmod"

    # 1. 清理和创建临时目录
    if TEMP_PROCESS_DIR.is_dir():
        shutil.rmtree(TEMP_PROCESS_DIR)
    mkdir(TEMP_PROCESS_DIR)

    if MO_MKMOD_PATH.is_file(): os.remove(MO_MKMOD_PATH)
    if JSON_MKMOD_PATH.is_file(): os.remove(JSON_MKMOD_PATH)

    # 2. 强制创建占位符源文件
    try:
        with open(PLACEHOLDER_SOURCE_PATH, 'w', encoding='utf-8') as f:
            f.write("placeholder")
    except Exception as e:
        print(f"FATAL: Failed to create placeholder source file: {e}")
        return None, None

    # 3. 初始化收集字典
    native_mo_files: Dict[str, Path] = {}
    json_mods_to_process: List[Path] = []

    # 4. 遍历源文件夹 (如果存在) 并收集用户Mods
    if MODS_SOURCE_DIR.is_dir():
        for item in os.listdir(MODS_SOURCE_DIR):
            item_path = MODS_SOURCE_DIR / item
            if item_path.is_file():
                # a. 处理 zip 文件: 提取到 TEMP_PROCESS_DIR
                if item.lower().endswith('.zip'):
                    _extract_zip_mods(item_path, TEMP_PROCESS_DIR)

                # b. 处理 mods 文件: 复制到 TEMP_PROCESS_DIR
                elif item.lower().endswith(('.mo', '.l10nmod', '.i18nmod')):
                    unique_filename = f"{uuid.uuid4()}{item_path.suffix}"
                    final_path = TEMP_PROCESS_DIR / unique_filename
                    shutil.copy(item_path, final_path)

    # 5. 将收集到的文件分类 (位于 TEMP_PROCESS_DIR)
    for file in os.listdir(TEMP_PROCESS_DIR):
        file_path = TEMP_PROCESS_DIR / file
        if file.lower().endswith('.mo'):
            # Native MOs go to the first MKMOD
            native_mo_files[f"texts/ru/LC_MESSAGES/{file}"] = file_path
        elif file.lower().endswith(('.l10nmod', '.i18nmod')):
            json_mods_to_process.append(file_path)

    # --- 7. JSON Mod 编译 (生成多个 MO 文件) ---
    json_converted_mo_files: Dict[str, Path] = {}

    # A. 编译
    if json_mods_to_process:
        try:
            base_mo = polib.mofile(str(mo_file_path))
        except Exception as e:
            print(f"Error: Failed to load base MO file for JSON mod compilation: {e}")
            pass
        else:
            for json_path in json_mods_to_process:
                try:
                    # Load JSON rules
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_mod_data = json.load(f)

                    single_d_replace = {}
                    single_m_replace = {}
                    append_json_mod(json_mod_data, single_d_replace, single_m_replace)

                    # Apply rules and get only modified entries
                    modified_entries = process_json_mod_entries(base_mo, single_d_replace, single_m_replace)

                    if modified_entries:
                        # Create a new PO/MO for this single JSON mod
                        new_po = polib.POFile()
                        new_po.metadata = base_mo.metadata
                        for entry in modified_entries:
                            po_entry = polib.POEntry()
                            po_entry.msgid = entry.msgid
                            po_entry.msgid_plural = entry.msgid_plural
                            po_entry.msgstr = entry.msgstr
                            po_entry.msgstr_plural = entry.msgstr_plural
                            new_po.append(po_entry)

                        # Save the converted MO file to a unique temp path
                        mo_filename = json_path.stem + ".mo"
                        temp_mo_path = TEMP_DIR / f"compiled_json_{uuid.uuid4()}_{mo_filename}"
                        new_po.save_as_mofile(str(temp_mo_path))

                        # Store the converted MO file for JSON MKMOD packaging
                        json_converted_mo_files[f"texts/ru/LC_MESSAGES/{mo_filename}"] = temp_mo_path

                except Exception as e:
                    print(f"Warning: Failed to compile JSON mod {json_path}: {e}")

    # --- 8. 强制添加占位符到打包列表并打包 ---

    # A. 打包原生 MO 文件 (lk_i18n_mo_mod.mkmod)
    # 强制添加占位符
    #native_mo_files['texts/ru/LC_MESSAGES/.placeholder'] = PLACEHOLDER_SOURCE_PATH

    mo_mkmod_path = None
    try:
        create_mkmod(MO_MKMOD_PATH, native_mo_files)
        mo_mkmod_path = MO_MKMOD_PATH
    except Exception as e:
        print(f"FATAL: Failed to create native MO mkmod file: {e}")

    # B. 打包编译后的 JSON MO 文件 (lk_i18n_json_mod.mkmod)
    # 强制添加占位符
    #json_converted_mo_files['texts/ru/LC_MESSAGES/.placeholder'] = PLACEHOLDER_SOURCE_PATH

    json_mkmod_path = None
    try:
        create_mkmod(JSON_MKMOD_PATH, json_converted_mo_files)
        json_mkmod_path = JSON_MKMOD_PATH
    except Exception as e:
        print(f"FATAL: Failed to create JSON MO mkmod file: {e}")

    if TEMP_PROCESS_DIR.is_dir():
        shutil.rmtree(TEMP_PROCESS_DIR)
    # 9. 清理所有临时文件
    # 清理占位符源文件
    if PLACEHOLDER_SOURCE_PATH.is_file():
        os.remove(PLACEHOLDER_SOURCE_PATH)
    # 清理所有编译后的 MO 文件
    for mo_path in json_converted_mo_files.values():
        if mo_path.is_file():
            os.remove(mo_path)

    return mo_mkmod_path, json_mkmod_path