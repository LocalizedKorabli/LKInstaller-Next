# LKInstaller Next → Rust 移植计划

## 概述

将 **LKInstaller Next**（Python/Tkinter 应用）移植到 Rust，分两个版本：

| 版本 | 技术栈 | 目标 |
|------|--------|------|
| **LK Blaze** | Rust + Tauri v2 + Svelte 5 | 现代桌面 GUI 应用 |
| **LK Retro** | Rust + ratatui + crossterm | TUI 终端应用，**支持 Windows 7** |

**核心思路**：两个版本共享一个公共 Rust 核心库 `lk-core`，各自前端只负责 UI 层。

---

## 仓库结构

```
lk-next-rust/
├── Cargo.toml                  # [workspace]
├── lk-core/                    # 共享核心库（业务逻辑 + 数据模型 + 平台抽象）
├── lk-blaze/                   # Tauri v2 + Svelte 5 桌面版
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── main.rs         # Tauri 入口，注入 lk-core
│   │   │   ├── commands/       # Tauri commands (instance, installation, settings...)
│   │   │   └── lib.rs
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   └── src/                    # Svelte 5 前端
│       ├── routes/
│       ├── components/
│       ├── lib/
│       └── app.html
├── lk-retro/                   # ratatui + crossterm TUI 版
│   ├── src/
│   │   ├── main.rs
│   │   ├── app.rs              # TUI 应用主循环
│   │   ├── tabs/               # 各标签页 widget
│   │   ├── widgets/            # 可复用 UI 组件
│   │   └── cli.rs              # CLI 参数解析 + 静默模式
│   ├── Cargo.toml
│   └── build.rs                # Win7 兼容构建配置
├── resources/                  # 共享资源
│   ├── locales/                # Fluent (.ftl) 翻译文件
│   ├── icons/                  # SVG 图标（Blaze 用）
│   └── logo/                   # Logo 文件
├── support/                    # 安装脚本、CI 配置等
│   ├── innosetup/              # Retro 版安装脚本（可选）
│   └── github/                 # GitHub Actions workflows
└── README.md
```

---

## 第一阶段：lk-core 共享核心库

将现有 Python 业务逻辑全部移植到 Rust，作为 workspace 的公共 crate。

### 1.1 设置与配置 (`lk-core/src/config/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `core/settings.py` | `config/mod.rs` | `GlobalSettings` → serde 序列化结构体 |
| `core/dirs.py` | `config/paths.rs` | 路径管理（LOCALAPPDATA / portable 回退） |
| `core/constants.py` | `config/constants.rs` | 版本号等常量 |

- 配置存储：`%LOCALAPPDATA%/LocalizedKorabli/LKInstallerNext/settings/global.json`
- 依赖：`serde`、`serde_json`、`dirs` crate
- Windows 注册表读写的 MSIX 检测逻辑

### 1.2 本地化引擎 (`lk-core/src/i18n/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `core/localizer.py` | `i18n/mod.rs` | Fluent 加载器 |

- 使用 **Fluent (.ftl)** 格式替代 JSON
- 将现有 `resources/locales/*.json` 迁移为 `*.ftl`，保留五种语言：
  - `zh_CN`、`zh_TW`、`en`、`ja`、`ru`
- 编译时生成绑定（`rust-i18n` 或 `fluent-rs`）
- 保留 `_best_fonts` 字体映射

### 1.3 日志系统 (`lk-core/src/logging/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `core/logger.py` | `logging/mod.rs` | 日志初始化 |

- 使用 `tracing` crate + `tracing-appender` 文件输出
- 支持 stderr 重定向捕获崩溃日志
- 日志路径：`%LOCALAPPDATA%/.../logs/lki-next-{date}.log`
- 自动轮转或按日期分割

### 1.4 游戏实例层 (`lk-core/src/instance/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `instance/game_instance.py` | `instance/game_instance.rs` | `GameInstance`、`GameVersion`、`LocalizationInfo` |
| `instance/instance_detector.py` | `instance/detector.rs` | 自动检测游戏安装 |
| `instance/instance_manager.py` | `instance/manager.rs` | 实例 CRUD + JSON 持久化 |

关键实现：

