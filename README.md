<p align="center">
  <img src=".github/images/icon.svg" alt="Minecraft UniBot" width="120" height="120">
</p>

<p align="center">
  <img src="https://img.shields.io/github/v/release/MineJPGcraft/UniBot" alt="版本">
  <img src="https://img.shields.io/github/license/MineJPGcraft/UniBot" alt="许可证">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/NoneBot2-2.2%2B-purple" alt="NoneBot2">
  <!-- <img src="https://img.shields.io/github/downloads/MineJPGcraft/UniBot/total" alt="下载量"> -->
</p>

<h1 align="center">Minecraft UniBot</h1>

<p align="center">
  <b>跨平台 · 多服互联 · 即插即用 — 让 Minecraft 与你的聊天世界无缝相连</b>
</p>

<p align="center">
  <a href="https://qm.qq.com/q/B3kmvJl2xO">💬 加入 QQ 群</a>
  ·
  <a href="https://github.com/MineJPGcraft/UniBot/issues">🐛 反馈问题</a>
  ·
  <a href="https://bot.mcjpg.dev/">**📚 项目文档**</a>
</p>

---

## ✨ 亮点速览

| 特性 | 说明 |
|------|------|
| **🌐 真正的跨平台** | 不止 QQ，还支持 Telegram、Discord、Kook、QQ 频道等，一套指令全平台通用 |
| **🔗 多服互联** | 同时连接多台 Minecraft 服务器，消息互通，跨服聊天零延迟 |
| **🔄 全服务端兼容** | 支持 Fabric、Forge、Spigot、Paper 等主流服务端，即插即用，无需额外适配 |
| **🧩 模块化架构** | 指令按插件拆分，扩展新功能就像搭积木 |
| **🖥️ WebUI 管理面板** | 的现代化管理界面，可视化配置、实时监控、日志查看，开箱即用 |
| **🤖 AI 智能对话** | 接入任意 OpenAI 兼容 API，@机器人即可与 AI 对话，支持上下文记忆 |
| **🔐 白名单管理** | 完善的平台账号与游戏 ID 绑定系统，支持多服白名单同步 |
| **🎨 图片渲染模式** | 基于 HTML + CSS 模板引擎，将指令输出渲染为精美图片，支持自定义背景 |
<!-- | **🐳 Docker 支持** | 一键部署，开箱即用 | -->

---

## 📸 效果展示

### 🖥️ WebUI 管理面板

| | |
|---|---|
| <p align="center"><img src=".github/images/shows/webui/dashboard.png"><br>仪表盘</p> | <p align="center"><img src=".github/images/shows/webui/server.png"><br>服务器管理</p> |
| <p align="center"><img src=".github/images/shows/webui/config.png"><br>配置管理</p> | <p align="center"><img src=".github/images/shows/webui/adapters.png"><br>适配器管理</p> |
| <p align="center"><img src=".github/images/shows/webui/plugins.png"><br>插件管理</p> | <p align="center"><img src=".github/images/shows/webui/log.png"><br>日志查看</p> |
| <p align="center"><img src=".github/images/shows/webui/market.png"><br>插件市场</p> | |

### 🎨 指令图片渲染

指令输出渲染为精美图片，支持玩家头像与自定义背景：

| | | |
|---|---|---|
| <p align="center"><img src=".github/images/shows/commands/about.png"><br>About 指令</p> | <p align="center"><img src=".github/images/shows/commands/list.png"><br>List 指令</p> | <p align="center"><img src=".github/images/shows/commands/help.png"><br>Help 指令</p> |

---

## 📖 快速开始

### 前置要求

