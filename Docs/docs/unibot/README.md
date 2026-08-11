# UniBot

**UniBot** 是 Minecraft UniBot 的核心机器人，基于 [NoneBot2](https://nonebot.dev/) 框架构建，负责与聊天平台和多台 Minecraft 服务器通信。UniBot 完全兼容 NoneBot2 生态，可无缝接入 [NB 插件商店](https://registry.nonebot.dev/)，直接使用社区现成插件。

## 快速导航

- [配置说明](/unibot/配置说明.html) — `.env` 与 `Config.toml` 等全部配置项
- [扩展系统](/unibot/扩展系统.html) — 扩展类型、清单、状态与渲染体系
- [架构设计](/unibot/架构设计.html) — 深入了解项目结构
- [REST API](/unibot/接口文档.html) — WebUI 后端 API 参考
- [开发扩展](/unibot/开发插件.html) — 编写自己的 UniBot 扩展
- [上传市场](/unibot/上传市场.html) — 把你的扩展发布到扩展市场

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | NoneBot2（FastAPI 驱动） |
| 命令解析 | Alconna |
| 会话信息 | uninfo |
| 数据校验 | Pydantic |
| HTTP 客户端 | httpx |
| 图片渲染 | Jinja2（模板） + html2pic / Playwright（引擎） |
| 认证 | JWT + bcrypt |
| 前端 | Vue 3 + Vite + Pinia |

## 核心能力

- **跨平台消息**：一套指令逻辑，全平台通用。
- **多服互联**：同时连接多台服务器，消息互转。
- **扩展系统**：指令、服务、渲染引擎、模板与资源五类扩展，按需启停、失败隔离。
- **WebUI 管理面板**：可视化配置、监控、日志、扩展管理。
- **图片渲染**：指令输出渲染为精美图片，模板与引擎可自由组合。
- **白名单管理**：平台账号与游戏 ID 绑定。
- **NoneBot2 生态**：无缝接入 NB 插件商店，社区插件即插即用。

## 目录结构

```
UniBot/
├── Bot.py                 # 机器人入口
├── Watchdog.py            # 守护进程（自动重启）
├── Config.toml            # 机器人配置
├── Config/
│   ├── Extensions.toml    # 扩展启停
│   ├── Extensions/        # 扩展配置（每扩展一个文件）
│   └── Messages.toml      # 消息文本
├── Data/                  # 数据持久化（JSON）
│   ├── Extension/         # 扩展管理状态
│   └── Exs/               # 扩展业务数据
├── Logs/                  # 运行日志
├── Extensions/            # 扩展包（本地 / 市场）
├── Plugins/               # NoneBot 插件（指令模块）
│   ├── Commands/          # 内置指令
│   └── Events.py          # 事件处理中枢
├── Scripts/               # 核心脚本
│   ├── Extensions/        # 扩展系统框架
│   ├── Managers/          # 管理器（数据、服务器、插件等）
│   ├── Api/               # REST API 路由
│   ├── Config.py          # 配置模型
│   ├── Network.py         # 网络工具
│   └── ...
└── WebUi/                 # Vue 3 管理面板前端
```

## 启动方式

UniBot 有两个入口：

- **`Bot.py`**：直接运行机器人进程。
- **`Watchdog.py`**：守护进程，监控机器人异常退出并自动重启，同时处理 WebUI 的重启请求与依赖同步。

推荐使用 `Watchdog.py` 启动：

```bash
uv run Watchdog.py
```