- **PE 版本读取**（`Korabli64.exe` ProductVersion）：Win32 API `GetFileVersionInfo`，通过 `windows-sys` 或 `winapi` crate 调用
- **SHA256 文件验证**：`sha2` crate
- **注册表扫描**：`winreg` crate
- **实例 ID**：`sha256(normalized_path)`
- **预设系统**：支持默认/自定义预设，`lang_code`、`use_ee`、`use_fonts`、`use_mods`、`use_lk_mods`

### 1.5 下载基础设施 (`lk-core/src/download/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `installation/installation_utils.py` | `download/manager.rs` | 下载、缓存、解压 |
| `installation/localization_sources.py` | `download/sources.rs` | 镜像路由配置 |

- HTTP 客户端：`reqwest`（支持代理 `reqwest::Proxy`）
- 多镜像路由优先级（`CloudFlare`、`GitLab`、`GitHub`、`Gitee`、`Tencent`）
- 故障转移：主路由失败自动切换到下一个
- 文件缓存：`%LOCALAPPDATA%/.../cache/`
- 临时目录管理：`tempfile` crate
- ZIP/MO 解压：`zip` crate + 自定义 `.mo` 解析（gettext 二进制格式）

### 1.6 安装逻辑 (`lk-core/src/install/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `installation/installation_manager.py` | `install/manager.rs` | 安装任务编排 |
| `installation/installation_utils.py`（部分） | `install/patch.rs` | 文件修补 |

- `.mo` 文件分发到 `bin/<version>/res/texts/`
- `locale_config.xml` 修改（`quick-xml` crate）
- Experience Enhancement ZIP 解包安装
- 字体文件安装
- Mods 安装
- `installation_info.json` 写入（安装状态追踪）
- 组件状态验证（`i18n`、`ee`、`font`、`mods`）

### 1.7 计划任务抽象 (`lk-core/src/scheduler/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `core/scheduler.py` | `scheduler/mod.rs` | Windows Task Scheduler 集成 |

- 通过 `schtasks.exe` 命令行或 COM 接口管理计划任务
- 支持：一次性、每日、每周、登录时、启动时、空闲时触发
- 构建 `--auto-execute-preset` 参数

### 1.8 工具函数 (`lk-core/src/utils/`)

| Python 文件 | Rust 对应 | 说明 |
|---|---|---|
| `core/utils.py` | `utils/mod.rs` | 跨平台工具 |

- HiDPI 检测（Windows `GetDpiForWindow`，但 Retro 版需做 Win7 兼容判断）
- MSIX 包检测（`GetCurrentPackageFullName` Win32 API）
- 路径规范化、防 ASCII 路径警告
- 系统语言/时区检测
- `scale_dpi()` 缩放辅助

### 关键依赖 (lk-core)

```toml
[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tracing = "0.1"
tracing-appender = "0.2"
reqwest = { version = "0.12", features = ["socks", "gzip"] }
sha2 = "0.10"
zip = "2"
quick-xml = "0.36"
winreg = "0.52"
windows-sys = { version = "0.59", features = ["Win32_System_Kernel", "Win32_UI_HiDpi"] }
fluent-fluent-bundle = "0.15"
fluent-resmgr = "0.8"
unic-langid = "0.9"
tempfile = "3"
dirs = "6"
```

---

## 第二阶段：LK Blaze（Tauri v2 + Svelte 5）

### 2.1 Tauri 后端

- **初始化**：`create-tauri-app` 选择 Tauri v2 + Svelte 5 + TypeScript
- **状态管理**：`tauri::State<AppState>` 持有 `lk-core` 的各项管理器
- **Commands**：
  - `get_instances` / `detect_instances` / `add_instance` / `remove_instance`
  - `get_presets` / `save_preset` / `delete_preset` / `set_active_preset`
  - `start_installation` / `cancel_installation`（events 推送进度）
  - `get_settings` / `update_settings`
  - `get_available_languages`
  - `check_for_updates`
  - `launch_game`
- **事件系统**：安装进度、任务状态变更 → 前端响应式更新

### 2.2 Svelte 5 前端

布局：顶部标签栏 + 主内容区，共**三个**标签页（原"高级"内容合并进游戏页的可展开卡片）。

