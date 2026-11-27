# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2026-11-27

### Added
- Centered empty-state guide and clickable auto-import button in the game instance list when no instances are configured ([#5](https://github.com/LocalizedKorabli/LKInstaller-Next/pull/5)).
- ETag-based conditional caching mechanism and unit tests for ExperienceEnhancement (`ee.zip`) downloads.
- Pure Windows SDK MSIX packaging pipeline (`_compile_msix.py`, `msix/`) and GitHub Actions workflow (`.github/workflows/build.yml`) with Nuitka `clcache` caching and Inno Setup EXE builds.

### Changed
- Renamed the localization helper from `_` to `tr` across all modules to prevent shadowing collisions with Python throwaway variables ([#7](https://github.com/LocalizedKorabli/LKInstaller-Next/pull/7)).
- Updated `_compile.py` to sign via the Windows Certificate Store (`/sha1`), auto-detect per-user Inno Setup installations, and support `--skip-nuitka` / `--no-sign` flags.
- Bundled Simplified and Traditional Chinese `.isl` files in `inno/Languages/`.

### Fixed
- Stream-repack `ee.zip` directly into `ee.mkmod` (`ZIP_STORED`) without extracting to disk, eliminating Windows 260-character `MAX_PATH` failures ([#4](https://github.com/LocalizedKorabli/LKInstaller-Next/pull/4), closes [#1](https://github.com/LocalizedKorabli/LKInstaller-Next/issues/1)).
- Select language-appropriate vector UI fonts (`Microsoft YaHei UI`, `Microsoft JhengHei UI`, `Yu Gothic UI`, `Segoe UI`) instead of overriding Windows 11 to `Segoe UI`, preventing bitmap SimSun fallback for CJK text ([#6](https://github.com/LocalizedKorabli/LKInstaller-Next/pull/6)).
- Resolve MSIX VFS/AppData redirections to the real physical path before displaying or opening `APP_DATA_PATH` in Explorer ([#6](https://github.com/LocalizedKorabli/LKInstaller-Next/pull/6)).

## [1.2.0]

### Added
- German (`de`) and Spanish (`es`) UI translations and localization support.

### Fixed
- Prevented localization installation task stalls and avoided redundant version route scans.

[Unreleased]: https://github.com/LocalizedKorabli/LKInstaller-Next/compare/1.2.1...dev
[1.2.1]: https://github.com/LocalizedKorabli/LKInstaller-Next/compare/f0cf638...1.2.1
[1.2.0]: https://github.com/LocalizedKorabli/LKInstaller-Next/compare/1.1.1...f0cf638
