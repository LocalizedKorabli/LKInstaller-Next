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
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import semver

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core import constants

PFX_SHA1 = "43ff9aecc348a54ed61178eda015832ec5b050fc"
TIMESTAMP_URL = "http://timestamp.digicert.com"
MSIX_FILENAME = "LK Next_ L10n Installer for Mir Korabley-x64.msix"


def find_sdk_tool(tool_name: str, fallback: str = "") -> str:
    """Locate the newest x64 Windows SDK tool under Windows Kits 10."""
    kits_bin = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")
    if kits_bin.is_dir():
        candidates = sorted(kits_bin.glob(f"*/x64/{tool_name}"), reverse=True)
        if candidates:
            return str(candidates[0])
    if fallback and Path(fallback).exists():
        return fallback
    raise FileNotFoundError(f"Cannot locate Windows SDK tool: {tool_name}")


def get_msix_version() -> tuple:
    """Return (major, minor, patch, 'M.m.p.0') aligned with APP_VERSION."""
    sem_ver = semver.parse(constants.APP_VERSION)
    major = sem_ver.get("major", 0)
    minor = sem_ver.get("minor", 0)
    patch = sem_ver.get("patch", 0)
    return major, minor, patch, f"{major}.{minor}.{patch}.0"


def run_nuitka(major: int, minor: int, patch: int) -> None:
    """Build standalone dist/lki.dist/lki.exe via Nuitka."""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={Path('src', 'resources', 'logo', 'logo.ico')}",
        "--include-data-dir=src/resources=resources",
        "--enable-plugin=tk-inter",
        "--include-package=win32api",
        "--include-package=win32com.client",
        "--include-package=keyring",
        "--noinclude-unittest-mode=nofollow",
        "--noinclude-setuptools-mode=nofollow",
        "--windows-company-name=LocalizedKorabli",
        "--windows-product-name=LK Installer Next",
        "--windows-file-description=LK Installer Next",
        f"--windows-file-version={major}.{minor}.{patch}.0",
        f"--windows-product-version={major}.{minor}.{patch}.0",
        "--output-filename=lki.exe",
        "--output-dir=dist",
        str(Path("src", "lki.py")),
    ]
    print("Running Nuitka:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def sign_msix(msix_path: Path) -> None:
    """Sign the MSIX package using PFX env vars if set, otherwise cert store."""
    signtool = find_sdk_tool(
        "signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe",
    )
    cmd = [signtool, "sign", "/fd", "SHA256"]
    pfx_path = os.environ.get("PFX_PATH", "")
    pfx_password = os.environ.get("PFX_PASSWORD", "")
    if pfx_path:
        cmd.extend(["/f", pfx_path])
        if pfx_password:
            cmd.extend(["/p", pfx_password])
    else:
        cmd.extend(["/sha1", PFX_SHA1])
    cmd.extend(["/tr", TIMESTAMP_URL, "/td", "SHA256", str(msix_path)])

    print(f"Signing MSIX: {msix_path}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SIGN FAILED:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)
    print(f"Signed OK: {msix_path}")


def build_msix(build_nuitka: bool = False, sign: bool = True) -> Path:
    """Stage files, compile resources.pri, and pack the MSIX package."""
    major, minor, patch, msix_version = get_msix_version()
    print(f"MSIX version: {msix_version} (from APP_VERSION={constants.APP_VERSION})")

    dist_dir = Path("dist") / "lki.dist"
    if build_nuitka or not (dist_dir / "lki.exe").exists():
        if Path("dist").is_dir():
            shutil.rmtree("dist")
        run_nuitka(major, minor, patch)

    msix_root = Path("packaging") / "msix"
    staging = msix_root / "staging"
    output_dir = msix_root / "Output"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(dist_dir, staging / "LKInstallerNext")
    shutil.copytree(msix_root / "Assets", staging / "Assets")
    shutil.copytree(msix_root / "Strings", staging / "Strings")

    manifest_text = (msix_root / "AppxManifest.xml").read_text(encoding="utf-8")
    updated_manifest, count = re.subn(
        r'(<Identity\b[^>]*\bVersion=")\d+\.\d+\.\d+\.\d+(")',
        rf"\g<1>{msix_version}\g<2>",
        manifest_text,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Failed to update Identity Version in AppxManifest.xml")
    manifest_path = staging / "AppxManifest.xml"
    manifest_path.write_text(updated_manifest, encoding="utf-8")

    makepri = find_sdk_tool("makepri.exe")
    makeappx = find_sdk_tool("makeappx.exe")

    priconfig_path = staging / "priconfig.xml"
    subprocess.run(
        [makepri, "createconfig", "/cf", str(priconfig_path), "/dq", "en-US", "/o"],
        check=True,
    )
    subprocess.run(
        [
            makepri, "new",
            "/pr", str(staging),
            "/cf", str(priconfig_path),
            "/mn", str(manifest_path),
            "/of", str(staging / "resources.pri"),
            "/o",
        ],
        check=True,
    )

    priconfig_path.unlink(missing_ok=True)
    shutil.rmtree(staging / "Strings")

    msix_path = output_dir / MSIX_FILENAME
    subprocess.run(
        [makeappx, "pack", "/d", str(staging), "/p", str(msix_path), "/o"],
        check=True,
    )

    if sign:
        sign_msix(msix_path)

    print(f"MSIX created: {msix_path}")
    return msix_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MSIX package for LKInstaller Next")
    parser.add_argument("--build", action="store_true", help="Force Nuitka rebuild before packing")
    parser.add_argument("--no-sign", action="store_true", help="Skip signtool signing")
    args = parser.parse_args()
    build_msix(build_nuitka=args.build, sign=not args.no_sign)


if __name__ == "__main__":
    main()