**游戏标签页** (`GamePage.svelte`)：
- 游戏实例卡片列表，每个卡片**可展开/折叠**
- **卡片折叠态**：实例名称、类型徽标、路径摘要、组件状态指示灯（绿/黄/红）、展开按钮 `▸`
- **卡片展开态**（点击卡片或 `▸` 展开）：
  - 实例详细信息（完整路径、版本信息）
  - **预设管理区域**：当前预设名称、预设下拉切换、`+` 添加预设、`✎` 编辑、`🗑` 删除
  - **预设配置表单**（内联在卡片中）：
    - 本地化语言选择（下拉）
    - 组件开关组：EE（体验增强）、字体（含字体 ID 选择）、Mods、LK Mods
  - 操作按钮组：`▶ 安装此预设`、`📋 复制路径`、`🔄 刷新状态`
  - **计划任务配置**：简化版（快速设置每日/每周自动更新），或跳转到设置页完整配置
- 卡片外全局操作栏：`🔍 自动检测实例`、`☑ 全选`、`▶ 安装选中`、`↑↓ 排序`
- 多实例批量安装时，展开所有进行中的卡片显示实时进度条

**设置标签页** (`SettingsTab.svelte`)：
- 主题切换（亮/暗，CSS 变量实现）
- UI 语言选择
- 代理配置（模式、主机、端口）
- 下载路由优先级排序（拖拽或上下移动）
- 清除缓存按钮
- 关于应用信息

**关于标签页** (`AboutTab.svelte`)：
- Logo + 应用名称版本
- AGPL v3 许可证信息
- 链接：官网、GitHub、Discord、QQ
- 更新检查

### 2.3 LK Blaze 前端设计规范（干净极简方向）

> 基于 `frontend-design` skill 输出。风格定调：**日式极简 × 工业精密**——灵感来自 Muji 的留白哲学与 iOS 设置页的信息层级，拒绝一切装饰性冗余。

#### 2.3.1 设计方向

| 维度 | 选择 |
|------|------|
| **风格关键词** | 干净、安静、精确、呼吸感、去边框化 |
| **差异化记忆点** | 卡片展开/折叠的"翻折"微动效（纸张折叠隐喻）+ 仅用 typography 作为视觉层级工具 |
| **情绪板参考** | Linear.app 的极简任务管理 × Notion 的块编辑器 × Arc browser 的边栏 |

#### 2.3.2 色彩系统

基于两个原则：**内容为王**（色彩服务于可读性）、**克制用色**（一个强调色，其余全是中性色）。

**亮色模式：**

```
--bg-base:          #FAFAF8  (米白基底，比纯白暖一度，护眼)
--bg-surface:       #FFFFFF  (卡片/面板)
--bg-hover:         #F3F3F0  (悬浮态)
--border-subtle:    #E8E8E5  (分隔线，极淡)
--text-primary:     #1A1A18  (主文字)
--text-secondary:   #8A8A86  (辅助文字)
--text-tertiary:    #B8B8B4  (最弱文字/占位符)
--accent:           #2B7A4B  (深绿——安装完成/成功感，而非蓝色)
--accent-hover:     #23683E
--danger:           #C73A3A  (错误/篡改)
--warning:          #B8860B  (警告/未安装)
--badge-bg:         #EDEDEA  (标签底色)
```

选用深绿而非蓝色作为强调色：本地化安装的本质是"让游戏说你的语言"，绿色象征通过/就绪/自然，与"澪刻"品牌名的水/刻印意象呼应。

**暗色模式：**

```
--bg-base:          #121210  (近黑，带一丝暖)
--bg-surface:       #1B1B18  (卡片)
--bg-hover:         #252522
--border-subtle:    #2C2C29
--text-primary:     #ECECE5
--text-secondary:   #8A8A84
--text-tertiary:    #555552
--accent:           #4CAF6E  (亮绿)
--accent-hover:     #66BB7A
--badge-bg:         #2C2C29
```

#### 2.3.3 字体系统

**禁止使用** Inter、Roboto、Arial、系统默认字体——这些是"AI 感"的元凶。

```
--font-display:    "DM Sans", "Noto Sans SC", sans-serif
--font-body:       "DM Sans", "Noto Sans SC", sans-serif
--font-mono:       "JetBrains Mono", "Noto Sans Mono", monospace
```

| 用法 | 字重 | 字号 | 行高 |
|------|------|------|------|
| 应用标题 / 大号展示 | 500 | 1.5rem | 1.2 |
| 实例名称（卡片标题） | 500 | 1rem | 1.4 |
| 正文 / 表单标签 | 400 | 0.875rem | 1.5 |
| 辅助文字 / 状态 | 400 | 0.75rem | 1.4 |
| 等宽（路径/版本号） | 400 | 0.8125rem | 1.4 |

