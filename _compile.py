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
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import semver

from core import constants

PFX_PATH = os.environ.get("PFX_PATH", r"")
PFX_PASSWORD = os.environ.get("PFX_PASSWORD", "")
PFX_SHA1 = "43ff9aecc348a54ed61178eda015832ec5b050fc"
TIMESTAMP_URL = "http://timestamp.digicert.com"
# signtool.exe from Windows SDK; adjust the version folder if needed
SIGNTOOL_PATH = r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe"

def sign_file(file_path):
    cmd = [
        SIGNTOOL_PATH, "sign",
        "/fd", "SHA256",
        "/f", PFX_PATH,
        "/p", PFX_PASSWORD,
        "/sha1", PFX_SHA1,
        "/tr", TIMESTAMP_URL,
        "/td", "SHA256",
        str(file_path),
    ]
    print(f"Signing: {file_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SIGN FAILED:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)
    print(f"Signed OK: {file_path}")

def run_build(major, minor, patch):
    python_exe = os.path.join('.venv', 'Scripts', 'python.exe')

    if not os.path.exists(python_exe):
        print(f"Error: Cannot locate Python venv in '{python_exe}'")
        sys.exit(1)

    nuitka_args = [
        '-m', 'nuitka',
        '--standalone',
        '--assume-yes-for-downloads',
        '--windows-console-mode=disable',
        f'--windows-icon-from-ico={os.path.join("resources", "logo", "logo.ico")}',
        '--include-data-dir=resources=resources',
        '--enable-plugin=tk-inter',
        '--include-package=win32api',
        '--include-package=win32com.client',
        '--include-package=keyring',
        '--noinclude-unittest-mode=nofollow',
        '--noinclude-setuptools-mode=nofollow',
        '--windows-company-name=LocalizedKorabli',
        '--windows-product-name=LK Installer Next',
        '--windows-file-description=LK Installer Next',
        f'--windows-file-version={major}.{minor}.{patch}.0',
        f'--windows-product-version={major}.{minor}.{patch}.0',
        '--output-filename=lki.exe',
        '--output-dir=dist',
    ]

    command = [python_exe] + nuitka_args + ['lki.py']

    print("--- Run Commands in venv ---")
    print(" ".join(f'"{arg}"' if " " in arg else arg for arg in command))
    print("-" * 30, flush=True)

    try:
        subprocess.run(command, check=True, text=True, encoding='utf-8', shell=True)
        print("-" * 30)
        print("BUILD SUCCESS")

    except subprocess.CalledProcessError as e:
        print("-" * 30)
        print(f"BUILD FAILED: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Cannot locate Python venv in {python_exe}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

app_version = constants.APP_VERSION

sem_ver = semver.parse(app_version)

major = sem_ver.get('major', 0)
minor = sem_ver.get('minor', 0)
patch = sem_ver.get('patch', 0)

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

# Clean dist, then run Nuitka
# Note: lki.build/ is Nuitka's incremental compilation cache, intentionally kept.

if os.path.isdir('dist'):
    shutil.rmtree('dist')
run_build(major, minor, patch)

# Sign lki.exe before Inno Setup packages it
sign_file(Path('dist') / 'lki.dist' / 'lki.exe')

# Run Inno Setup to compile; /Smysign passes the sign tool used by SignTool=mysign in pack.iss
output_path = Path('inno').joinpath('Output')

iscc_path = r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
target_iss_file = os.path.join('inno', 'pack.iss')
sign_cmd = (
    f'{SIGNTOOL_PATH} sign /fd SHA256 /f $q{PFX_PATH}$q /p $q{PFX_PASSWORD}$q'
    f' /sha1 {PFX_SHA1} /tr {TIMESTAMP_URL} /td SHA256 $f'
)
result = subprocess.run(
    [iscc_path, target_iss_file, f'/Smysign={sign_cmd}'],
    capture_output=True, text=True,
)

print("Compile prints:")
print(result.stdout)
if result.stderr:
    print("Compile errors:")
    print(result.stderr)

sign_file(output_path / 'lki_setup.exe')
shutil.copy(output_path.joinpath('lki_setup.exe'), output_path.joinpath(f'LK Next v{app_version}.exe'))

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
