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
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import semver

import constants

def run_build():
    pyinstaller_exe = os.path.join('.venv', 'Scripts', 'pyinstaller.exe')

    if not os.path.exists(pyinstaller_exe):
        print(f"Error: Cannot locate PyInstaller in '{pyinstaller_exe}'")
        sys.exit(1)

    pyinstaller_args = [
        '-w',  # 窗口化 (无控制台)
        '--clean',  # 构建前清理
        '--uac-admin',  # 请求管理员权限
        '--add-data',
        f"resources{os.pathsep}resources",
        '-i', os.path.join('resources', 'logo', 'logo.ico'),
        # --version-file
        '--version-file', os.path.join('assets', 'version_file.txt')
    ]

    command = [pyinstaller_exe] + pyinstaller_args + ['lki.py']

    print("--- Run Commands in venv ---")
    print(" ".join(f'"{arg}"' if " " in arg else arg for arg in command))
    print("-" * 30, flush=True)

    try:
        subprocess.run(command, check=True, text=True, encoding='utf-8')
        print("-" * 30)
        print("BUILD SUCCESS")

    except subprocess.CalledProcessError as e:
        print("-" * 30)
        print(f"BUILD FAILED: {e.returncode}")
    except FileNotFoundError:
        print(f"Cannot locate PyInstaller in {pyinstaller_exe}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

app_version = constants.APP_VERSION

sem_ver = semver.parse(app_version)

major = sem_ver.get('major', 0)
minor = sem_ver.get('minor', 0)
patch = sem_ver.get('patch', 0)

# Generate version_file.txt
version_file = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=({major}, {minor}, {patch}, 0),  # Version
prodvers=({major}, {minor}, {patch}, 0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x3f,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1, # Type
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'LocalizedKorabli'),
    StringStruct(u'FileDescription', u'LK Installer Next'),
    StringStruct(u'FileVersion', u'{major}.{minor}.{patch}'),
    StringStruct(u'InternalName', u'LKInstallerNext'),
    StringStruct(u'LegalCopyright', u'© 2025 LocalizedKorabli'),
    StringStruct(u'OriginalFilename', u'lki.exe'),
    StringStruct(u'ProductName', u'LK Installer Next'),
    StringStruct(u'ProductVersion', u'{major}.{minor}.{patch}')])
  ]),
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

assets_dir = Path('assets')
os.makedirs(assets_dir, exist_ok=True)

with open(assets_dir.joinpath('version_file.txt'), 'w', encoding='utf-8') as f:
    f.write(version_file)

# Modify Inno Setup file
iss_path = Path('inno').joinpath('pack.iss')

pattern = re.compile(r'(^\s*#define\s+MyAppVersion\s+)"(.*?)"', re.M)

try:
    # 1. 读取整个文件内容
    with open(iss_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 2. 检查是否找到匹配项
    if not pattern.search(content):
        print(f"Warning: '#define MyAppVersion' not found in the file")
    else:
        new_content = pattern.sub(f'\\g<1>"{app_version}"', content)
        # 4. 写回文件
        with open(iss_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"MyAppVersion in {iss_path} successfully updated to {app_version}")

except FileNotFoundError:
    print(f"Error: {iss_path} not found!")
except Exception as e:
    print(f"Error occurred while modifying the file: {e}")

# Clean build & dist, then run PyInstaller

if os.path.isdir('build'):
    shutil.rmtree('build')
if os.path.isdir('dist'):
    shutil.rmtree('dist')
run_build()

# Run Inno Setup to compile
output_path = Path('inno').joinpath('Output')

iscc_path = r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
target_iss_file = os.path.join('inno', 'pack.iss')
result = subprocess.run([iscc_path, target_iss_file], capture_output=True, text=True)

print("Compile logs:")
print(result.stdout)
if result.stderr:
    print("Compile errors:")
    print(result.stderr)

shutil.copy(output_path.joinpath('lki_setup.exe'), output_path.joinpath(f'澪刻·本地化安装器Next-{app_version}.exe'))

# Generate version_info.json

os.makedirs(output_path, exist_ok=True)

with open(output_path.joinpath('version_info.json'), 'w', encoding='utf-8') as f:
    json.dump(
        {
            "version": app_version
        },
        f,
        indent=2,
        ensure_ascii=False
    )