选择 DM Sans：几何感强但温暖，数字和标点特别清晰，适合显示路径/版本号等技术内容。Noto Sans SC 作为中文后备，保证 CJK 字符的家族一致性。

#### 2.3.4 间距与布局

采用 **4px 栅格系统**，所有间距为 4 的倍数。

```
--space-xs:   4px
--space-sm:   8px
--space-md:   16px
--space-lg:   24px
--space-xl:   32px
--space-2xl:  48px
```

**窗口布局：**
```
┌──────────────────────────────────────────┐
│            标签栏 (40px)                  │  ← 极细，仅文字标签，无边框卡片式
├──────────────────────────────────────────┤
│                                          │
│    ┌─ 全局操作栏 ─────────────────┐      │  ← 32px 高，图标+文字
│    │  🔍 检测   ☐ 全选  ▶ 安装   │      │
│    └──────────────────────────────┘      │
│                                          │
│    ┌─ 实例卡片 ───────────────────┐      │  ← 圆角 8px, 阴影极淡
│    │  ☐  Lesta RU  ○ production  │      │  ← 折叠态 56px
│    │  C:\Games\Korabli           │      │
│    │  ● i18n  ● EE  ○ font  ○ m │      │
│    │                          ▾  │      │  ← 展开指示器
│    ├──────────────────────────────┤      │
│    │  ...展开内容...              │      │  ← 展开态，内边距 20px
│    │                              │      │
│    └──────────────────────────────┘      │
│                                          │
│    ┌─ 实例卡片 ───────────────────┐      │
│    │  ...                          │      │
│    └──────────────────────────────┘      │
│                                          │
└──────────────────────────────────────────┘
    窗口默认尺寸: 420px × 640px (肩并肩不拥挤)
```

#### 2.3.5 卡片交互设计

**折叠态（默认）：**

```
┌──────────────────────────────────────────────┐
│  ☐  Lesta RU                        ⬤ prod  │  行1: 复选框 + 实例名 + 类型徽标
│  C:\Games\Korabli                            │  行2: 路径（次级文字，单行截断）
│  ● i18n  ● EE  ○ font  ○ mods       ▾ Inst. │  行3: 组件状态点 + 安装状态标签
└──────────────────────────────────────────────┘
```

- 状态点含义：● 绿色 = 已安装且验证通过，◉ 黄色 = 未安装，○ 灰色 = 不适用
- 整张卡片可点击展开，但复选框区域只处理选中
- 过渡动效：`max-height` + `opacity` 平滑展开，150ms ease-out

**展开态：**

```
┌──────────────────────────────────────────────┐
│  ☐  Lesta RU                        ⬤ prod  │
│  C:\Games\Korabli\bin\35\bin64               │  ← 展开后显示完整版本路径
│  v0.35.0.1  •  上次安装: 2025-06-20 14:30    │
├──────────────────────────────────────────────┤
│  预设: [默认预设           ▾]  +  ✎  🗑     │  ← 预设选择器 + 操作
│                                              │
│  本地化语言  [简体中文 ▾]                     │  ← 表单内联
│  ── 组件 ──                                  │
│  ☑ 体验增强 (EE)              ☑ 安装字体     │
│  ☑ 安装 Mods                 字体: [推荐 ▾]  │
│  ☑ LK Mods (跟随全局设置)                    │
│  ── 计划任务 ──                              │
│  ○ 不自动更新  ● 每日 08:00  ○ 每周一 08:00  │
│                                              │
│  [  安装此预设  ]  [复制路径]  [刷新状态]     │  ← 操作按钮
└──────────────────────────────────────────────┘
```

- 展开区域背景不变，仅通过内边距增加和分隔线区分
- 所有表单控件极简化：switch 用纯 CSS 圆点滑块，select 用原生箭头
- 按钮使用 outline 样式（无填充），hover 时填充强调色

#### 2.3.6 动效原则

极简 ≠ 没有动效；动效应服务于理解，而非装饰。

| 元素 | 动效 | 时长 | 缓动 |
|------|------|------|------|
| 卡片展开/折叠 | max-height + opacity | 200ms | ease-out |
| 标签页切换 | 立即切换，无滑动 | 0 | — |
| 状态更新（安装进度） | 数字平滑过渡 | 300ms | ease |
| 按钮 hover | 背景色填充 | 100ms | ease |
| 进度条 | 连续条 + 百分比数字 | 实时 | linear |