- Python 3.11+
- [UV](https://docs.astral.sh/uv/)（推荐，快速包管理器）或 pip
- Minecraft Java 服务端（需安装 [鹊桥](https://github.com/17TheWord/QueQiao)）
- 一个 QQ 机器人账号（或其他平台账号）

### 🚀 安装与启动

#### 方式一：一键脚本安装（推荐）

从 [Releases 页面](https://github.com/MineJPGcraft/UniBot/releases) 下载对应平台的一键安装脚本：

| 平台 | 脚本 |
|------|------|
| **Windows** | `Install.bat` — 双击运行，自动安装 uv、克隆仓库、配置 WebUI 并同步依赖 |
| **Linux / macOS** | `Install.sh` — `chmod +x Install.sh && ./Install.sh`，一键完成所有部署步骤 |

脚本会自动完成以下操作：
1. 检测并安装 [UV](https://docs.astral.sh/uv/) 包管理器
2. 下载并解压指定版本的 UniBot 仓库
3. 询问是否启用 WebUI（选择 `y` 自动将 `Config.toml` 中的 `[webui] enabled` 改为 `true`）
4. 执行 `uv sync` 同步所有依赖（启用 WebUI 时附带 `--extra webui`）

安装完成后运行机器人仅需 `uv run Watchdog.py`！

> 💡 一键脚本适合快速部署，如需自定义配置可后续编辑 `.env` 和 `Config.toml`。

#### 方式二：使用 UV（手动）

```bash
# 克隆项目
git clone https://github.com/MineJPGcraft/UniBot
cd UniBot

# 创建虚拟环境并安装依赖（UV 自动管理）
uv sync

# 如需启用图片渲染模式，额外安装 image 依赖
uv sync --extra image --inexact

# 如需启用 WebUI 管理面板，额外安装 webui 依赖
uv sync --extra webui --inexact

# 编辑配置文件（按需修改）
# .env — NoneBot 框架与适配器配置
# Config.toml — 机器人自定义配置

# 启动机器人
uv run Watchdog.py
```

> **为什么推荐 UV？**
> UV 比 pip 快 10-100 倍，自动解析依赖冲突，一条命令即可完成虚拟环境创建与依赖安装。
> [官方文档](https://uv.doczh.com/)

#### 方式三：使用 pip + venv（传统方式）

```bash
git clone https://github.com/MineJPGcraft/UniBot
cd UniBot

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .

# 如需启用图片渲染模式，额外安装 image 依赖
pip install -e ".[image]"

# 如需启用 WebUI 管理面板，额外安装 webui 依赖
pip install -e ".[webui]"

# 配置环境（编辑 .env 与 Config.toml）

# 启动
python3 Watchdog.py
```

<!-- ### 🐳 Docker 部署

#### Docker Compose（推荐）

```bash
git clone https://github.com/Minecraft-QQBot/UniBot
cd UniBot
# 编辑 .env 配置文件
docker compose up -d
```

#### 自行构建

```bash
docker build -t minecraft-qqbot .
docker run -d \
  --name minecraft-qqbot \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/Logs:/app/Logs \
  --restart unless-stopped \
  minecraft-qqbot
``` -->

### ⚙️ 配置说明

项目采用 **双配置文件** 体系：

| 文件 | 用途 | 格式 |
|------|------|------|
| `.env` | NoneBot 框架配置与适配器配置 | INI 风格 |
| `Config.toml` | 机器人自定义配置（指令、消息同步、图片渲染、AI 等） | TOML |

#### `.env` — 框架与适配器

```ini
# 监听端口与主机
PORT=8000
HOST="127.0.0.1"

# 超级用户（管理员 QQ 号）
SUPERUSERS=["1234567890"]

# 命令起始字符与分隔符
COMMAND_SEP=[" "]
COMMAND_START=["."]

# Minecraft 服务器 WebSocket 地址（支持多服）
MINECRAFT_WS_URLS={"server1": ["ws://127.0.0.1:8080/mc"]}
```

#### `Config.toml` — 自定义配置

```toml
# 启用的指令（send 仅在 sync_all_qq_message 为 false 时生效）
command_enabled = ["list", "luck", "server", "help", "bound", "command", "send"]

# 指令响应群 / 消息同步群（格式 "{平台}:{群ID}"）
command_groups = ["qq_client:123456789"]
message_groups = ["qq_client:123456789"]

# 消息同步开关
sync_all_qq_message = true       # 群消息 → 服务器
sync_all_game_message = false    # 服务器消息 → 群
sync_message_between_servers = false  # 服务器之间互转

# WebUi 相关配置
[webui]
enabled = false

# 图片渲染模式
[image]
mode = false
background = 'url("./Resources/Backgrounds/dirt.png")'

# AI 对话（OpenAI 兼容 API）
[ai]
enabled = false
base_url = ""
model_name = ""
api_key = ""
system_prompt = "你是一个可爱的小女孩……"

# 关键词自动回复
[auto_reply]
enabled = false
keywords = { "看群公告里的 IP 地址。" = ["服务器在哪", "服务器地址"] }
```

> 💡 **可选功能依赖**：以上任一功能启用前，建议先同步对应 extra 依赖：
>
> ```bash
> # 图片渲染模式
> uv sync --extra image --inexact
> # 或 WebUI 管理面板
> uv sync --extra webui --inexact
> # 或 AI 对话
> uv sync --extra ai --inexact
> ```

> 📖 完整配置项说明请参阅 `Config.toml` 与 `.env` 文件内注释。

## 🎯 功能一览

### 群服互通

- ✅ 游戏内实时看到 QQ 群消息
- ✅ QQ 群内看到游戏内聊天，支持文字、图片等消息类型
- ✅ 玩家 **加入 / 离开 / 死亡** 全事件播报
- ✅ 服务器 **开启 / 关闭** 自动通知
- ✅ 多服消息互转，构建你的分布式 MC 网络

### 指令系统

| 指令 | 功能 |
|------|------|
| `.list` | 查询所有服务器的在线玩家 |
| `.server` | 查看当前连接的服务器列表 |
| `.luck` | 每日运势占卜（仅供娱乐） |
| `.send` | 向游戏内发送消息（`sync_all_qq_message` 关闭时可用） |
| `.command` | 远程执行 Minecraft 指令（管理员） |
| `.bound` | 绑定 / 解绑 / 查询游戏白名单 |
| `.help` | 查看命令帮助 |
| `.about` | 关于本机器人 |

> 💡 所有指令均基于 [Alconna](https://github.com/ArcletProject/Alconna) 解析，跨平台表现一致。

### 🎨 图片渲染模式

在 `Config.toml` 中设置 `[image] mode = true` 后，机器人的指令输出将以 **图片** 形式发送，而非纯文本。渲染引擎基于 HTML + CSS 模板（Jinja2 + html2pic），效果美观且高度可定制。

**支持图片渲染的指令：**

| 指令 | 渲染内容 |
|------|----------|
| `.list` | 在线玩家列表（含玩家头像） |
| `.server` | 服务器连接状态 |
| `.luck` | 每日运势卡片 |
| `.bound` | 白名单绑定信息 |
| `.help` | 帮助信息 |
| `.about` | 关于页面 |

**自定义背景：**

在 `Config.toml` 的 `[image]` 下设置 `background`，值为 CSS `background-image` 属性值：

```toml
[image]
# 使用本地图片
background = 'url("./Resources/Backgrounds/dirt.png")'

# 使用渐变色
background = 'linear-gradient(150deg, #2e4a30 0%, #1d3524 55%, #12241a 100%)'
```

> ⚠️ 图片模式会略微增加响应时间（需渲染 HTML 并转换为图片）。模板文件位于 `Resources/Images/` 目录，可自行修改 HTML/CSS 定制样式。

### 🖥️ WebUI 管理面板

UniBot 内置基于 **Vue 3 + Vite** 构建的现代化 Web 管理面板，通过 REST API 与后端交互，让管理机器人变得轻松直观。

**主要功能：**

| 功能 | 说明 |
|------|------|
| **📊 仪表盘** | 实时查看机器人运行状态、内存占用、在线服务器数、绑定玩家数 |
| **⚙️ 配置管理** | 可视化编辑 `Config.toml` 和 `.env` 配置，支持 Schema 校验与分组展示 |
| **📋 服务器管理** | 查看所有连接服务器的状态、在线玩家，远程执行指令 |
| **👥 玩家管理** | 管理白名单绑定关系，查看所有已绑定玩家 |
| **🖥️ 服务器详情** | 单服在线玩家、状态详情，远程执行指令 |
| **🛰️ 适配器 / 插件** | 查看已安装的平台适配器与已加载插件列表及其状态 |
| **🙋 用户管理** | 管理 WebUI 登录账户与角色权限 |
| **📄 日志查看** | 实时滚动查看机器人运行日志，支持分级筛选 |
| **🔐 登录认证** | JWT + 密码认证（HttpOnly Cookie），保障管理安全 |

**启用方式：**

1. 在 `Config.toml` 中开启 WebUI：

```toml
[webui]
enabled = true
```

2. 启动机器人。首次启动时，机器人会自动从 GitHub Releases 下载与当前版本匹配的 WebUI 静态资源（需联网，已就绪时自动跳过）。
3. 浏览器访问 `http://<你的IP>:<PORT>/webui`（默认 `http://127.0.0.1:8000/webui`）。
4. **首次访问请先完成初始化**：系统会自动引导你创建管理员账户（用户名 + 密码）。之后即可通过该账户登录管理面板，无需额外配置 Token。

> ⚠️ WebUI 依赖额外包，请确保已执行 `uv sync --extra webui --inexact` 或 `pip install -e ".[webui]"`。

### 智能扩展

- **🤖 AI 对话**：@机器人即可聊天，支持自定义 API 地址、模型和系统提示词，对话上下文自动管理
- **🔑 关键词回复**：自定义关键词自动触发回复，无需编程

---

## 🏗️ 架构设计

```txt
UniBot
├── nonebot2 核心                    ← 异步事件驱动框架
├── nonebot-adapter-minecraft       ← Minecraft WebSocket 通信
├── nonebot-plugin-alconna          ← 跨平台命令解析
├── nonebot-plugin-uninfo           ← 统一会话信息
├── Plugins/
│   ├── Commands/                   ← 独立指令模块
│   │   ├── About.py                ← 关于信息
│   │   ├── Bound.py                ← 白名单绑定
│   │   ├── Command.py              ← 远程指令执行
│   │   ├── Help.py                 ← 帮助系统
│   │   ├── List.py                 ← 在线玩家查询
│   │   ├── Luck.py                 ← 每日运势
│   │   ├── Send.py                 ← 消息发送
│   │   └── Server.py               ← 服务器状态
│   ├── Events.py                   ← MC 事件处理中枢
│   └── Expand/
│       ├── Ai.py                   ← AI 智能对话
│       └── Keywords.py             ← 关键词自动回复
├── Scripts/
│   ├── Managers/
│   │   ├── Data.py                 ← 数据持久化
│   │   ├── Server.py               ← 服务器连接管理
│   │   ├── WebUi.py                ← Web UI 静态资源管理
│   │   ├── Plugin.py               ← 插件管理
│   │   └── Version.py              ← 版本管理
│   ├── Api/                        ← REST API 路由
│   │   ├── Auth.py                 ← 登录认证（JWT / Cookie）
│   │   ├── Config.py               ← 配置管理
│   │   ├── Players.py              ← 玩家管理
│   │   ├── Servers.py              ← 服务器管理
│   │   ├── Plugins.py              ← 插件管理
│   │   ├── Logs.py                 ← 日志查看
│   │   ├── Status.py               ← 状态监控
│   │   ├── Users.py                ← 用户管理
│   │   ├── WebSocket.py            ← WebSocket 推送
│   │   └── Schemas.py              ← 数据模型与校验
│   ├── Config.py                   ← 配置模型定义
│   ├── Network.py                  ← 网络请求工具
│   ├── Utils.py                    ← 工具函数
│   └── Render.py                   ← 图片渲染引擎
└── WebUi/                          ← Vue 3 管理面板前端
    ├── src/
    │   ├── views/                  ← 各功能页面
    │   ├── stores/                 ← Pinia 状态管理
    │   ├── router/                 ← 路由配置
    │   ├── utils/                  ← 工具函数
    │   └── composables/            ← 组合式 API
    └── assets/                     ← 静态资源
```

### 通信流程

```mermaid
flowchart TB
    subgraph MC["🎮 Minecraft 服务器"]
        S1["服务器 A\n(鹊桥插件)"]
        S2["服务器 B\n(鹊桥插件)"]
        S3["服务器 C\n(鹊桥插件)"]
    end

    subgraph BOT["🤖 UniBot 核心"]
        CORE["NoneBot2\n事件驱动框架"]
        AC["Alconna\n跨平台命令解析"]
    end

    subgraph PLAT["💬 聊天平台"]
        QQ["QQ / QQ频道"]
        TG["Telegram"]
        DC["Discord"]
        KK["Kook"]
    end

    S1 <-->|WebSocket| CORE
    S2 <-->|WebSocket| CORE
    S3 <-->|WebSocket| CORE
    CORE --- AC
    AC <-->|OneBot 协议| QQ
    AC <-->|Telegram 适配器| TG
    AC <-->|Discord 适配器| DC
    AC <-->|Kook 适配器| KK

    style S1 fill:#4a9e6b,color:#fff
    style S2 fill:#4a9e6b,color:#fff
    style S3 fill:#4a9e6b,color:#fff
    style CORE fill:#7c3aed,color:#fff
    style AC fill:#2563eb,color:#fff
```

## 🧪 对比同类方案

| 特性 | **Minecraft QQ Bot** | 传统方案 |
|------|---------------------|---------|
| 多平台支持 | ✅ QQ / Telegram / Discord / Kook… | ❌ 通常仅 QQ |
| 多服互联 | ✅ 原生支持，消息互转 | ❌ 需自行改装 |
| WebSocket 通信 | ✅ 实时长连接 | ⚠️ 多为 HTTP 轮询 |
| 模块化插件 | ✅ 指令即插即用 | ❌ 单体耦合 |
| AI 集成 | ✅ 开箱即用 | ❌ 需自行对接 |
| 🖥️ WebUI | ✅ Vue 3 管理面板，开箱即用 | ❌ 无 |
| 🎨 图片渲染 | ✅ HTML/CSS 模板引擎 | ❌ 无 |
| 白名单管理 | ✅ 完善的绑定系统 | ❌ 无或基础 |

---

## 🤝 贡献指南

欢迎任何形式的贡献！无论是 Bug 报告、功能建议还是代码提交：

1. **提交 Issue**：报告 Bug 或提出新功能建议
2. **Pull Request**：Fork 项目，创建特性分支，提交 PR
3. **加入讨论**：加入 [QQ 群 `962802248`](https://qm.qq.com/q/B3kmvJl2xO)

> [!WARNING]
> 本项目采用 **GPL-3.0** 许可证。修改后的代码必须开源并注明出处，**禁止商用**。

---

## 🙏 致谢

- [NoneBot2](https://nonebot.dev/) — 高效优雅的异步机器人框架
- [nonebot-adapter-minecraft](https://github.com/17TheWord/nonebot-adapter-minecraft) — Minecraft 协议适配
- [Alconna](https://github.com/ArcletProject/Alconna) — 强大的命令解析库
- 感谢以下伙伴的贡献与支持：
  - [meng877](https://github.com/meng877) — 意见与代码贡献
  - [Decent_Kook](https://github.com/AISophon) — 宣传

---

## 🔗 友情链接

- [TQM 服务器](https://tqm.mc/)
- [LemonFate 服务器](https://www.lemonfate.cn/)
- [MCJPG](https://www.mcjpg.org)

---

<p align="center">
  Made with ❤️ by LonelySail
</p>
