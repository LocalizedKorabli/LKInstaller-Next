<div align=center>
  
  <img width="200" alt="logo" src="https://github.com/user-attachments/assets/7bf8c1be-2abe-47d0-b8d9-78394a2a3312" />
  
  <h2>澪刻・本地化安装器Next</h2>
  
  [![stars](https://img.shields.io/github/stars/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/stargazers)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-purple.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
  [![release](https://img.shields.io/github/release/LocalizedKorabli/LKInstaller-Next.svg?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/releases/latest)
  
  [![源代码](https://img.shields.io/badge/项目-源代码-orange?style=for-the-badge)](https://github.com/LocalizedKorabli/LKInstaller-Next/tree/dev)
  [![Discord](https://img.shields.io/discord/1275430075369656381?style=for-the-badge)](https://discord.gg/3d9k2mkWy4)
  [![QQ群](https://img.shields.io/badge/QQ-发布群-red?style=for-the-badge)](https://qm.qq.com/q/oLZZH47TRA)
  
</div>

<details><summary style="font-size: 14px;">Languages🌐</summary>

[English](/docs/en/README.md)

</details>

## 简介

澪刻・本地化安装器Next（以下简称**澪刻Next**）是对[澪刻・汉化安装器](https://github.com/LocalizedKorabli/L10nInstallerGUI)的完全重写。

<details><summary style="font-size: 12px;">澪刻Next新特性</summary>
<h4>相较于澪刻・汉化安装器，澪刻Next引入的新功能：</h4>

- 支持安装多个语言的本地化包：简体中文、繁体中文、英文、日文；
- 支持为Steam上的Mir Korabley客户端安装本地化包；
- 支持卸载本地化包；
- 支持安装字体优化包，本地化包语言设定为简体中文/繁体中文/日文时此选项默认启用；
- 支持应用本体一键更新；
- 引入“实例”和”预设“，现在支持为多个游戏客户端实例同时执行不同的安装/卸载操作；
- 支持同时使用多条下载线路，并对后者进行优先级排序；
  - 支持的线路：
    - 腾讯云（仅字体优化包和应用更新包）
    - Cloudflare（仅字体优化包和应用更新包）
    - Gitee（仅本地化包和体验增强包）
    - Gitlab（仅本地化包和体验增强包）
    - GitHub（仅本地化包和体验增强包）
- 支持更细致地调节代理选项；
- 支持切换应用界面语言、浅色/深色主题。

<h4>相较于澪刻・汉化安装器，澪刻Next的功能改动：</h4>

- 版本识别机制已被优化，现在总是只为远程仓库定义的活跃版本安装本地化包；
- 所有内容现在均以Mir Korabley新引入的.mkmod格式安装；
- 本地化修改包（原汉化修改包）现在总是以Mir Korabley新引入的“MO挂载”机制安装。

<h4>相较于澪刻・汉化安装器，澪刻Next删除的功能：</h4>

- 由于极少被使用且易误导用户，向直营服/国服安装本地化包的功能已被删除。

</details>

## 下载并安装澪刻Next

### 下载线路
- [蓝奏云分享](https://tapio.lanzouu.com/b0nzmcv9i)
- [官方下载线路-中国大陆](https://lk-1251573974.cos.accelerate.myqcloud.com/lki/lk-next/lki_setup.exe)
- [官方下载线路-海外地区](https://dl.localizedkorabli.org/lki/lk-next/lki_setup.exe)

<details><summary style="font-size: 12px;"><b>浏览器阻止下载时的操作方法</b></summary>

- Microsoft Edge（通常不会下载 lki_setup.exe。请在打开前确保信任 lki_setup.exe）：
  - 鼠标移至文件对应的下载项上，点击在右侧出现的以“3个点”（...）为图标的按钮，再点击**保留**选项；
  - 弹出“打开前请确保信任 lki_setup.exe”子窗口后，从蓝色**删除**按钮最右侧打开下拉栏，点击**仍然保留**选项。

- Chrome（已阻止可疑下载操作）：
  - 点击文件对应的下载项，再点击**下载可疑文件**选项。

</details>

### 安装应用
- 打开您下载的安装包文件，选择安装时使用的语言（此语言也会被设为澪刻Next的默认显示语言及安装本地化包的默认语言），并根据指示完成安装。

## 使用澪刻Next

### 省流

如果您只需要安装本地化包而不需要进行任何额外设定，直接点击应用主界面（**游戏**页）左下角的**安装**按钮即可。

### 实例

#### 什么是实例？

您安装的Mir Korabley客户端可被作为“实例”导入应用，以便安装本地化包。

#### 导入实例

首次启动时，应用会尝试扫描设备上所有Mir Korabley客户端，并作为实例导入。

若列表中未出现您想要的实例，请先确保游戏已完整安装，然后点击“游戏实例”标签行最右侧的**自动导入电脑上的实例**按钮。

若仍未导入，请点击同一标签行的**导入实例**按钮，尝试手动导入游戏实例。

#### 管理实例

您可以在**游戏**页查看目前已导入的所有游戏实例。

您还可以通过**游戏**页的其他按钮对实例进行导入、快速编辑、移除、排序、打开所在文件夹、运行游戏等操作。

#### 选中实例（用于查看实例详细信息）

点击游戏实例的名称来选中它。选中后，该实例项将被蓝色高亮。您可以切换到**高级**页，查看实例以及当前选中预设的详细信息。

#### 勾选实例（用于安装/卸载本地化包）

点击**游戏**页左侧与游戏实例列表项平齐的复选框，以勾选/取消勾选实例。点击“游戏实例”标签行的复选框能一次性勾选/取消勾选所有实例。

所有新导入的实例默认被勾选。

### 预设

#### 什么是预设？

一个实例可以拥有多个“预设”，后者决定着应用**在为实例安装本地化包过程中执行的具体操作**：

- 下载并安装何种**语言/客户端类型**（正式服、PT服）的本地化包
- 是否下载并安装[**体验增强包**](#体验增强包)
- 是否下载并安装[**字体优化包**](#字体优化包)
- 是否加载[**本地化修改包**](#本地化修改包)

#### 默认预设

每一个实例都有一个**默认预设**，其中本地化的安装语言被默认设定为**用户导入实例时应用正在显示的语言**。

#### 管理预设

要管理预设，请先选中一个游戏实例，然后切换到**高级**页。

在预设配置标签框架下名为**安装预设**的下拉菜单中，您可以快速切换实例。

点击下拉菜单右侧的齿轮按钮，可进入**管理预设**界面。

在预设管理界面中，您可以：
- 对该实例的预设本身进行增删改等操作；
- 改变预设的各项设定；
- 为当前预设生成**自动更新快捷方式**。

### 自定义

#### 体验增强包

体验增强包是一组适用于Mir Korabley的模组，其中包含：
- [输入法支持模组](https://bbs.nga.cn/read.php?tid=29102783)；
- 基于Unbound框架的UI优化模组；
- 基于当前本地化语言的、对其他Mir Korabley模组的翻译补丁模组；
- 带有本团队标识的开屏Logo补丁。

默认预设下将会安装体验增强包，您也可以在**管理预设**界面中选择是否安装它。

#### 字体优化包

字体优化包是适用于Mir Korabley的字体优化模组，其中包含了SrcWagon——基于Mir Korabley原生字体“ALS Wagon”和“Source Han Sans CN”制作的新字体，修复了部分字形的外观与位置。

当您预设中的本地化语言设置为**简体中文**、**繁体中文**或**日文**时，将默认安装字体优化包，您也可以在**管理预设**界面中选择是否安装它。

#### 本地化修改包

本地化修改包用于对本地化包的局部文本进行修改。关于本地化修改包的制作，请查阅[Mir Korabley论坛上的帖子](https://forum.korabli.su/topic/162025-)。

您可以将已制作的本地化修改包直接拖入或是打包到zip文件后放入（通过点击**管理预设**界面中的文件夹图标按钮打开的）当前预设所使用的本地化修改包文件夹。

本地化修改包将在您**下一次**安装本地化包时被加载。

默认预设下将会安装本地化修改包，您也可以在**管理预设**界面中选择是否安装它。

### 应用设定

在**设置**页中，您可以：
- 调整应用的**外观**、**下载**、**文件**相关设置；
- 清除下载缓存和输出日志；
- 查看应用的工作目录和数据目录。

### 应用信息

在**关于**页中，您可以：
- 查看应用的版本，并为应用**检查更新**；
- 通过点击图标为GitHub、QQ、Discord的按钮来访问此应用的源代码仓库或加入本团队在对应社交平台上的群组；
- 通过点击版权标注信息上方的紫色“AGPL V3”图标来跳转到GNU的官方网页，以查看本应用许可证的全文。

## Q&A

### 应用出现报错或本地化包安装失败怎么办？

请先尝试[**检查更新**](#应用信息)后重新安装本地化包。

点击**设置**页，点击**应用数据路径**行的**打开目录**按钮。在被打开的文件夹中，进入logs文件夹，并保存好最新的.log文件。

您可以打开该文件尝试分析报错原因并自行修复，或将文件提交到[GitHub Issues](https://github.com/LocalizedKorabli/LKInstaller-Next/issues) | [QQ群](https://qm.qq.com/q/SUoZAcV442) | [Discord服务器](https://discord.gg/3d9k2mkWy4) 以寻求帮助。

### 自动更新功能去哪里了？

请见[管理预设](#管理预设)。您可以在**管理预设**界面中为当前预设生成**自动更新快捷方式**。

### 对本地化包本身有疑问怎么办？

请根据您所使用的语言和客户端类型，在[团队主页传送门](https://github.com/LocalizedKorabli#%E9%A1%B9%E7%9B%AE%E4%BC%A0%E9%80%81%E9%97%A8portal)中找到相关的仓库，并在其Issues中提交反馈。

您也可以加入QQ群或Discord服务器参与讨论。

## 鸣谢

- 参与本项目内部测试的所有用户

- [Python](https://www.python.org/)——本应用所使用的编程语言

- [Tkinter](https://docs.python.org/3/library/tkinter.html)——本应用所使用的GUI框架

- [Google Gemini](https://gemini.google.com/)——将本应用的开发时间缩短了约70%

- [Azure theme for ttk](https://github.com/rdbende/Azure-ttk-theme)——本应用界面所使用的ttk主题

- [Inno Setup](https://jrsoftware.org/isinfo.php)和[PyInstaller](https://pyinstaller.org/)——为本应用提供了便捷的打包方案