禁止：弹跳、旋转、飞入飞出、粒子效果。

#### 2.3.7 图标系统

不使用 emoji（上面示意图中仅用于示意），改用 **Lucide** 开源 SVG 图标集，线条风格，1.5px stroke：

| 用途 | 图标 |
|------|------|
| 自动检测 | `search` |
| 全选 | `check-square` |
| 安装 | `play` |
| 刷新 | `refresh-cw` |
| 复制路径 | `clipboard-copy` |
| 展开/折叠 | `chevron-down` / `chevron-right` |
| 添加预设 | `plus` |
| 编辑预设 | `pencil` |
| 删除预设 | `trash-2` |
| 游戏类型徽标 | `radio` (filled = production, outlined = pts) |
| 强调色主题色 | 全部使用 `currentColor`，跟随文字色 |

#### 2.3.8 关于页设计

刻意极简——仅三段内容居中：

```
┌──────────────────────────────────────┐
│                                      │
│              [Logo SVG]              │  ← 64px 宽，灰度
│                                      │
│          LK Blaze  v1.1.0            │  ← font-display 500
│                                      │
│    Mir Korabley 本地化安装器          │  ← text-secondary
│                                      │
│    © 2025 LocalizedKorabli           │
│    AGPL v3 许可证                     │
│                                      │
│    GitHub  •  Discord  •  QQ 群      │  ← 文字链接，下划线 hover
│                                      │
└──────────────────────────────────────┘
```

没有大标题、没有 hero 图片、没有装饰边框。Logo 用灰度 SVG（不抢眼），版本号是页面上唯一的大字号文字。

#### 2.3.9 实现要点

- 所有 CSS 变量定义在 `:root` 和 `[data-theme="dark"]` 中
- 暗色模式切换仅需切换 `data-theme` 属性，无 FOUC
- 使用 `svelte:head` 加载 Google Fonts (DM Sans, Noto Sans SC, JetBrains Mono)
- 字体文件建议下载自托管，避免 Tauri 应用依赖网络
- Lucide 图标使用 `svelte-lucide` 包，按需引入

### 2.10 资源处理

- 图标：PNG → SVG 图标（Svelte 组件或内联 SVG）
- Logo / 图片：嵌入 Tauri bundle
- 国际化：Fluent `.ftl` 资源通过 Tauri 命令加载

### 2.11 打包

- Tauri bundler：Windows (NSIS / MSI)、macOS (DMG)、Linux (.deb / AppImage)
- 自动更新机制（Tauri updater）

---

## 第三阶段：LK Retro（Tauri v2 + Svelte 5 + XP.css）

**重大变更**：Retro 不再使用 ratatui/crossterm TUI，改为与 Blaze 相同的 Tauri v2 + Svelte 5 架构，但使用 **XP.css** 复古 Windows XP 主题，以原生窗口外观运行在 Windows 7 上。

### 3.1 架构定位

```
lk-next-rust/
├── lk-core/              # 共享核心库（两个版本共用）
├── lk-blaze/             # Tauri v2 + Svelte 5 + 现代极简主题
└── lk-retro/             # Tauri v2 + Svelte 5 + XP.css 复古主题
```

**差异点仅在于**：
- CSS 主题文件不同（Blaze = 自定义极简变量，Retro = XP.css）
- 部分布局决策不同（Retro 使用经典四标签页，Blaze 使用三标签页+可展开卡片）
- Retro 需要额外处理 WebView2 运行时分发

### 3.2 Windows 7 兼容策略

| 关注点 | 做法 |
|--------|------|
| **Tauri 版本** | 使用 **Tauri v2**（官方明确支持 Windows 7） |
| **WebView2 运行时** | 在安装时附带 Evergreen WebView2 Bootstrapper（~2MB），静默安装到目标机器 |
| **WebView2 分发** | 使用 Tauri bundler 的 `webview2-install-mode` 配置为 `"bootstrapper"`（安装时自动下载安装）；或离线打包完整运行时 |
| **Windows API** | Tauri v2 的 `wry` 层已处理 Win7 兼容；Rust 端通过 `windows-sys` 条件编译避免 Win8+ API |
| **MSVC 运行时** | 静态链接 MSVC CRT（`+crt-static`），避免需要 KB2999226 |
| **DPI** | XP.css 是固定像素设计（96 DPI），在 HiDPI 下可让 Tauri 窗口的 `zoom` 因子保持 1.0，保留原始像素外观 |
| **Unicode** | XP.css 本身是纯 CSS，不影响；Svelte/HTML 原生支持 UTF-8，中文/俄文/日文正常显示 |

