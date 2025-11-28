<div align=center>
  
  <img width="200" alt="logo" src="https://github.com/user-attachments/assets/7bf8c1be-2abe-47d0-b8d9-78394a2a3312" />
  
  <h2>LK I18n Installer Next</h2>
  
  [![stars](https://img.shields.io/github/stars/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/stargazers)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-purple.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
  [![release](https://img.shields.io/github/release/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/releases/latest)
  
  [![Source Code](https://img.shields.io/badge/Source-Code-orange?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)
  [![Discord](https://img.shields.io/discord/1275430075369656381?style=for-the-badge)](https://discord.gg/3d9k2mkWy4)
  [![QQ Group](https://img.shields.io/badge/QQ-Group-red?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)

  
</div>

*The documentation was AI-translated. Errors or ambiguities may occur.*

## Introduction

**LK I18n Installer Next** (hereinafter referred to as **LK Next**) is a complete rewrite of the [LK I18n Installer](https://github.com/LocalizedKorabli/I18nInstallerGUI).

<details><summary style="font-size: 12px;">New Features in LK Next</summary>
<h4>New features introduced in LK Next compared to the previous installer:</h4>

- Supports installing **Localization Packages** in multiple languages: Simp. Chinese, Trad. Chinese, English, and Japanese;
- Supports installing localization packages for the Mir Korabley client on Steam;
- Supports uninstalling localization packages;
- Supports installing the **Font Optimization Pack** (Font Opt.). This option is enabled by default when the localization language is set to Simp. Chinese, Trad. Chinese, or Japanese;
- Supports one-click updates for the application itself;
- Introduces "**Instances**" and "**Presets**", allowing different installation/uninstallation operations to be performed simultaneously for multiple game client instances;
- Supports using multiple **Download Routes** simultaneously with priority sorting;
  - Supported routes:
    - Tencent (Font Opt. and App Updates only)
    - Cloudflare (Font Opt. and App Updates only)
    - Gitee (Localization and EE Pack only)
    - Gitlab (Localization and EE Pack only)
    - GitHub (Localization and EE Pack only)
- Supports more detailed proxy settings;
- Supports switching the application interface language and Light/Dark themes.

<h4>Functional changes in LK Next compared to the previous installer:</h4>

- The version recognition mechanism has been optimized. It now only installs localization packages for active versions defined by the remote repository;
- All content is now installed in the `.mkmod` format introduced by Mir Korabley;
- **Localization Modification Packs** (L10n Mods) are now always installed using the "MO mounting" mechanism introduced by Mir Korabley.

<h4>Features removed in LK Next compared to the previous installer:</h4>

- The function to install localization packages for Global/CN servers has been removed as it was rarely used and prone to misleading users.

</details>

## Download and Install LK Next

### Download Routes
- [Lanzou Cloud](https://tapio.lanzouu.com/b0nzmcv9i)
- [Official Route - Mainland China](https://lk-1251573974.cos.accelerate.myqcloud.com/lki/lk-next/lki_setup.exe)
- [Official Route - Overseas](https://dl.localizedkorabli.org/lki/lk-next/lki_setup.exe)

<details><summary style="font-size: 12px;"><b>How to handle browser download blocks</b></summary>

- Microsoft Edge (lki_setup.exe isn't commonly downloaded. Make sure you trust lki_setup.exe before you open it):
  - Hover over the download item, click the "three dots" (...) icon on the right, and click **Keep**;
  - In the "Make sure you trust lki_setup.exe before you open it" popup, open the dropdown menu next to the blue **Delete** button and click **Keep anyway**.

- Chrome (Suspicious download blocked):
  - Click the message, then click the option to **Download suspicious file**.

</details>

### Install Application
- Open the downloaded installer, select the installation language (this will also be set as the default display language for LK Next and the default language for localization packages), and follow the instructions to complete the installation.

## Using LK Next

### TL;DR

If you only need to install the localization package without any extra configuration, simply click the **Install** button at the bottom left of the main interface (**Game** tab).

### Instances

#### What is an Instance?

Your installed Mir Korabley client can be imported into the application as an "Instance" to install localization packages.

#### Importing Instances

On the first launch, the application will attempt to scan for all Mir Korabley clients on your device and import them as instances.

If the instance you want does not appear in the list, please ensure the game is fully installed, then click the **Auto-import instances on this PC** button on the far right of the "Game Instances" label row.

If it is still not imported, click the **Import Instance** button on the same row to try manually importing the game instance.

#### Managing Instances

You can view all currently imported game instances on the **Game** tab.

You can also use the other buttons on the **Game** tab to import, quickly edit, remove, sort, open the directory of, or run the game for the instances.

#### Selecting an Instance (For viewing details)

Click the name of a game instance to select it. Once selected, the instance item will be highlighted in blue. You can switch to the **Advanced** tab to view detailed information about the instance and the currently selected preset.

#### Checking an Instance (For installing/uninstalling)

Click the checkbox to the left of the game instance list item on the **Game** tab to check/uncheck the instance. Clicking the checkbox in the "Game Instances" label row will check/uncheck all instances at once.

All newly imported instances are checked by default.

### Presets

#### What is a Preset?

An instance can have multiple "Presets", which determine the **specific operations performed by the application when installing localization packages for that instance**:

- Which **Language/Client Type** (Live/PT) of the localization package to download and install.
- Whether to download and install the [**Experience Enhancement Pack (EE Pack)**](#experience-enhancement-pack-ee-pack).
- Whether to download and install the [**Font Optimization Pack (Font Opt.)**](#font-optimization-pack-font-opt).
- Whether to load [**Localization Modification Packs (L10n Mods)**](#localization-modification-pack-l10n-mods).

#### Default Preset

Every instance has a **Default Preset**, where the installation language is defaulted to **the language the application is displaying when the user imports the instance**.

#### Managing Presets

To manage presets, first select a game instance, then switch to the **Advanced** tab.

In the dropdown menu named **Install Preset** under the Preset Configuration frame, you can quickly switch presets for the instance.

Clicking the gear button to the right of the dropdown menu opens the **Manage Presets** interface.

In the Manage Presets interface, you can:
- Add, delete, or modify presets for the instance;
- Change various settings of a preset;
- Generate an **Auto-Update Shortcut** for the current preset.

### Customization

#### Experience Enhancement Pack (EE Pack)

The Experience Enhancement Pack (EE Pack) is a set of mods for Mir Korabley, containing:
- [Input Method Support Mod](https://bbs.nga.cn/read.php?tid=29102783);
- UI optimization mod based on the Unbound framework;
- Translation patch mods for other Mir Korabley mods based on the current localization language;
- A startup logo patch featuring our team's branding.

The EE Pack will be installed by default. You can choose whether to install it in the **Manage Presets** interface.

#### Font Optimization Pack (Font Opt.)

The Font Optimization Pack contains font optimization mods for Mir Korabley, including SrcWagon—a new font based on Mir Korabley's native "ALS Wagon" and "Source Han Sans CN"—which fixes the appearance and positioning of some glyphs.

When your preset's localization language is set to **Simp. Chinese**, **Trad. Chinese**, or **Japanese**, the Font Optimization Pack will be installed by default. You can choose whether to install it in the **Manage Presets** interface.

#### Localization Modification Pack (L10n Mods)

Localization Modification Packs (L10n Mods) are used to modify specific text in the localization package. For information on creating L10n Mods, please refer to the [post on the Mir Korabley forum](https://forum.korabli.su/topic/162025-).

You can drag and drop your created L10n Mods directly, or pack them into a zip file and place them into the L10n Mods folder for the current preset (opened by clicking the folder icon button in the **Manage Presets** interface).

L10n Mods will be loaded the **next time** you install the localization package.

L10n Mods will be installed by default. You can choose whether to install them in the **Manage Presets** interface.

### App Settings

In the **Settings** tab, you can:
- Adjust **Appearance**, **Download**, and **Files** settings;
- Clear download cache and output logs;
- View the application's working directory and data directory.

### App Info / Update App

In the **About** tab, you can:
- View the application version and **Check for Update**;
- Visit the source code repository or join the team's groups on social platforms by clicking the GitHub, QQ, or Discord icons;
- View the full text of the application license by clicking the purple "AGPL V3" icon above the copyright notice.

## Q&A

### What if the app reports an error or the localization package fails to install?

Please try to [**Check for Update**](#app-info--update-app) first, then reinstall the localization package.

Go to the **Settings** tab and click the **Open Dir** button in the **App Data Path** row. In the opened folder, enter the `logs` folder and save the latest `.log` file.

You can open the file to try and analyze the cause of the error yourself, or submit the file to [GitHub Issues](https://github.com/LocalizedKorabli/LKInstaller-Next/issues) | [QQ Group](https://qm.qq.com/q/SUoZAcV442) | [Discord Server](https://discord.gg/3d9k2mkWy4) for help.

### Where did the auto-update function go?

Please see [Managing Presets](#managing-presets). You can generate an **Auto-Update Shortcut** for the current preset in the **Manage Presets** interface.

### What if I have questions about the localization package itself?

Please find the relevant repository in the [Team Portal](https://github.com/LocalizedKorabli#%E9%A1%B9%E7%9B%AE%E4%BC%A0%E9%80%81%E9%97%A8portal) according to the language and client type you are using, and submit feedback in its Issues.

You can also join the QQ group or Discord server to participate in the discussion.

## Credits

- All users who participated in the internal testing of this project

- [Python](https://www.python.org/) — The programming language used by this application

- [Tkinter](https://docs.python.org/3/library/tkinter.html) — The GUI framework used by this application

- [Google Gemini](https://gemini.google.com/) — Shortened the development time of this application by approximately 70%

- [Azure theme for ttk](https://github.com/rdbende/Azure-ttk-theme) — The ttk theme used by this application interface

- [Inno Setup](https://jrsoftware.org/isinfo.php) and [PyInstaller](https://pyinstaller.org/) — Provided convenient packaging solutions for this application