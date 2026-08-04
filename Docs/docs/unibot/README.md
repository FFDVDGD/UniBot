# UniBot

**UniBot** 是 Minecraft UniBot 的核心机器人，基于 [NoneBot2](https://nonebot.dev/) 框架构建，负责与聊天平台和多台 Minecraft 服务器通信。

## 快速导航

- [架构设计](/unibot/架构设计.html) — 深入了解项目结构
- [REST API](/unibot/接口文档.html) — WebUI 后端 API 参考

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | NoneBot2（FastAPI 驱动） |
| 命令解析 | Alconna |
| 会话信息 | uninfo |
| 数据校验 | Pydantic |
| HTTP 客户端 | httpx |
| 图片渲染 | Jinja2 + html2pic |
| 认证 | JWT + bcrypt |
| 前端 | Vue 3 + Vite + Pinia |

## 核心能力

- **跨平台消息**：一套指令逻辑，全平台通用。
- **多服互联**：同时连接多台服务器，消息互转。
- **模块化插件**：指令按插件拆分，可独立启用/禁用。
- **WebUI 管理面板**：可视化配置、监控、日志。
- **图片渲染**：指令输出渲染为精美图片。
- **AI 对话**：接入任意 OpenAI 兼容 API。
- **白名单管理**：平台账号与游戏 ID 绑定。

## 目录结构

```
UniBot/
├── Bot.py                 # 机器人入口
├── Watchdog.py            # 守护进程（自动重启）
├── Config.toml            # 机器人配置
├── Config/
│   └── Messages.toml      # 消息文本
├── Data/                  # 数据持久化（JSON）
├── Logs/                  # 运行日志
├── Plugins/               # 插件（指令模块）
│   ├── Commands/          # 内置指令
│   ├── Expand/            # 扩展功能（AI、关键词）
│   └── Events.py          # 事件处理中枢
├── Scripts/               # 核心脚本
│   ├── Managers/          # 管理器（数据、服务器、插件等）
│   ├── Api/               # REST API 路由
│   ├── Config.py          # 配置模型
│   ├── Network.py         # 网络工具
│   ├── Render.py          # 图片渲染引擎
│   └── ...
├── Resources/             # 资源（图片模板、背景）
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