```toml
# lk-retro/.cargo/config.toml
[target.x86_64-pc-windows-msvc]
rustflags = ["-C", "target-feature=+crt-static"]
```

### 3.3 UI 风格：XP.css

导入方式：
```html
<!-- index.html -->
<link rel="stylesheet" href="https://unpkg.com/xp.css">
```

或通过 npm 安装并本地打包：
```bash
npm install xp.css
```

```svelte
<!-- 在 Svelte 中导入 -->
<script>
  import "xp.css/dist/XP.css";
</script>
```

#### 可用组件（XP.css 原生提供）

| XP.css 组件 | 对应用途 |
|---|---|
| `<button>` | 所有按钮 |
| `<input type="checkbox">` | 组件开关、全选 |
| `<input type="radio">` | 单选选项 |
| `<input type="text">` | 文本输入 |
| `<textarea>` | 多行输入 |
| `<select>` | 下拉选择（语言、预设） |
| `<progress>` | 安装进度条 |
| `<fieldset>` + `<legend>` | 设置分组 |
| `.tabs` + `role="tablist"` | 标签页导航（原生 XP 标签外观） |
| `.title-bar` + `.window` + `.window-body` | 窗口容器 |
| `.status-bar` + `.status-bar-field` | 底部状态栏 |
| `.tree-view` | 版本列表树 |
| `.field-row` / `.field-row-stacked` | 表单排列 |
| `<input type="range">` | 滑块（如有需要） |

#### 主题切换

XP.css 提供两套主题：
- `xp.css` → Windows XP 经典（蓝/绿/银渐变，Luna 风格）
- `98.css` → Windows 98 经典（灰色、凸起边框）

```html
<!-- XP 主题 -->
<link rel="stylesheet" href="https://unpkg.com/xp.css/dist/XP.css">
<!-- 或 98 主题 -->
<link rel="stylesheet" href="https://unpkg.com/xp.css/dist/98.css">
```

可在 Retro 设置页添加"主题"切换（XP / 98）。

### 3.4 UI 布局——四标签页（经典设计）

与 Blaze 不同，Retro 保留独立的"高级"标签页，因为 XP.css 的标签组件（`role="tablist"`）原生支持多标签，且卡片展开交互在 XP 风格中不够自然。

```
┌────────────────────────────────────────────────────────────────┐
│  [■] LK Retro - Mir Korabley 本地化安装器                  [─][□][✕] │  ← XP 原生标题栏
├────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  [游戏]  [高级]  [设置]  [关于]                          │      │  ← XP.css tabs
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│                   当前标签页内容（XP.css styled）                      │
│                                                                      │
│                                                                      │
├────────────────────────────────────────────────────────────────┤
│  LK Retro v1.1.0  │  实例: Lesta RU  │  CPU: 2%              │  ← status-bar
└────────────────────────────────────────────────────────────────┘
```

**游戏标签页**：
- 实例列表（`<ul class="tree-view">` 或自定义表格）
- 每项：复选框 + 名称 + 类型标签 + 安装状态文字
- 底部操作栏：`<button>` 检测、全选、安装选中、刷新
- 实例详情在右侧或底部面板（`<fieldset>` 包裹），选中实例后显示
- 安装进度条：`<progress>` 元素

**高级标签页**：
- 当前选中实例的预设管理
- 预设下拉选择 + 添加/编辑/删除按钮
- 预设配置：`<fieldset>` 分组，`<input type="checkbox">` 组件开关，`<select>` 语言/字体选择
- 计划任务配置：简洁的表单

**设置标签页**：
- 语言选择（`<select>`）
- 主题切换（XP / 98 / 经典灰，单选按钮组）
- 代理配置（文本输入）
- 下载路由排序（列表 + 上下移动按钮）
- 清除缓存按钮

**关于标签页**：
- Logo（可使用经典的 Windows 对话框中图标样式）
- 版本号、许可证信息
- 链接按钮组

### 3.5 WebView2 运行时分发

这是 Retro 版在 Win7 上唯一需要额外处理的部分。

