# MCDR 端插件

本页介绍 **本项目维护的鹊桥 MCDR 端插件**，它运行在 MCDReforged 之上，负责将 Minecraft 服务器接入鹊桥协议。

*需说明的是：该插件仅支持 MCDReforged 服务端。* 若使用 Spigot / Paper / Fabric / Forge / NeoForge 等其它服务端，请参阅 [鹊桥官方实现](/queqiao/官方实现.html)。

## 功能特性

- **双模式 WebSocket**：支持客户端模式（主动连接）与服务端模式（被动监听）。
- **自动重连**：客户端模式可配置重连间隔与最大重试次数。
- **热重载**：`!!queqiao reload` 重载配置并复用旧连接，无需重启服务器。
- **游戏事件转发**：玩家加入 / 退出 / 聊天 / 命令 / 死亡 / 成就。
- **API 指令执行**：广播、私聊、Title、ActionBar、RCON 命令、状态查询。

## 安装

::: tabs
@tab 方式一：直接下载 .mcdr 包

从 [Releases](https://github.com/Minecraft-UniBot/QueQiao.MCDReforged/releases) 下载 `queqiao-vX.X.X.mcdr`，放入 MCDR 的 `plugins/` 目录，重启 MCDR 即可。

@tab 方式二：源码安装

```bash
git clone https://github.com/Minecraft-UniBot/QueQiao.MCDReforged.git
cd MCDReforged
uv sync
```

将整个目录作为 Directory Plugin 放入 MCDR 插件目录，或自行打包：

```bash
uv run python -m mcdreforged pack
```
:::

### 依赖

- **MCDReforged** ≥ 2.15.0
- **Python** ≥ 3.12
- Python 包：`websockets` ≥ 16.0、`PyYAML` ≥ 6.0、`psutil` ≥ 5.9
- MCDR 插件依赖：

::: table title="MCDR 插件依赖" copy="all"
| 插件 | 用途 | 必需 |
|------|------|------|
| [MoreGameEvents](https://mcdreforged.com/zh-CN/plugin/mg_events) | 玩家死亡、成就事件 | ::fluent-color:checkmark-circle-24:: |
| [Minecraft Data API](https://mcdreforged.com/zh-CN/plugin/minecraft_data_api) | 玩家坐标、生命值、经验等级 | ::fluent-color:checkmark-circle-24:: |
| [online_player_api](https://mcdreforged.com/zh-CN/plugin/online_player_api) | 在线玩家列表 | ::fluent-color:warning-24:: 可选（缺失时回退 MCDR 内置接口） |
:::

## 配置

首次加载会在 `config/queqiao/config.json` 生成默认配置：

```json
{
  "server_name": "MCDR",
  "access_token": "",
  "client_origin": "mcdr",
  "minecraft": {
    "host": "",
    "port": 0
  },
  "client": {
    "enable": false,
    "url": "ws://127.0.0.1:8080/minecraft/ws",
    "reconnect_interval": 5,
    "reconnect_max_times": 0
  },
  "server": {
    "enable": false,
    "host": "0.0.0.0",
    "port": 8080
  },
  "log_events": true
}
```

### 字段说明

::: table title="config.json 字段说明" copy="all"
| 字段 | 说明 |
|------|------|
| `server_name` | 本服务器名称，用于 Header `x-self-name` 与事件标识 |
| `access_token` | 鉴权 Token，留空则不发送 `Authorization` 头 |
| `client_origin` | 客户端来源标识，默认 `mcdr` |
| `minecraft.host` / `minecraft.port` | MC 服务器地址，用于 Server List Ping。留空则自动从 MCDR 解析，解析不到时回退 `127.0.0.1:25565` |
| `client.enable` | 启用客户端模式 |
| `client.url` | 鹊桥服务端 WebSocket 地址 |
| `client.reconnect_interval` | 重连间隔（秒） |
| `client.reconnect_max_times` | 最大重连次数，`0` 表示无限重试 |
| `server.enable` | 启用服务端模式 |
| `server.host` / `server.port` | WebSocket 服务端监听地址 |
| `log_events` | 是否在日志中打印事件转发记录 |
:::

### 连接模式

::: tabs
@tab 客户端模式

将 `client.enable` 设为 `true`，并填写鹊桥服务端的 WebSocket 地址（`client.url`）。该模式下插件主动连接服务端，需与对端 `server_name`、`access_token` 保持一致。

*推荐使用客户端模式。* 当服务器在内网、无法直接对外暴露端口时，客户端模式可主动外连，无需在服务器上开放监听端口。

@tab 服务端模式

将 `server.enable` 设为 `true`，插件将启动 WebSocket 服务端监听 `server.host:server.port`，等待鹊桥客户端接入。需在对端 `websocket_client.url_list` 中填写本插件的监听地址。
:::

## 命令

::: table title="命令列表" copy="all"
| 命令 | 权限 | 说明 |
|------|------|------|
| `!!queqiao` | 2 | 显示帮助 |
| `!!queqiao status` | 2 | 查看连接状态（模式、玩家、CPU、内存、MOTD 等） |
| `!!queqiao reload` | 2 | 重载配置并重新连接 |
:::

## 与适配器对接

UniBot 通过 [nonebot-adapter-minecraft](/adapter/使用说明.html) 与鹊桥协议互通。两端需保证：

- **服务器名称**：MCDR 端 `server_name` 与适配器 `MINECRAFT_WS_URLS` 中的键名一致。
- **鉴权 Token**：MCDR 端 `access_token` 与适配器 `MINECRAFT_ACCESS_TOKEN` 一致（不为空时校验）。
- **地址可达**：WebSocket 地址与端口互通，任一端启用客户端模式主动外连即可。

## 基岩版（Bedrock）支持

本插件运行于 MCDReforged 之上，而 MCDR 通过**服务端处理器（Server Handler）**来管理不同类型的 Minecraft 服务端。借助 [Bedrock Liteloader Handler](https://mcdreforged.com/zh-CN/plugin/bedrock_liteloader_handler) 这一处理器，MCDR 可以直接托管 **基岩版专用服务器（BDS）**，从而让本插件也能将基岩版服务器接入鹊桥。

### 原理

`bedrock_liteloader_handler` 是一个 MCDR 服务端处理器，它把 BDS 的标准输出解析为 MCDR 事件（玩家加入 / 退出 / 聊天等）。因此，本插件的事件转发（玩家进出、聊天）在基岩版服务器上**开箱即用**，无需改动插件代码。

### 安装与配置

::: steps

1. **安装处理器**：从 [liteloader_handler Releases](https://github.com/Elec-Glacier/liteloader_handler/releases) 下载最新 `.mcdr` 包，放入 MCDR 的 `plugins/` 目录。

2. **安装本插件**：按上文 [安装](#安装) 安装鹊桥 MCDR 端插件。

3. **配置处理器**：启动 MCDR 后，在 `config/` 下生成处理器的配置文件，选择对应的基岩版处理器（默认即原版处理器），然后重载配置。

4. **配置鹊桥插件**：按上文 [配置](#配置) 填写 `config/queqiao/config.json`，`server_name` / `access_token` 与适配器保持一致。

:::

### 聊天输出

原版 BDS **默认不输出玩家聊天**。要让玩家聊天事件被 MCDR 捕获并转发，需通过**行为包**或**修改服务端**的方式开启聊天输出，否则玩家聊天无法转发到鹊桥。

### 已知限制

基岩版与 Java 版是两套不同的游戏，本插件部分能力在基岩版上存在差异：

::: table title="基岩版能力对照" copy="all"
| 能力 | Java 版 | 基岩版（BDS） |
|------|---------|---------------|
| 玩家加入 / 退出事件 | ✅ | ✅（经处理器解析） |
| 玩家聊天事件 | ✅ | ✅（需行为包 / 修改服务端开启输出） |
| 玩家死亡 / 成就事件 | ✅（MoreGameEvents） | ::fluent-color:warning-24:: 依赖 Java 事件，通常不可用 |
| 玩家坐标 / 生命值等数据 | ✅（minecraft_data_api） | ❌ 不可用，字段为 `None` |
| Server List Ping（MOTD / 在线数） | ✅（Java SLP 协议） | ❌ 基岩版使用 RakNet 协议，ping 失败，`get_status` 回退 |
| 广播 / 私聊（`tellraw`） | ✅ | ::fluent-color:warning-24:: 命令语法不同，需适配 |
| Title / ActionBar | ✅ | ::fluent-color:warning-24:: 命令语法不同（如 `titleraw`） |
| RCON 命令 | ✅ | ::fluent-color:warning-24:: 命令集不同 |
:::

*由于基岩版与 Java 版命令体系差异较大，若需在基岩版上使用广播、私聊、Title 等 API，建议在 [QueQiao.MCDReforged](https://github.com/Minecraft-UniBot/QueQiao.MCDReforged) 仓库中提出需求或提交适配。*

### 注意事项

- **LeviLamina**：LeviLamina 1.0.0 之后 MCDR 无法直接获取修改过的服务端输出，需借助支持 pty 的应用作为桥梁（详见 [liteloader_handler#13](https://github.com/Elec-Glacier/liteloader_handler/issues/13)）。
- **Unicode 修复**：受 [BDS-3791](https://bugs.mojang.com/browse/BDS-3791) 影响，中文等非 ASCII 字符可能显示异常，可安装 [UnicodeFixer](https://www.minebbs.com/resources/unicodefixer.6991/) 修复。
- **插件兼容性**：基岩版与 Java 版判若两个游戏，使用其它 MCDR 插件前请确认其是否兼容基岩版。

## 协议

鹊桥 V2 协议基于 WebSocket，通过 `Authorization` 头鉴权，双向实时通信。MCDR 端将游戏事件转发给鹊桥，鹊桥再向 MCDR 发送 API 指令（广播、私聊、Title、RCON 等）。