**选项 A（推荐）— Bootstrapper 模式**：
Tauri bundler 配置：
```json
{
  "bundle": {
    "windows": {
      "webview2InstallMode": "bootstrapper"
    }
  }
}
```
安装时自动下载安装 WebView2 Evergreen Runtime（~2MB 启动器），静默安装。

**选项 B — 离线打包**：
在安装程序中捆绑 WebView2 离线安装包（~130MB），适用于无网络环境的 Win7 机器。

**选项 C — 使用固定的 Edge Chromium 版本**：
Tauri 支持 `fixedVersion` 模式，在应用目录中捆绑特定版本的 WebView2 二进制文件。

### 3.6 与 Blaze 的代码复用

```
lk-retro/src-tauri/src/
├── main.rs              # Tauri 入口（结构与 lk-blaze 相同）
├── lib.rs
└── commands/            # Tauri commands（与 lk-blaze 共用相同的 Rust 函数）
```

**Commands 复用策略**：
- 将 commands 函数放在 `lk-core` 或独立的 `lk-commands` crate 中
- 或者直接在各自 `src-tauri/src/commands/` 中引用 `lk-core` 的公共 API
- Tauri 的 `#[tauri::command]` 函数体在两个版本中几乎相同

**Svelte 组件复用**：
- 部分 UI 逻辑组件（如安装进度条逻辑）可放在共享的 `lk-ui-shared` Svelte 库中
- 样式完全不共享（Blaze = CSS 变量极简风，Retro = XP.css）

### 3.7 关键依赖

```toml
# lk-retro/src-tauri/Cargo.toml
[dependencies]
lk-core = { path = "../../lk-core" }
tauri = { version = "2", features = [] }
tauri-build = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```json
// lk-retro/package.json
{
  "dependencies": {
    "xp.css": "^1.0.0",
    "svelte": "^5"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2",
    "vite": "^6",
    "@sveltejs/vite-plugin-svelte": "^5"
  }
}
```

---

## 第四阶段：构建、测试与分发

### 4.1 Cargo Workspace 统一构建

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["lk-core", "lk-blaze", "lk-retro"]

[workspace.package]
version = "1.1.0"
edition = "2024"
license = "AGPL-3.0"
```

构建命令：

```bash
# 共享库 (测试用)
cargo test -p lk-core

# LK Blaze
cd lk-blaze && cargo tauri build

# LK Retro (Win7 兼容)
cd lk-retro && cargo tauri build
```

### 4.2 GitHub Actions CI

```yaml
# .github/workflows/build.yml
jobs:
  lk-core:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - run: cargo test -p lk-core

  lk-blaze:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tauri-apps/tauri-action@v2
        with:
          projectPath: lk-blaze

  lk-retro:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tauri-apps/tauri-action@v2
        with:
          projectPath: lk-retro
```

### 4.3 Fluent 翻译资源迁移

将现有 `resources/locales/*.json` 转为 `resources/locales/*.ftl`。

例如 `en.json` 中的条目：
```json
{
  "lki.app.title": "LK Next: Mir Korabley L10n Installer",
  "lki.tab.game": "Game",
  "lki.preset.default.name": "Default"
}
```

转为 `en.ftl`：
```fluent
lki-app-title = LK Next: Mir Korabley L10n Installer
lki-tab-game = Game
lki-preset-default-name = Default
```

### 4.4 安装程序

- **LK Blaze**：Tauri bundler (NSIS)，仅 Windows 10+
- **LK Retro**：Tauri bundler (NSIS)，附 WebView2 bootstrapper 自动安装运行时；可选 Inno Setup 脚本沿袭现有 `pack.iss` 逻辑
- **两个版本共享**：同一个 Inno Setup 项目文件，通过条件编译选择打包哪个版本

### 4.5 文档

- `README.md`：项目概述、两个版本的截图对比（现代 vs 复古）、安装方式
- `BUILD.md`：构建指南
- `CONTRIBUTING.md`：贡献指南
- `CHANGELOG.md`：版本历史

---

## 附录：架构总览

### 最终仓库结构

```
lk-next-rust/
├── Cargo.toml                  # [workspace]
├── lk-core/                    # 共享核心库
├── lk-blaze/                   # Tauri v2 + Svelte 5 + 现代极简
│   ├── src-tauri/              # Rust 后端
│   └── src/                    # Svelte 5 前端
├── lk-retro/                   # Tauri v2 + Svelte 5 + XP.css 复古
│   ├── src-tauri/              # Rust 后端（与 blaze 共用 commands 模式）
│   └── src/                    # Svelte 5 前端
├── resources/                  # 共享资源
│   ├── locales/                # Fluent (.ftl)
│   └── logo/                   # Logo
└── README.md
```

### 两个版本对比

| 维度 | LK Blaze | LK Retro |
|------|----------|----------|
| **引擎** | Tauri v2 + Svelte 5 | Tauri v2 + Svelte 5 |
| **主题** | 日式极简（DM Sans + 深绿强调） | Windows XP 复古（XP.css） |
| **标签页数** | 3（游戏/设置/关于） | 4（游戏/高级/设置/关于） |
| **实例交互** | 可展开/折叠卡片 | 选中 → 详情面板 |
| **目标 OS** | Windows 10+, macOS, Linux | Windows 7+ |
| **WebView2** | 系统自带（Win10+） | 安装时自动部署 |
| **设计关键词** | 干净、留白、呼吸感 | 怀旧、像素、Luna |

### Rust 映射对照

| Python 模块 | lk-core 模块 | 前端映射 |
|---|---|---|
| `lki.py` | — | `main.rs` (Tauri 入口) |
| `core/settings.py` | `config/` | Tauri state 访问 |
| `core/dirs.py` | `config/paths.rs` | Tauri state 访问 |
| `core/localizer.py` | `i18n/` | Fluent loader |
| `core/logger.py` | `logging/` | 初始化时配置 |
| `core/scheduler.py` | `scheduler/` | Tauri commands |
| `core/utils.py` | `utils/` | 内部调用 |
| `instance/*` | `instance/` | Tauri commands |
| `installation/*` | `download/` + `install/` | Tauri commands |
| `ui/app.py` | — | `App.svelte`（Blaze 极简 / Retro XP.css） |
| `ui/tabs/tab_game.py` | — | `GamePage.svelte` |
| `ui/tabs/tab_advanced.py` | — | Retro: `AdvancedTab.svelte`；Blaze: 合并到卡片中 |
| `ui/tabs/tab_settings.py` | — | `SettingsTab.svelte` |
| `ui/tabs/tab_about.py` | — | `AboutTab.svelte` |
| `ui/dialogs.py` | — | Svelte modals / 内联表单 |
| `ui/ui_manager.py` | — | CSS 变量 / XP.css |
| 资源文件 | — | `resources/` Fluent + assets |

---

## 开发路线图（建议顺序）

```
Weeks 1-2   第一阶段：lk-core
             ├── 项目初始化 + workspace 结构
             ├── config/paths + settings 移植
             ├── logging 移植
             ├── i18n + Fluent 迁移
             ├── instance/ 检测 + 管理移植
             └── 单元测试覆盖

Weeks 3-4   第一阶段续：lk-core
             ├── download/ HTTP + 路由 + 缓存
             ├── install/ 文件修补 + 安装编排
             ├── scheduler/ 移植
             └── utils/ 工具函数

Weeks 5-6   第二阶段：LK Blaze
             ├── Tauri v2 初始化 + 后端 commands
             ├── Svelte 5 框架 + 三标签页布局
             ├── 游戏页：实例卡片（可展开/折叠）
             │   ├── 卡片折叠态 + 展开态 UI
             │   ├── 内联预设管理 + 配置表单
             │   └── 计划任务快捷配置
             ├── 设置页 + 关于页
             ├── 安装进度推送 + 实时反馈
             └── 极简主题系统 + Lucide 图标

Weeks 7-8   第三阶段：LK Retro
             ├── Tauri v2 项目初始化（与 Blaze 共享 commands）
             ├── XP.css 主题集成
             ├── 四标签页布局（游戏/高级/设置/关于）
             ├── 游戏页：实例列表 + 详情面板
             ├── 高级页：预设管理
             ├── 安装进度 + 状态栏
             ├── WebView2 运行时部署方案
             └── Windows 7 兼容性测试

Weeks 9-10  第四阶段：收尾
             ├── CI/CD 配置（两个版本并行构建）
             ├── 打包测试（Blaze NSIS / Retro NSIS+WebView2）
             ├── README + 文档 + 截图
             └── 端到端测试
```

---

*本计划基于 LKInstaller Next v1.1.0，AGPL v3 许可证。*

